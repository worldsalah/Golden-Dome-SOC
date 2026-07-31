from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.database.models import User
from app.security.jwt import get_current_user, get_current_user_optional
from app.security.permissions import Role, _resolve_role, require_min_role, require_role

DBDependency = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]
SuperAdminUser = Annotated[User, Depends(require_role(Role.SUPER_ADMIN))]

async def first_boot_allowed(
    db: DBDependency,
    user: CurrentUserOptional,
) -> User | None:
    from sqlalchemy import select, func
    from app.database.models import User as UserModel
    count = (await db.execute(select(func.count(UserModel.id)))).scalar() or 0
    if count == 0:
        return None
    if not user or _resolve_role(user.role) != Role.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Platform already configured. Authenticate as super admin.")
    return user

FirstBootOrSuperAdmin = Annotated[User | None, Depends(first_boot_allowed)]
SecurityManagerUser = Annotated[User, Depends(require_min_role(Role.SECURITY_MANAGER))]
AnalystUser = Annotated[User, Depends(require_min_role(Role.ANALYST))]
ITAdminUser = Annotated[User, Depends(require_min_role(Role.IT_ADMINISTRATOR))]
ViewerUser = Annotated[User, Depends(require_min_role(Role.EXECUTIVE))]
AdminUser = Annotated[User, Depends(require_role(Role.SUPER_ADMIN))]
