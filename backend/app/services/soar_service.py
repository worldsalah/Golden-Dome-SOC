"""Backward-compatible re-export of the SOAR service package."""
from app.services.soar.soar_service import BUILTIN_PLAYBOOKS, SoarService

__all__ = ["BUILTIN_PLAYBOOKS", "SoarService"]
