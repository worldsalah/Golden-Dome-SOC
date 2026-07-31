from enum import Enum

from fastapi import Depends, HTTPException, status

from app.database.models import User
from app.security.jwt import get_current_user


class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    SECURITY_MANAGER = "security_manager"
    ANALYST = "analyst"
    IT_ADMINISTRATOR = "it_administrator"
    EXECUTIVE = "executive"
    # Legacy aliases
    ADMIN = "super_admin"
    SOC_ANALYST = "analyst"
    VIEWER = "executive"


ROLE_HIERARCHY = {
    Role.SUPER_ADMIN: 100,
    Role.SECURITY_MANAGER: 80,
    Role.ANALYST: 60,
    Role.IT_ADMINISTRATOR: 60,
    Role.EXECUTIVE: 40,
    # Legacy
    Role.ADMIN: 100,
    Role.SOC_ANALYST: 60,
    Role.VIEWER: 40,
}


def _resolve_role(role_str: str) -> Role:
    """Resolve a role string, handling legacy values."""
    role_map = {
        "admin": Role.SUPER_ADMIN,
        "soc_analyst": Role.ANALYST,
        "viewer": Role.EXECUTIVE,
        "super_admin": Role.SUPER_ADMIN,
        "security_manager": Role.SECURITY_MANAGER,
        "analyst": Role.ANALYST,
        "it_administrator": Role.IT_ADMINISTRATOR,
        "executive": Role.EXECUTIVE,
    }
    return role_map.get(role_str, Role.ANALYST)


def require_role(*allowed_roles: Role):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = _resolve_role(current_user.role)
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


def require_min_role(min_role: Role):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = _resolve_role(current_user.role)
        if ROLE_HIERARCHY.get(user_role, 0) < ROLE_HIERARCHY.get(min_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker
