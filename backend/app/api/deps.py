from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.database.models import User
from app.security.jwt import get_current_user
from app.security.permissions import Role, require_min_role, require_role

DBDependency = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_role(Role.ADMIN))]
AnalystUser = Annotated[User, Depends(require_min_role(Role.SOC_ANALYST))]
ViewerUser = Annotated[User, Depends(require_min_role(Role.VIEWER))]
