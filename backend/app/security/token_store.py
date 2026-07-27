import time

from redis.asyncio import Redis

from app.config.settings import get_settings

_fallback_revocations: dict[str, float] = {}


async def is_token_revoked(token_id: str | None) -> bool:
    if not token_id:
        return True
    settings = get_settings()
    client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=0.2, socket_timeout=0.2)
    try:
        return bool(await client.exists(f"auth:revoked:{token_id}"))
    except Exception:
        return _fallback_revocations.get(token_id, 0) > time.time()
    finally:
        await client.aclose()


async def revoke_token(token_id: str | None, expires_in_seconds: int) -> None:
    if not token_id:
        return
    settings = get_settings()
    client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=0.2, socket_timeout=0.2)
    try:
        await client.set(f"auth:revoked:{token_id}", "1", ex=max(expires_in_seconds, 1))
    except Exception:
        _fallback_revocations[token_id] = time.time() + max(expires_in_seconds, 1)
    finally:
        await client.aclose()


async def consume_login_attempt(identifier: str) -> bool:
    settings = get_settings()
    client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=0.2, socket_timeout=0.2)
    key = f"auth:login:{identifier.lower()}"
    try:
        attempts = await client.incr(key)
        if attempts == 1:
            await client.expire(key, settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)
        return attempts > settings.LOGIN_RATE_LIMIT_ATTEMPTS
    except Exception:
        return False
    finally:
        await client.aclose()


async def clear_login_attempts(identifier: str) -> None:
    settings = get_settings()
    client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=0.2, socket_timeout=0.2)
    try:
        await client.delete(f"auth:login:{identifier.lower()}")
    except Exception:
        pass
    finally:
        await client.aclose()
