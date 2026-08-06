"""Thin client for querying the Prometheus HTTP API used by the monitoring dashboard."""

from __future__ import annotations

import logging
import os
import time

import httpx

logger = logging.getLogger(__name__)

PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://prometheus:9090")

RANGE_PRESETS = {
    "1h": (3600, 15),
    "24h": (86400, 300),
    "7d": (604800, 3600),
}


async def is_available() -> bool:
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get(f"{PROMETHEUS_URL}/-/healthy")
            return resp.status_code == 200
    except Exception:
        return False


async def query(promql: str) -> float | None:
    """Instant query — returns the first scalar result, or None."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": promql})
            resp.raise_for_status()
            data = resp.json()
            result = data.get("data", {}).get("result", [])
            if not result:
                return None
            value = result[0].get("value")
            if not value or len(value) < 2:
                return None
            return float(value[1])
    except Exception as exc:
        logger.debug("Prometheus query failed (%s): %s", promql, exc)
        return None


async def query_range(promql: str, range_key: str) -> list[dict]:
    """Range query — returns a list of {timestamp, value} points."""
    duration, step = RANGE_PRESETS.get(range_key, RANGE_PRESETS["1h"])
    end = time.time()
    start = end - duration
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{PROMETHEUS_URL}/api/v1/query_range",
                params={"query": promql, "start": start, "end": end, "step": step},
            )
            resp.raise_for_status()
            data = resp.json()
            result = data.get("data", {}).get("result", [])
            if not result:
                return []
            values = result[0].get("values", [])
            return [{"timestamp": int(v[0]), "value": float(v[1])} for v in values]
    except Exception as exc:
        logger.debug("Prometheus range query failed (%s): %s", promql, exc)
        return []
