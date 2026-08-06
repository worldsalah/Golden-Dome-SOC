"""Service health checks for the monitoring dashboard."""

from __future__ import annotations

import asyncio

from app.services import system_info
from app.services.monitoring import prometheus_service


async def get_service_health() -> dict[str, str]:
    """Return a name->status map for every core Golden Dome service."""
    checks = [
        ("backend", system_info._check_http("http://localhost:8000/health")),
        ("frontend", system_info._check_tcp("frontend", 8080)),
        ("postgresql", system_info._check_tcp("db", 5432)),
        ("wazuh_manager", system_info._check_tcp("wazuh-manager", 55000)),
        ("wazuh_indexer", system_info._check_tcp("wazuh-indexer", 9200)),
        ("wazuh_dashboard", system_info._check_tcp("wazuh-dashboard", 5601)),
        ("ollama", system_info._check_http("http://ollama:11434/api/version")),
        ("prometheus", prometheus_service.is_available()),
        ("grafana", system_info._check_http("http://grafana:3000/api/health")),
    ]
    names = [c[0] for c in checks]
    results = await asyncio.gather(*(c[1] for c in checks), return_exceptions=True)

    status: dict[str, str] = {}
    for name, result in zip(names, results):
        if isinstance(result, Exception):
            status[name] = "unknown"
        else:
            status[name] = "online" if result else "offline"
    return status
