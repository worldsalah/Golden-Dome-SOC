from enum import Enum
from functools import wraps

from fastapi import Depends, HTTPException, status

from app.database.models import User
from app.security.jwt import get_current_user


class Role(str, Enum):
    ADMIN = "admin"
    SOC_ANALYST = "soc_analyst"
    VIEWER = "viewer"


ROLE_HIERARCHY = {
    Role.ADMIN: 3,
    Role.SOC_ANALYST: 2,
    Role.VIEWER: 1,
}


def require_role(*allowed_roles: Role):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        try:
            user_role = Role(current_user.role)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


def require_min_role(min_role: Role):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        try:
            user_role = Role(current_user.role)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        if ROLE_HIERARCHY.get(user_role, 0) < ROLE_HIERARCHY.get(min_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker
