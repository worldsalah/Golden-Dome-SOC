"""System information collection service — powers the first-launch deployment wizard.

Collects OS, host, hardware, Docker, container, network, and platform-service
information so the onboarding wizard can display a live, professional-feeling
environment scan (similar to installers for VMware/GitLab/Wazuh).
"""

from __future__ import annotations

import asyncio
import json
import logging
import platform
import shutil
import socket
import subprocess

import httpx

logger = logging.getLogger(__name__)

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None


def _run(cmd: list[str], timeout: float = 3.0) -> str | None:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        return None
    return None


def get_os_info() -> dict:
    """Distribution, version, architecture."""
    distro = None
    version = None
    try:
        with open("/etc/os-release") as f:
            data = dict(
                line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#")
            )
        distro = data.get("PRETTY_NAME", "").strip('"') or None
        version = data.get("VERSION_ID", "").strip('"') or None
    except Exception:
        pass

    return {
        "distribution": distro or platform.system(),
        "version": version or platform.release(),
        "architecture": f"{platform.machine()} ({'64-bit' if platform.machine().endswith('64') else '32-bit'})",
        "kernel": platform.release(),
        "platform": platform.platform(),
    }


def _get_local_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(1.0)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return None


async def _get_public_ip() -> str | None:
    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            resp = await client.get("https://api.ipify.org?format=json")
            if resp.status_code == 200:
                return resp.json().get("ip")
    except Exception:
        return None
    return None


async def get_host_info() -> dict:
    """Hostname, local IP, public IP, domain."""
    hostname = socket.gethostname()
    fqdn = socket.getfqdn()
    domain = fqdn.split(".", 1)[1] if "." in fqdn and fqdn != hostname else None

    return {
        "hostname": hostname,
        "fqdn": fqdn,
        "domain": domain,
        "local_ip": _get_local_ip(),
        "public_ip": await _get_public_ip(),
    }


def _fmt_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def get_hardware_info() -> dict:
    """CPU, RAM, disk."""
    cpu_model = None
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.lower().startswith("model name"):
                    cpu_model = line.split(":", 1)[1].strip()
                    break
    except Exception:
        pass

    if psutil:
        physical_cores = psutil.cpu_count(logical=False) or 0
        logical_cores = psutil.cpu_count(logical=True) or 0
        vm = psutil.virtual_memory()
        ram_total, ram_available = vm.total, vm.available
        du = shutil.disk_usage("/")
        disk_total, disk_free = du.total, du.free
    else:
        physical_cores = 0
        logical_cores = 0
        try:
            with open("/proc/cpuinfo") as f:
                logical_cores = sum(1 for line in f if line.startswith("processor"))
            physical_cores = logical_cores
        except Exception:
            pass
        ram_total = ram_available = 0
        try:
            with open("/proc/meminfo") as f:
                mem = dict(line.split(":", 1) for line in f if ":" in line)
            ram_total = int(mem.get("MemTotal", "0 kB").strip().split()[0]) * 1024
            ram_available = int(mem.get("MemAvailable", "0 kB").strip().split()[0]) * 1024
        except Exception:
            pass
        du = shutil.disk_usage("/")
        disk_total, disk_free = du.total, du.free

    return {
        "cpu_model": cpu_model or platform.processor() or "Unknown CPU",
        "physical_cores": physical_cores,
        "logical_cores": logical_cores,
        "ram_total": _fmt_bytes(ram_total),
        "ram_available": _fmt_bytes(ram_available),
        "ram_total_bytes": ram_total,
        "disk_total": _fmt_bytes(disk_total),
        "disk_free": _fmt_bytes(disk_free),
        "disk_total_bytes": disk_total,
    }


def get_docker_info() -> dict:
    """Docker + Compose availability and version."""
    docker_path = shutil.which("docker")
    installed = docker_path is not None
    running = False
    version = None
    compose_version = None

    if installed:
        version = _run(["docker", "--version"])
        ps_check = _run(["docker", "info", "--format", "{{.ServerVersion}}"])
        running = ps_check is not None
        compose_version = _run(["docker", "compose", "version", "--short"]) or _run(
            ["docker-compose", "--version"]
        )

    return {
        "installed": installed,
        "running": running,
        "version": version,
        "compose_version": compose_version,
    }


def get_containers() -> list[dict]:
    """Currently running containers detected via the Docker CLI."""
    output = _run(
        [
            "docker",
            "ps",
            "--format",
            '{"name":"{{.Names}}","status":"{{.Status}}","image":"{{.Image}}","ports":"{{.Ports}}","created":"{{.RunningFor}}"}',
        ],
        timeout=5.0,
    )
    containers: list[dict] = []
    if not output:
        return containers
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            containers.append(
                {
                    "name": data.get("name"),
                    "status": data.get("status"),
                    "image": data.get("image"),
                    "ports": data.get("ports"),
                    "uptime": data.get("created"),
                }
            )
        except Exception:
            continue
    return containers


def get_network_info() -> dict:
    """Interfaces, IPv4 addresses, default gateway."""
    interfaces: list[dict] = []
    if psutil:
        for name, addrs in psutil.net_if_addrs().items():
            ipv4 = [a.address for a in addrs if a.family == socket.AF_INET]
            if ipv4:
                interfaces.append({"name": name, "addresses": ipv4})

    gateway = None
    try:
        with open("/proc/net/route") as f:
            for line in f.readlines()[1:]:
                fields = line.strip().split()
                if len(fields) >= 3 and fields[1] == "00000000":
                    gw_hex = fields[2]
                    gateway = socket.inet_ntoa(bytes.fromhex(gw_hex)[::-1])
                    break
    except Exception:
        pass

    return {"interfaces": interfaces, "gateway": gateway}


async def _check_tcp(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        conn = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(conn, timeout=timeout)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return True
    except Exception:
        return False


async def _check_http(url: str, timeout: float = 1.5) -> bool:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            return resp.status_code < 500
    except Exception:
        return False


async def get_platform_services() -> list[dict]:
    """Health status of core Golden Dome platform services."""
    checks = [
        ("Backend API", _check_http("http://localhost:8000/health")),
        ("Frontend", _check_tcp("frontend", 8080)),
        ("PostgreSQL", _check_tcp("db", 5432)),
        ("Wazuh Manager", _check_tcp("wazuh-manager", 55000)),
        ("Wazuh Indexer", _check_tcp("wazuh-indexer", 9200)),
        ("Wazuh Dashboard", _check_tcp("wazuh-dashboard", 5601)),
        ("Ollama", _check_http("http://ollama:11434/api/version")),
    ]
    names = [c[0] for c in checks]
    results = await asyncio.gather(*(c[1] for c in checks), return_exceptions=True)

    services = []
    for name, result in zip(names, results):
        if isinstance(result, Exception):
            state = "unknown"
        else:
            state = "online" if result else "offline"
        services.append({"name": name, "status": state})
    return services


async def get_full_system_info() -> dict:
    """Aggregate everything the onboarding wizard needs in one call."""
    host_info = await get_host_info()
    services = await get_platform_services()
    return {
        "operating_system": get_os_info(),
        "host": host_info,
        "hardware": get_hardware_info(),
        "docker": get_docker_info(),
        "containers": get_containers(),
        "network": get_network_info(),
        "services": services,
    }
