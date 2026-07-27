import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import (
    Alert,
    Campaign,
    Incident,
    Malware,
    ThreatActor,
    ThreatIOC,
    campaign_actor_association,
    campaign_ioc_association,
    campaign_malware_association,
    ioc_alert_association,
    ioc_incident_association,
)

logger = logging.getLogger(__name__)


class ThreatCorrelationEngine:
    """Correlate ThreatIOCs with related IOCs, alerts, incidents, malware, and actors."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def correlate_ioc(self, ioc_id: int) -> dict[str, Any]:
        """Build a correlation report for a single ThreatIOC."""
        result = await self.db.execute(
            select(ThreatIOC).where(ThreatIOC.id == ioc_id)
        )
        ioc = result.scalar_one_or_none()
        if not ioc:
            raise ValueError(f"IOC {ioc_id} not found")

        related_iocs = await self._related_iocs(ioc_id)
        related_alerts = await self._related_alerts(ioc_id)
        related_incidents = await self._related_incidents(ioc_id)
        related_campaigns = await self._related_campaigns(ioc_id)
        related_malware = await self._related_malware(ioc_id)
        related_actors = await self._related_actors(ioc_id)

        return {
            "ioc_id": ioc_id,
            "value": ioc.value,
            "type": ioc.type,
            "related_iocs": related_iocs,
            "related_alerts": related_alerts,
            "related_incidents": related_incidents,
            "related_campaigns": related_campaigns,
            "related_malware": related_malware,
            "related_actors": related_actors,
        }

    async def _related_campaigns(self, ioc_id: int) -> list[dict[str, Any]]:
        stmt = (
            select(Campaign)
            .join(campaign_ioc_association)
            .where(campaign_ioc_association.c.ioc_id == ioc_id)
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        return [{"id": c.id, "name": c.campaign_name, "status": c.status} for c in rows]

    async def _related_alerts(self, ioc_id: int) -> list[dict[str, Any]]:
        stmt = (
            select(Alert)
            .join(ioc_alert_association)
            .where(ioc_alert_association.c.ioc_id == ioc_id)
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        return [{"id": a.id, "title": a.title, "severity": a.severity, "status": a.status} for a in rows]

    async def _related_incidents(self, ioc_id: int) -> list[dict[str, Any]]:
        stmt = (
            select(Incident)
            .join(ioc_incident_association)
            .where(ioc_incident_association.c.ioc_id == ioc_id)
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        return [{"id": i.id, "name": i.name, "severity": i.severity, "status": i.status} for i in rows]

    async def _related_iocs(self, ioc_id: int) -> list[dict[str, Any]]:
        """Find IOCs that co-occur in the same campaigns or alerts/incidents."""
        campaign_ids_result = await self.db.execute(
            select(campaign_ioc_association.c.campaign_id).where(campaign_ioc_association.c.ioc_id == ioc_id)
        )
        campaign_ids = [r for r in campaign_ids_result.scalars().all()]

        alert_ids_result = await self.db.execute(
            select(ioc_alert_association.c.alert_id).where(ioc_alert_association.c.ioc_id == ioc_id)
        )
        alert_ids = [r for r in alert_ids_result.scalars().all()]

        incident_ids_result = await self.db.execute(
            select(ioc_incident_association.c.incident_id).where(ioc_incident_association.c.ioc_id == ioc_id)
        )
        incident_ids = [r for r in incident_ids_result.scalars().all()]

        related: dict[int, dict[str, Any]] = {}

        if campaign_ids:
            stmt = (
                select(ThreatIOC)
                .join(campaign_ioc_association)
                .where(campaign_ioc_association.c.campaign_id.in_(campaign_ids))
                .where(ThreatIOC.id != ioc_id)
            )
            for other in (await self.db.execute(stmt)).scalars().all():
                related.setdefault(other.id, {"value": other.value, "type": other.type, "reasons": set()})
                related[other.id]["reasons"].add("shared_campaign")

        if alert_ids:
            stmt = (
                select(ThreatIOC)
                .join(ioc_alert_association)
                .where(ioc_alert_association.c.alert_id.in_(alert_ids))
                .where(ThreatIOC.id != ioc_id)
            )
            for other in (await self.db.execute(stmt)).scalars().all():
                related.setdefault(other.id, {"value": other.value, "type": other.type, "reasons": set()})
                related[other.id]["reasons"].add("shared_alert")

        if incident_ids:
            stmt = (
                select(ThreatIOC)
                .join(ioc_incident_association)
                .where(ioc_incident_association.c.incident_id.in_(incident_ids))
                .where(ThreatIOC.id != ioc_id)
            )
            for other in (await self.db.execute(stmt)).scalars().all():
                related.setdefault(other.id, {"value": other.value, "type": other.type, "reasons": set()})
                related[other.id]["reasons"].add("shared_incident")

        return [
            {"id": i, "value": d["value"], "type": d["type"], "reasons": list(d["reasons"])}
            for i, d in related.items()
        ]

    async def _related_malware(self, ioc_id: int) -> list[dict[str, Any]]:
        campaign_ids_result = await self.db.execute(
            select(campaign_ioc_association.c.campaign_id).where(campaign_ioc_association.c.ioc_id == ioc_id)
        )
        campaign_ids = [r for r in campaign_ids_result.scalars().all()]
        if not campaign_ids:
            return []
        stmt = (
            select(Malware)
            .join(campaign_malware_association)
            .where(campaign_malware_association.c.campaign_id.in_(campaign_ids))
            .distinct()
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        return [{"id": m.id, "family": m.family} for m in rows]

    async def _related_actors(self, ioc_id: int) -> list[dict[str, Any]]:
        campaign_ids_result = await self.db.execute(
            select(campaign_ioc_association.c.campaign_id).where(campaign_ioc_association.c.ioc_id == ioc_id)
        )
        campaign_ids = [r for r in campaign_ids_result.scalars().all()]
        if not campaign_ids:
            return []
        stmt = (
            select(ThreatActor)
            .join(campaign_actor_association)
            .where(campaign_actor_association.c.campaign_id.in_(campaign_ids))
            .distinct()
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        return [{"id": a.id, "name": a.name} for a in rows]

    async def build_threat_graph(self, limit: int = 200) -> dict[str, Any]:
        """Return a graph payload for the interactive threat graph."""
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        node_ids: set[str] = set()

        def add_node(node_id: str, label: str, group: str, **kwargs: Any) -> None:
            if node_id not in node_ids:
                node_ids.add(node_id)
                nodes.append({"id": node_id, "label": label, "group": group, **kwargs})

        def add_edge(source: str, target: str, label: str) -> None:
            edges.append({"source": source, "target": target, "label": label})

        iocs = (
            await self.db.execute(
                select(ThreatIOC)
                .options(
                    selectinload(ThreatIOC.campaigns),
                    selectinload(ThreatIOC.linked_alerts),
                    selectinload(ThreatIOC.linked_incidents),
                )
                .limit(limit)
            )
        ).scalars().all()
        for ioc in iocs:
            ioc_node = f"ioc:{ioc.value}"
            add_node(ioc_node, ioc.value, "ioc", score=ioc.threat_score, malicious=ioc.malicious)
            for campaign in ioc.campaigns:
                camp_node = f"campaign:{campaign.id}"
                add_node(camp_node, campaign.campaign_name, "campaign", status=campaign.status)
                add_edge(ioc_node, camp_node, "observed_in")
            for alert in ioc.linked_alerts:
                alert_node = f"alert:{alert.id}"
                add_node(alert_node, f"Alert {alert.id}", "alert", severity=alert.severity)
                add_edge(ioc_node, alert_node, "observed_in")
            for incident in ioc.linked_incidents:
                inc_node = f"incident:{incident.id}"
                add_node(inc_node, incident.name, "incident", severity=incident.severity)
                add_edge(ioc_node, inc_node, "linked_to")

        campaigns = (
            await self.db.execute(
                select(Campaign)
                .options(selectinload(Campaign.malware), selectinload(Campaign.actors))
                .limit(limit)
            )
        ).scalars().all()
        for campaign in campaigns:
            camp_node = f"campaign:{campaign.id}"
            add_node(camp_node, campaign.campaign_name, "campaign", status=campaign.status)
            for malware in campaign.malware:
                mal_node = f"malware:{malware.id}"
                add_node(mal_node, malware.family, "malware", family=malware.family)
                add_edge(camp_node, mal_node, "uses")
            for actor in campaign.actors:
                actor_node = f"actor:{actor.id}"
                add_node(actor_node, actor.name, "actor", motivation=actor.motivation)
                add_edge(actor_node, camp_node, "attributed_to")

        return {"nodes": nodes, "edges": edges}

    async def enrich_alert_iocs(self, alert: Alert) -> None:
        """Link any known ThreatIOCs found in an alert's fields."""
        from app.services.threat_intelligence.enrichment.io_extractor import IOCExtractor
        extractor = IOCExtractor()
        text = " ".join(filter(None, [
            alert.title,
            alert.description,
            alert.raw_log,
            alert.source_ip or "",
            alert.destination_ip or "",
        ]))
        iocs = extractor.extract(text)
        for ioc_type, values in iocs.items():
            for value in values:
                existing = await self.db.execute(
                    select(ThreatIOC).where(ThreatIOC.value == value).where(ThreatIOC.type == ioc_type)
                )
                row = existing.scalar_one_or_none()
                if row:
                    alert.threat_iocs.append(row)
