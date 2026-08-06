"""Docker container metrics for the monitoring dashboard.

Primary source is cAdvisor (scraped by Prometheus) so the backend container
does not need privileged access to the Docker socket. Falls back to the local
`docker` CLI when it is available (e.g. dev environments with the socket
mounted), which also provides restart counts that cAdvisor does not track.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess

from app.services.monitoring import prometheus_service

logger = logging.getLogger(__name__)


def _run(cmd: list[str], timeout: float = 5.0) -> str | None:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as exc:
        logger.debug("docker command failed (%s): %s", cmd, exc)
        return None
    return None


def _fmt_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


async def list_containers_from_cadvisor() -> list[dict] | None:
    """Query cAdvisor metrics (via Prometheus) for Golden Dome containers."""
    if not await prometheus_service.is_available():
        return None

    cpu_query = 'sum by (name) (rate(container_cpu_usage_seconds_total{name=~"goldendome.*"}[1m])) * 100'
    mem_query = 'container_memory_usage_bytes{name=~"goldendome.*"}'
    uptime_query = 'time() - container_start_time_seconds{name=~"goldendome.*"}'

    async def _named_series(promql: str) -> dict[str, float]:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(
                    f"{prometheus_service.PROMETHEUS_URL}/api/v1/query", params={"query": promql}
                )
                resp.raise_for_status()
                result = resp.json().get("data", {}).get("result", [])
                out: dict[str, float] = {}
                for item in result:
                    name = item.get("metric", {}).get("name")
                    value = item.get("value")
                    if name and value and len(value) > 1:
                        out[name] = float(value[1])
                return out
        except Exception as exc:
            logger.debug("cAdvisor series query failed (%s): %s", promql, exc)
            return {}

    cpu, mem, uptime = None, None, None
    cpu = await _named_series(cpu_query)
    mem = await _named_series(mem_query)
    uptime = await _named_series(uptime_query)

    names = set(cpu) | set(mem) | set(uptime)
    if not names:
        return None

    containers = []
    for name in sorted(names):
        containers.append(
            {
                "id": name,
                "name": name,
                "status": "running",
                "raw_status": "Up",
                "image": None,
                "uptime": f"{int(uptime.get(name, 0) // 3600)}h" if name in uptime else None,
                "cpu": f"{cpu.get(name, 0):.1f}%" if name in cpu else "0%",
                "memory": _fmt_bytes(mem.get(name, 0)) if name in mem else "0B",
            }
        )
    return containers


def list_containers_from_docker_cli() -> list[dict]:
    """Return running Golden Dome containers with live CPU/memory stats."""
    ps_output = _run(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            "name=goldendome",
            "--format",
            '{"id":"{{.ID}}","name":"{{.Names}}","status":"{{.Status}}","state":"{{.State}}","image":"{{.Image}}","created":"{{.RunningFor}}"}',
        ]
    )
    containers: list[dict] = []
    if not ps_output:
        return containers

    by_id: dict[str, dict] = {}
    for line in ps_output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            by_id[data["id"]] = {
                "id": data["id"],
                "name": data.get("name"),
                "status": "running" if "Up" in data.get("status", "") else "stopped",
                "raw_status": data.get("status"),
                "image": data.get("image"),
                "uptime": data.get("created"),
                "cpu": "0%",
                "memory": "0B",
            }
        except Exception:
            continue

    if not by_id:
        return []

    stats_output = _run(
        [
            "docker",
            "stats",
            "--no-stream",
            "--format",
            '{"id":"{{.ID}}","cpu":"{{.CPUPerc}}","mem":"{{.MemUsage}}"}',
        ]
        + list(by_id.keys()),
        timeout=8.0,
    )
    if stats_output:
        for line in stats_output.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                cid = data["id"]
                if cid in by_id:
                    by_id[cid]["cpu"] = data.get("cpu", "0%")
                    by_id[cid]["memory"] = data.get("mem", "0B").split(" / ")[0]
            except Exception:
                continue

    return list(by_id.values())


async def list_containers() -> list[dict]:
    """Return Golden Dome container status/CPU/memory, preferring cAdvisor."""
    containers = await list_containers_from_cadvisor()
    if containers:
        return containers
    if shutil.which("docker"):
        return list_containers_from_docker_cli()
    return []
