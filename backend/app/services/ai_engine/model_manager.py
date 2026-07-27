import json
import logging
from typing import Any

import httpx
from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class ModelManager:
    """Thin client for the local Ollama API with a deterministic fallback."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.base_url = self.settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = self.settings.OLLAMA_MODEL
        self.timeout = self.settings.OLLAMA_TIMEOUT
        self.fallback_enabled = self.settings.AI_FALLBACK_ENABLED

    async def health(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                return {"status": "ok", "data": response.json()}
        except Exception as exc:
            logger.warning("Ollama health check failed: %s", exc)
            return {"status": "unreachable", "error": str(exc)}

    async def generate(self, prompt: str, system: str | None = None, format: str | None = "json") -> dict[str, Any]:
        """Generate a response from the local LLM, falling back to rule-based output if unavailable."""
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 2048},
        }
        if system:
            payload["system"] = system
        if format:
            payload["format"] = format

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                raw = data.get("response", "")
                return {"success": True, "raw": raw, "source": "ollama", "model": self.model}
        except Exception as exc:
            logger.warning("Ollama generation failed: %s", exc)
            if self.fallback_enabled:
                return {"success": True, "raw": self._fallback_json(prompt), "source": "fallback", "model": "sentinel-rule"}
            return {"success": False, "raw": "", "source": "error", "error": str(exc)}

    def _fallback_json(self, prompt: str) -> str:
        """Deterministic fallback that mimics the LLM JSON structure."""
        lower = prompt.lower()
        technique_id = "T1190"
        tactic = "Initial Access"
        if "brute force" in lower or "failed" in lower or "logon" in lower:
            technique_id = "T1110"
            tactic = "Credential Access"
        elif "port scan" in lower or "scan" in lower:
            technique_id = "T1046"
            tactic = "Discovery"
        elif "deny" in lower or "firewall" in lower:
            technique_id = "T1190"
            tactic = "Initial Access"

        severity = "high"
        confidence = 78
        priority = "P2"
        if "critical" in lower or "13" in lower:
            severity = "critical"
            confidence = 92
            priority = "P1"
        elif "low" in lower:
            severity = "low"
            confidence = 55
            priority = "P4"

        risk_score = 70
        try:
            # Try to extract a Wazuh severity from the prompt.
            import re
            match = re.search(r"severity[:\s]+(\d+)", lower)
            if match:
                level = int(match.group(1))
                risk_score = min(int((level / 15) * 100), 100)
        except Exception:
            pass

        result = {
            "executive_summary": (
                "Sentinel AI has identified suspicious activity matching the alert signature. "
                "The event should be triaged according to the recommended priority and investigation steps."
            ),
            "technical_explanation": {
                "what": "A security alert was triggered by telemetry collected from the environment.",
                "how": "The detection rule correlated raw logs to produce this event.",
                "logs": "Refer to the attached raw log and source/destination metadata.",
                "indicators": [],
            },
            "mitre_mapping": {"tactic": tactic, "technique": f"{technique_id} Technique", "technique_id": technique_id},
            "risk_assessment": {
                "severity": severity,
                "confidence": confidence,
                "business_impact": "Potential unauthorized access or data exposure if confirmed.",
                "priority": priority,
            },
            "risk_score": risk_score,
            "investigation_steps": [
                "Verify the source IP reputation and geolocation.",
                "Check for successful follow-on events from the same actor.",
                "Review asset logs for lateral movement or privilege escalation.",
            ],
            "recommended_response": {
                "immediate": ["Contain or block the suspicious source if IOCs are confirmed."],
                "short_term": ["Reset affected credentials", "Enable or review MFA policies"],
                "long_term": ["Tune detection rules", "Conduct purple-team validation"],
            },
            "analyst_notes": "This analysis was generated in fallback mode because the local LLM was unreachable.",
        }
        return json.dumps(result, indent=2)
