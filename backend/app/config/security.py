"""Security helpers for password hashing and verification.

bcrypt limits passwords to 72 bytes. We truncate longer passphrases
before hashing and verification to match the bcrypt constraint.
"""

import bcrypt


def _truncate(password: str) -> bytes:
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_truncate(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(_truncate(plain_password), hashed_password.encode("utf-8"))
