import logging
import time
import json
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.security import hash_password, verify_password
from app.database.database import get_db
from app.database.models import User, AuditLog, UserSession
from app.config.settings import get_settings
from app.schemas.auth import RefreshTokenRequest, Token, TokenRevokeRequest, UserRegister
from app.schemas.user import UserRead
from app.security.jwt import create_access_token, create_refresh_token, decode_token, get_current_user
from app.security.token_store import clear_login_attempts, consume_login_attempt, is_token_revoked, revoke_token
from app.utils.datetime_helper import utc_now

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


class MfaEnrollResponse(BaseModel):
    secret: str
    qr_uri: str
    backup_codes: list[str]


class MfaVerifyRequest(BaseModel):
    code: str


class MfaVerifyResponse(BaseModel):
    verified: bool
    message: str


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    if await consume_login_attempt(form_data.username):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts. Try again later.")

    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        # Record failed login attempt
        if user:
            user.failed_login_count = (user.failed_login_count or 0) + 1
            await db.commit()
        audit = AuditLog(
            tenant_id=user.organization_id if user else None,
            user_id=user.id if user else None,
            username=form_data.username,
            action="login_failed",
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            status="failed",
        )
        db.add(audit)
        await db.commit()
        logger.warning("Failed login attempt for user: %s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    await clear_login_attempts(form_data.username)

    # Update login tracking
    user.last_login = utc_now()
    user.last_login_ip = request.client.host if request else None
    user.failed_login_count = 0

    # Create access token with tenant_id
    extra_claims = {}
    if user.organization_id:
        extra_claims["tenant_id"] = user.organization_id
    access_token = create_access_token(subject=user.id, role=user.role, extra_claims=extra_claims)
    refresh_token = create_refresh_token(subject=user.id)

    # Record session
    session = UserSession(
        user_id=user.id,
        tenant_id=user.organization_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(session)

    # Record audit log
    audit = AuditLog(
        tenant_id=user.organization_id,
        user_id=user.id,
        username=user.username,
        action="login_success",
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        status="success",
    )
    db.add(audit)
    await db.commit()

    logger.info("User %s logged in successfully", user.username)

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    claims = decode_token(payload.refresh_token)
    subject = claims.get("sub") if claims else None
    if not claims or claims.get("type") != "refresh" or not subject or await is_token_revoked(claims.get("jti")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    await revoke_token(claims.get("jti"), int(claims.get("exp", time.time())) - int(time.time()))
    return Token(
        access_token=create_access_token(subject=user.id, role=user.role),
        refresh_token=create_refresh_token(subject=user.id),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: TokenRevokeRequest):
    claims = decode_token(payload.refresh_token)
    if claims and claims.get("type") == "refresh":
        await revoke_token(claims.get("jti"), int(claims.get("exp", time.time())) - int(time.time()))


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    user_count = (await db.execute(select(User.id))).scalars().first()
    if user_count is not None or not settings.ALLOW_BOOTSTRAP_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is disabled. Contact an administrator.",
        )
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
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("Registered new user: %s with role %s", user.username, user.role)
    return user


@router.post("/mfa/enroll", response_model=MfaEnrollResponse)
async def enroll_mfa(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Generate a TOTP secret and backup codes for MFA enrollment."""
    import pyotp

    secret = pyotp.random_base32()
    backup_codes = [secrets.token_hex(8) for _ in range(10)]

    current_user.mfa_secret = secret
    current_user.mfa_backup_codes = json.dumps(backup_codes)
    await db.commit()

    otp = pyotp.TOTP(secret)
    qr_uri = otp.provisioning_uri(name=current_user.email, issuer_name="Golden Dome SOC")

    audit = AuditLog(
        tenant_id=current_user.organization_id,
        user_id=current_user.id,
        username=current_user.username,
        action="mfa_enrollment_started",
        resource_type="user",
        resource_id=str(current_user.id),
        status="success",
    )
    db.add(audit)
    await db.commit()

    return MfaEnrollResponse(secret=secret, qr_uri=qr_uri, backup_codes=backup_codes)


@router.post("/mfa/verify", response_model=MfaVerifyResponse)
async def verify_mfa(
    payload: MfaVerifyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Verify a TOTP code and enable MFA for the user."""
    import pyotp

    if not current_user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA not enrolled. Call /auth/mfa/enroll first.")

    otp = pyotp.TOTP(current_user.mfa_secret)
    if not otp.verify(payload.code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code.")

    current_user.mfa_enabled = True
    audit = AuditLog(
        tenant_id=current_user.organization_id,
        user_id=current_user.id,
        username=current_user.username,
        action="mfa_enabled",
        resource_type="user",
        resource_id=str(current_user.id),
        status="success",
    )
    db.add(audit)
    await db.commit()

    return MfaVerifyResponse(verified=True, message="MFA enabled successfully.")


@router.post("/mfa/disable", response_model=MfaVerifyResponse)
async def disable_mfa(
    payload: MfaVerifyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Disable MFA for the current user (requires a valid TOTP code)."""
    import pyotp

    if not current_user.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled.")

    otp = pyotp.TOTP(current_user.mfa_secret or "")
    if not otp.verify(payload.code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code.")

    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.mfa_backup_codes = None
    audit = AuditLog(
        tenant_id=current_user.organization_id,
        user_id=current_user.id,
        username=current_user.username,
        action="mfa_disabled",
        resource_type="user",
        resource_id=str(current_user.id),
        status="success",
    )
    db.add(audit)
    await db.commit()

    return MfaVerifyResponse(verified=True, message="MFA disabled successfully.")
