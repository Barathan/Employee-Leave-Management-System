"""
Security helpers: password hashing (bcrypt) and JWT issuing/decoding.

NOTE: SECRET_KEY is read from an environment variable so it can be changed
per-deployment without touching code. A fallback is provided purely for local
development/demo convenience -- always override it in production.

We call the `bcrypt` library directly instead of going through `passlib`.
`passlib` has been unmaintained since 2020 and its bcrypt backend breaks on
bcrypt>=4.1 (its version-detection shim errors out). Calling bcrypt directly
avoids that entirely and has no extra dependency cost since bcrypt is already
required.
"""
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import jwt

SECRET_KEY = os.getenv("LEAVE_APP_SECRET_KEY", "dev-only-secret-change-me-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hour session

# bcrypt has a hard 72-byte input limit; truncate defensively so very long
# passwords don't raise instead of just being capped.
_MAX_PASSWORD_BYTES = 72


def _prep(password: str) -> bytes:
    return password.encode("utf-8")[:_MAX_PASSWORD_BYTES]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_prep(plain_password), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    hashed = bcrypt.hashpw(_prep(password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
