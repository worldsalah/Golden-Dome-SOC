import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser, CurrentUser
from app.config.security import hash_password
from app.database.database import get_db
from app.database.models import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(current_user: CurrentUser):
    return current_user


@router.get("", response_model=dict)
async def list_users(
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    limit: int = 20,
):
    total_result = await db.execute(select(User))
    total = len(total_result.scalars().all())

    result = await db.execute(
        select(User)
        .offset((page - 1) * limit)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return {
        "data": [UserRead.model_validate(u) for u in users],
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(User).where((User.username == payload.username) | (User.email == payload.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("User created by %s: %s", current_user.username, user.username)
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    logger.info("User updated by %s: %s", current_user.username, user.username)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    await db.delete(user)
    await db.commit()
    logger.info("User deleted by %s: %s", current_user.username, user.username)
    return None
