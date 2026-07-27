import logging
from typing import Any

from app.services.threat_intelligence.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class MITREAttackConnector(BaseConnector):
    """MITRE ATT&CK technique enrichment connector.

    This connector does not require an API key. It interprets technique IDs
    (e.g. T1110) and returns normalized tactic/technique metadata.
    """

    @property
    def name(self) -> str:
        return "mitre_attack"

    async def enrich(self, ioc: str, ioc_type: str) -> dict[str, Any]:
        if ioc_type != "mitre_technique":
            return self._normalize_common()
        from app.services.ai_engine.knowledge_base import KnowledgeBase
        info = KnowledgeBase.lookup_mitre(ioc)
        if info.get("tactic"):
            return {
                "provider": self.name,
                "provider_score": 100,
                "provider_reference": f"https://attack.mitre.org/techniques/{ioc}/",
                "raw_data": info,
                "tactic": info.get("tactic"),
                "technique": info.get("technique"),
                "mitre_technique_id": ioc,
            }
        return self._normalize_common()

    async def health(self) -> dict[str, Any]:
        return {"name": self.name, "healthy": True, "api_key_required": False}
