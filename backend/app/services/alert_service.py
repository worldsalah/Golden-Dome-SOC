import logging
from datetime import datetime
from typing import Sequence

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Alert, AlertStatus, Asset
from app.schemas.alert import AlertCreate, AlertListParams, AlertStatusUpdate

logger = logging.getLogger(__name__)


async def _run_alert_triggered_playbooks(db: AsyncSession, alert: Alert) -> None:
    """Fire alert-triggered SOAR playbooks in the background."""
    from app.services.soar_service import SoarService

    try:
        service = SoarService(db)
        await service.trigger_alert_playbooks(alert)
    except Exception:
        logger.exception("Failed to run alert-triggered playbooks for alert %s", alert.id)


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_alerts(self, params: AlertListParams) -> tuple[Sequence[Alert], int]:
        query = select(Alert)

        if params.severity is not None:
            query = query.where(Alert.severity == params.severity)
        if params.status:
            query = query.where(Alert.status == params.status)
        if params.search:
            search = f"%{params.search}%"
            query = query.where(
                Alert.title.ilike(search)
                | Alert.description.ilike(search)
                | Alert.source_ip.ilike(search)
                | Alert.destination_ip.ilike(search)
            )
        start = _parse_iso_datetime(params.start_date)
        end = _parse_iso_datetime(params.end_date)
        if start:
            query = query.where(Alert.created_at >= start)
        if end:
            query = query.where(Alert.created_at <= end)
        if params.assigned_to_me:
            query = query.where(Alert.assigned_user_id.isnot(None))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(desc(Alert.created_at))
        query = query.offset((params.page - 1) * params.limit).limit(params.limit)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_alert(self, alert_id: int) -> Alert | None:
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def create_alert(self, alert_in: AlertCreate) -> Alert:
        alert = Alert(**alert_in.model_dump())
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        logger.info("Created alert %s (Wazuh ID: %s)", alert.id, alert.wazuh_alert_id)
        await _run_alert_triggered_playbooks(self.db, alert)
        return alert

    async def update_status(self, alert_id: int, update: AlertStatusUpdate) -> Alert | None:
        alert = await self.get_alert(alert_id)
        if not alert:
            return None

        alert.status = update.status
        if update.assigned_user_id is not None:
            alert.assigned_user_id = update.assigned_user_id

        await self.db.commit()
        await self.db.refresh(alert)
        logger.info("Updated alert %s status to %s", alert.id, alert.status)
        return alert

    async def get_alert_stats(self) -> dict:
        total_result = await self.db.execute(select(func.count(Alert.id)))
        total = total_result.scalar_one()

        status_counts = {}
        for status in AlertStatus:
            count_result = await self.db.execute(
                select(func.count(Alert.id)).where(Alert.status == status.value)
            )
            status_counts[status.value] = count_result.scalar_one()

        severity_result = await self.db.execute(
            select(Alert.severity, func.count(Alert.id))
            .group_by(Alert.severity)
            .order_by(desc(Alert.severity))
        )
        severity_counts = {sev: count for sev, count in severity_result.all()}

        return {
            "total": total,
            "by_status": status_counts,
            "by_severity": severity_counts,
        }

    async def sync_alerts_from_wazuh(self, normalized_alerts: list[dict]) -> tuple[int, int]:
        created = 0
        skipped = 0
        new_alerts: list[Alert] = []
        for data in normalized_alerts:
            existing = await self.db.execute(
                select(Alert).where(Alert.wazuh_alert_id == data["wazuh_alert_id"])
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            asset = None
            if data.get("agent_id") or data.get("source_ip"):
                asset = await self.db.execute(
                    select(Asset).where(
                        (Asset.wazuh_agent_id == str(data.get("agent_id")))
                        | (Asset.ip_address == data.get("source_ip"))
                    )
                )
                asset = asset.scalar_one_or_none()

            alert_data = {
                **data,
                "asset_id": asset.id if asset else None,
            }
            alert = Alert(**alert_data)
            self.db.add(alert)
            new_alerts.append(alert)
            created += 1

        await self.db.commit()
        for alert in new_alerts:
            await self.db.refresh(alert)
            await _run_alert_triggered_playbooks(self.db, alert)
        logger.info("Synced %d new alerts, skipped %d duplicates", created, skipped)
        return created, skipped
