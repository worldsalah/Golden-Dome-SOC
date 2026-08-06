"""Real-time infrastructure monitoring API — server, container, and service health metrics."""

from __future__ import annotations

import asyncio
import time
from datetime import timedelta

from fastapi import APIRouter, Query

from app.api.deps import AnalystUser
from app.services import system_info
from app.services.monitoring import docker_service, health_service, prometheus_service

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


def _fmt_mbps(bytes_per_sec: float) -> str:
    return f"{(bytes_per_sec * 8 / 1_000_000):.1f} Mbps"


def _fmt_uptime(seconds: float) -> str:
    delta = timedelta(seconds=max(0, seconds))
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes = rem // 60
    if days:
        return f"{days} days, {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


async def _server_metrics_from_prometheus() -> dict | None:
    if not await prometheus_service.is_available():
        return None

    cpu_idle = await prometheus_service.query('avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100')
    mem_pct = await prometheus_service.query(
        "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"
    )
    disk_pct = await prometheus_service.query(
        '(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100'
    )
    net_in = await prometheus_service.query('sum(rate(node_network_receive_bytes_total{device!="lo"}[1m]))')
    net_out = await prometheus_service.query('sum(rate(node_network_transmit_bytes_total{device!="lo"}[1m]))')
    uptime_secs = await prometheus_service.query("time() - node_boot_time_seconds")

    if cpu_idle is None and mem_pct is None:
        return None

    return {
        "cpu_usage": round(100 - cpu_idle, 1) if cpu_idle is not None else None,
        "memory_usage": round(mem_pct, 1) if mem_pct is not None else None,
        "disk_usage": round(disk_pct, 1) if disk_pct is not None else None,
        "network_in": _fmt_mbps(net_in) if net_in is not None else None,
        "network_out": _fmt_mbps(net_out) if net_out is not None else None,
        "uptime": _fmt_uptime(uptime_secs) if uptime_secs is not None else None,
        "source": "prometheus",
    }


async def _server_metrics_fallback() -> dict:
    hw = system_info.get_hardware_info()
    cpu_usage = None
    if psutil:
        cpu_usage = psutil.cpu_percent(interval=0.3)

    ram_pct = None
    disk_pct = None
    if psutil:
        vm = psutil.virtual_memory()
        ram_pct = vm.percent
        du = psutil.disk_usage("/")
        disk_pct = du.percent

    net_in = net_out = None
    uptime = None
    if psutil:
        io1 = psutil.net_io_counters()
        await asyncio.sleep(0.5)
        io2 = psutil.net_io_counters()
        net_in = (io2.bytes_recv - io1.bytes_recv) / 0.5
        net_out = (io2.bytes_sent - io1.bytes_sent) / 0.5
        uptime = time.time() - psutil.boot_time()

    return {
        "cpu_usage": round(cpu_usage, 1) if cpu_usage is not None else None,
        "memory_usage": round(ram_pct, 1) if ram_pct is not None else None,
        "disk_usage": round(disk_pct, 1) if disk_pct is not None else None,
        "network_in": _fmt_mbps(net_in) if net_in is not None else None,
        "network_out": _fmt_mbps(net_out) if net_out is not None else None,
        "uptime": _fmt_uptime(uptime) if uptime is not None else None,
        "source": "local",
    }


@router.get("/server")
async def server_metrics(current_user: AnalystUser):
    """Live server resource usage: CPU, memory, disk, network, uptime."""
    metrics = await _server_metrics_from_prometheus()
    if metrics is None:
        metrics = await _server_metrics_fallback()

    hw = system_info.get_hardware_info()
    metrics["cores"] = hw["physical_cores"]
    metrics["ram_total"] = hw["ram_total"]
    metrics["disk_total"] = hw["disk_total"]
    return metrics


@router.get("/containers")
async def container_metrics(current_user: AnalystUser):
    """Docker container status, CPU, and memory usage for the Golden Dome stack."""
    return await docker_service.list_containers()


@router.get("/services")
async def service_health(current_user: AnalystUser):
    """Online/offline status for every core Golden Dome service."""
    return await health_service.get_service_health()


@router.get("/history")
async def metrics_history(
    current_user: AnalystUser,
    metric: str = Query("cpu", pattern="^(cpu|memory|network)$"),
    range: str = Query("1h", pattern="^(1h|24h|7d)$"),
):
    """Historical CPU/memory/network series from Prometheus, for charting."""
    queries = {
        "cpu": 'avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * -100 + 100',
        "memory": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
        "network": 'sum(rate(node_network_receive_bytes_total{device!="lo"}[5m])) * 8 / 1000000',
    }
    if not await prometheus_service.is_available():
        return {"metric": metric, "range": range, "points": [], "available": False}

    points = await prometheus_service.query_range(queries[metric], range)
    return {"metric": metric, "range": range, "points": points, "available": True}
