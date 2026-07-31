"""Background worker that synchronizes Wazuh alerts, agents, and correlated incidents into the platform database."""

import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import AsyncSessionLocal
from app.database.models import (
    Alert,
    AlertStatus,
    Asset,
    AssetType,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    IncidentTimeline,
    incident_alert_association,
)
from app.services.wazuh_service import WazuhService

logger = logging.getLogger(__name__)

SYNC_INTERVAL_SECONDS = 60
SYNC_BATCH_SIZE = 200
INCIDENT_CORRELATION_HOURS = 24
INCIDENT_MIN_CLUSTER_SIZE = 2


def _utcnow() -> datetime:
    """Return naive UTC datetime for DB compatibility."""
    return datetime.utcnow()


async def _sync_assets(db: AsyncSession, wazuh: WazuhService) -> int:
    """Upsert Wazuh agents as assets in the platform DB."""
    try:
        agents_resp = await wazuh.get_agents()
    except Exception:
        logger.exception("Failed to fetch agents from Wazuh")
        return 0

    agents = agents_resp.get("data", {}).get("affected_items", [])
    synced = 0
    for agent in agents:
        agent_id = agent.get("id")
        if not agent_id:
            continue

        existing = await db.execute(
            select(Asset).where(Asset.wazuh_agent_id == str(agent_id))
        )
        asset = existing.scalar_one_or_none()

        os_info = agent.get("os", {})
        os_name = os_info.get("name", "") or ""
        if "windows" in os_name.lower() or "windows" in (os_info.get("platform", "") or "").lower():
            asset_type = AssetType.WINDOWS_SERVER.value
        elif "linux" in os_name.lower() or "ubuntu" in os_name.lower() or "amazon" in os_name.lower():
            asset_type = AssetType.LINUX_SERVER.value
        elif "forti" in (agent.get("name", "") or "").lower():
            asset_type = AssetType.FIREWALL.value
        else:
            asset_type = AssetType.UNKNOWN.value

        ip = agent.get("ip", "")
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()

        if asset:
            asset.last_seen = _utcnow()
            asset.ip_address = ip or asset.ip_address
            asset.operating_system = os_name or asset.operating_system
            if asset_type != AssetType.UNKNOWN.value:
                asset.type = asset_type
        else:
            asset = Asset(
                hostname=agent.get("name", f"agent-{agent_id}"),
                ip_address=ip or None,
                type=asset_type,
                operating_system=os_name or None,
                wazuh_agent_id=str(agent_id),
                last_seen=_utcnow(),
            )
            db.add(asset)
        synced += 1

    await db.commit()
    logger.info("Asset sync: %d agents processed", synced)
    return synced


async def _sync_alerts(db: AsyncSession, wazuh: WazuhService) -> tuple[int, int]:
    """Pull recent alerts from OpenSearch and persist them in the platform DB."""
    try:
        raw_alerts = await wazuh.get_alerts(size=SYNC_BATCH_SIZE)
    except Exception:
        logger.exception("Failed to fetch alerts from OpenSearch")
        return 0, 0

    normalized = [await wazuh.normalize_alert(a) for a in raw_alerts]
    created = 0
    skipped = 0

    for data in normalized:
        wazuh_id = data.get("wazuh_alert_id", "")
        if not wazuh_id:
            continue

        existing = await db.execute(
            select(Alert).where(Alert.wazuh_alert_id == wazuh_id)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        agent_id = data.get("agent_id")
        asset = None
        if agent_id:
            asset_result = await db.execute(
                select(Asset).where(Asset.wazuh_agent_id == str(agent_id))
            )
            asset = asset_result.scalar_one_or_none()

        alert = Alert(
            wazuh_alert_id=wazuh_id,
            title=data.get("title", "Wazuh Alert"),
            description=data.get("description", ""),
            severity=data.get("severity", 1),
            source_ip=data.get("source_ip"),
            destination_ip=data.get("destination_ip"),
            rule_id=data.get("rule_id"),
            mitre_technique=data.get("mitre_technique"),
            status=AlertStatus.NEW.value,
            raw_log=data.get("raw_log"),
            asset_id=asset.id if asset else None,
        )
        db.add(alert)
        created += 1

    await db.commit()
    logger.info("Alert sync: %d created, %d skipped", created, skipped)
    return created, skipped


async def _sync_incidents(db: AsyncSession, wazuh: WazuhService) -> int:
    """Correlate alerts into incidents and persist them in the platform DB."""
    try:
        clusters = await wazuh.correlate_incidents(
            hours=INCIDENT_CORRELATION_HOURS,
            min_cluster_size=INCIDENT_MIN_CLUSTER_SIZE,
        )
    except Exception:
        logger.exception("Failed to correlate incidents")
        return 0

    created = 0
    for cluster in clusters:
        cluster_key = cluster.get("cluster_key", "")
        if not cluster_key:
            continue

        existing_name = f"Correlated: {cluster.get('rule_description', cluster_key)}"
        existing = await db.execute(
            select(Incident).where(Incident.name == existing_name).limit(1)
        )
        if existing.scalar_one_or_none():
            continue

        max_severity = cluster.get("max_severity", 3)
        if max_severity >= 10:
            severity = IncidentSeverity.CRITICAL.value
        elif max_severity >= 7:
            severity = IncidentSeverity.HIGH.value
        elif max_severity >= 4:
            severity = IncidentSeverity.MEDIUM.value
        else:
            severity = IncidentSeverity.LOW.value

        incident = Incident(
            name=existing_name,
            severity=severity,
            status=IncidentStatus.OPEN.value,
            description=json.dumps({
                "cluster_key": cluster_key,
                "alert_count": cluster.get("alert_count", 0),
                "rule_ids": cluster.get("rule_ids", []),
                "mitre_techniques": cluster.get("mitre_techniques", []),
                "source_ips": cluster.get("source_ips", []),
                "agent_names": cluster.get("agent_names", []),
                "first_seen": cluster.get("first_seen"),
                "last_seen": cluster.get("last_seen"),
            }, default=str),
        )
        db.add(incident)
        await db.flush()

        timeline = IncidentTimeline(
            incident_id=incident.id,
            action="incident_created",
            note=f"Auto-correlated from {cluster.get('alert_count', 0)} alerts (cluster: {cluster_key})",
        )
        db.add(timeline)

        rule_ids = cluster.get("rule_ids", [])
        if rule_ids:
            alerts_result = await db.execute(
                select(Alert.id).where(Alert.rule_id.in_([str(r) for r in rule_ids]))
            )
            for (alert_id,) in alerts_result.all():
                await db.execute(
                    insert(incident_alert_association).values(
                        incident_id=incident.id, alert_id=alert_id
                    )
                )

        created += 1

    await db.commit()
    if created:
        logger.info("Incident sync: %d incidents created", created)
    return created


async def run_sync_cycle() -> dict:
    """Run one full sync cycle: assets → alerts → incidents."""
    results = {"assets": 0, "alerts_created": 0, "alerts_skipped": 0, "incidents": 0}
    try:
        async with AsyncSessionLocal() as db:
            wazuh = WazuhService()
            results["assets"] = await _sync_assets(db, wazuh)
            created, skipped = await _sync_alerts(db, wazuh)
            results["alerts_created"] = created
            results["alerts_skipped"] = skipped
            results["incidents"] = await _sync_incidents(db, wazuh)
    except Exception:
        logger.exception("Sync cycle failed")
    return results


async def sync_worker_loop():
    """Background loop that runs sync cycles periodically."""
    logger.info("Starting Wazuh sync worker (interval=%ds)", SYNC_INTERVAL_SECONDS)
    while True:
        try:
            await run_sync_cycle()
        except asyncio.CancelledError:
            logger.info("Sync worker cancelled")
            break
        except Exception:
            logger.exception("Unexpected error in sync worker loop")
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)
