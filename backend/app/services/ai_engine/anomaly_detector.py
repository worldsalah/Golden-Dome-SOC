import json
import logging
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Alert, AnomalyRecord


from app.utils.datetime_helper import utc_now
logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Train and run an Isolation Forest model for security behavior anomalies."""

    def __init__(self, contamination: float = 0.05):
        self.model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)

    def fit(self, features: np.ndarray) -> "AnomalyDetector":
        """Fit the model on normal/ mixed feature vectors."""
        if len(features) == 0:
            logger.warning("No features provided for anomaly detection training")
            return self
        self.model.fit(features)
        return self

    def predict(self, features: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Return anomaly labels (-1 for anomaly, 1 normal) and anomaly scores (lower = more anomalous)."""
        if len(features) == 0:
            return np.array([]), np.array([])
        labels = self.model.predict(features)
        scores = self.model.score_samples(features)
        return labels, scores

    async def analyze_auth_patterns(
        self,
        db: AsyncSession,
        hours: int = 168,
    ) -> list[dict[str, Any]]:
        """Simple anomaly detection based on failed login counts per source IP per hour."""
        cutoff = utc_now() - timedelta(hours=hours)
        result = await db.execute(
            select(Alert)
            .where(Alert.created_at >= cutoff)
            .where(Alert.title.ilike("%logon%"))
            .order_by(Alert.created_at)
        )
        alerts = result.scalars().all()

        # Group by source_ip -> count of alerts and unique hours
        buckets: dict[str, dict[str, Any]] = {}
        for alert in alerts:
            ip = alert.source_ip or "unknown"
            hour = alert.created_at.replace(minute=0, second=0, microsecond=0).isoformat()
            entry = buckets.setdefault(ip, {"count": 0, "hours": set(), "severity_sum": 0})
            entry["count"] += 1
            entry["hours"].add(hour)
            entry["severity_sum"] += alert.severity

        if len(buckets) < 5:
            logger.info("Not enough distinct source IPs for reliable anomaly detection")
            return []

        rows = list(buckets.items())
        features = np.array([
            [
                data["count"],
                len(data["hours"]),
                data["severity_sum"] / max(data["count"], 1),
            ]
            for _, data in rows
        ], dtype=np.float64)

        self.fit(features)
        labels, scores = self.predict(features)

        anomalies = []
        for idx, (ip, data) in enumerate(rows):
            if labels[idx] == -1:
                record = AnomalyRecord(
                    feature_type="auth",
                    record_id=ip,
                    anomaly_score=int(max(0, min((-scores[idx]) * 100, 100))),
                    features=json.dumps({
                        "total_alerts": data["count"],
                        "unique_hours": len(data["hours"]),
                        "avg_severity": data["severity_sum"] / max(data["count"], 1),
                    }),
                )
                db.add(record)
                anomalies.append({
                    "source_ip": ip,
                    "score": record.anomaly_score,
                    "details": record.features,
                })
        await db.commit()
        return anomalies

    async def analyze_traffic_patterns(
        self,
        db: AsyncSession,
        hours: int = 168,
    ) -> list[dict[str, Any]]:
        """Anomaly detection for port-scan / network alerts per source IP."""
        cutoff = utc_now() - timedelta(hours=hours)
        result = await db.execute(
            select(Alert)
            .where(Alert.created_at >= cutoff)
            .where(Alert.title.ilike("%scan%"))
            .order_by(Alert.created_at)
        )
        alerts = result.scalars().all()

        buckets: dict[str, dict[str, Any]] = {}
        for alert in alerts:
            ip = alert.source_ip or "unknown"
            entry = buckets.setdefault(ip, {"count": 0, "unique_targets": set(), "severity_sum": 0})
            entry["count"] += 1
            entry["unique_targets"].add(alert.destination_ip)
            entry["severity_sum"] += alert.severity

        if len(buckets) < 5:
            return []

        rows = list(buckets.items())
        features = np.array([
            [
                data["count"],
                len(data["unique_targets"]),
                data["severity_sum"] / max(data["count"], 1),
            ]
            for _, data in rows
        ], dtype=np.float64)

        self.fit(features)
        labels, scores = self.predict(features)

        anomalies = []
        for idx, (ip, data) in enumerate(rows):
            if labels[idx] == -1:
                record = AnomalyRecord(
                    feature_type="traffic",
                    record_id=ip,
                    anomaly_score=int(max(0, min((-scores[idx]) * 100, 100))),
                    features=json.dumps({
                        "total_alerts": data["count"],
                        "unique_targets": len(data["unique_targets"]),
                        "avg_severity": data["severity_sum"] / max(data["count"], 1),
                    }),
                )
                db.add(record)
                anomalies.append({
                    "source_ip": ip,
                    "score": record.anomaly_score,
                    "details": record.features,
                })
        await db.commit()
        return anomalies
