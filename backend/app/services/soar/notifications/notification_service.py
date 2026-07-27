import json
import logging
import smtplib
from email.mime.text import MIMEText
from typing import Any

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Deliver notifications via email, webhook, or simulated team channels."""

    async def send_email(self, recipient: str, subject: str, body: str, sender: str | None = None) -> dict[str, Any]:
        settings = get_settings()
        smtp_host = getattr(settings, "SMTP_HOST", None) or ""
        smtp_port = getattr(settings, "SMTP_PORT", 587)
        smtp_user = getattr(settings, "SMTP_USER", "")
        smtp_pass = getattr(settings, "SMTP_PASSWORD", "")
        smtp_tls = getattr(settings, "SMTP_TLS", True)

        if not smtp_host:
            logger.info("SMTP not configured; email simulated to %s: %s", recipient, subject)
            return {"status": "simulated", "channel": "email", "recipient": recipient, "subject": subject, "body": body}

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender or smtp_user or "soc@goldendome.local"
        msg["To"] = recipient

        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                if smtp_tls:
                    server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return {"status": "sent", "channel": "email", "recipient": recipient, "subject": subject}
        except Exception as exc:
            logger.exception("Failed to send email to %s", recipient)
            return {"status": "error", "channel": "email", "recipient": recipient, "error": str(exc)}

    async def send_slack(self, webhook_url: str, message: str) -> dict[str, Any]:
        if not webhook_url:
            logger.info("Slack webhook not configured; message simulated: %s", message[:80])
            return {"status": "simulated", "channel": "slack", "message": message}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(webhook_url, json={"text": message})
                response.raise_for_status()
            return {"status": "sent", "channel": "slack", "http_status": response.status_code}
        except Exception as exc:
            logger.exception("Failed to send Slack message")
            return {"status": "error", "channel": "slack", "error": str(exc)}

    async def send_teams(self, webhook_url: str, message: str) -> dict[str, Any]:
        if not webhook_url:
            logger.info("Teams webhook not configured; message simulated: %s", message[:80])
            return {"status": "simulated", "channel": "teams", "message": message}
        try:
            import httpx
            card = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": "SOAR Notification",
                "text": message,
            }
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(webhook_url, json=card)
                response.raise_for_status()
            return {"status": "sent", "channel": "teams", "http_status": response.status_code}
        except Exception as exc:
            logger.exception("Failed to send Teams message")
            return {"status": "error", "channel": "teams", "error": str(exc)}

    async def send_discord(self, webhook_url: str, message: str) -> dict[str, Any]:
        if not webhook_url:
            logger.info("Discord webhook not configured; message simulated: %s", message[:80])
            return {"status": "simulated", "channel": "discord", "message": message}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(webhook_url, data={"content": message})
                response.raise_for_status()
            return {"status": "sent", "channel": "discord", "http_status": response.status_code}
        except Exception as exc:
            logger.exception("Failed to send Discord message")
            return {"status": "error", "channel": "discord", "error": str(exc)}

    async def notify(self, channel: str, config: dict[str, Any], message: str, subject: str | None = None) -> dict[str, Any]:
        if channel == "email":
            return await self.send_email(config.get("recipient", "soc@goldendome.local"), subject or "SOAR Notification", message, config.get("sender"))
        if channel == "slack":
            return await self.send_slack(config.get("webhook_url", ""), message)
        if channel == "teams":
            return await self.send_teams(config.get("webhook_url", ""), message)
        if channel == "discord":
            return await self.send_discord(config.get("webhook_url", ""), message)
        logger.info("Notification channel %s simulated: %s", channel, message[:80])
        return {"status": "simulated", "channel": channel, "message": message}
