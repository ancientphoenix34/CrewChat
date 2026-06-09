from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings

# CryptContext is passlib's way of configuring the hashing algorithm.
# Node parallel: import bcrypt from 'bcrypt' — same library, same algorithm.
# schemes=["bcrypt"] → use bcrypt. deprecated="auto" → auto-upgrade old hashes.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password utilities ────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    # Node parallel: bcrypt.hashSync(plain, 12)
    # passlib handles the cost factor (12 rounds) via the CryptContext config above.
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    # Node parallel: bcrypt.compareSync(plain, hashed)
    # Timing-safe — won't leak information through response time differences.
    return pwd_context.verify(plain, hashed)


# ── JWT utilities ─────────────────────────────────────────────────────────────

def create_access_token(user_id: UUID, org_id: UUID, role: str) -> str:
    # Node parallel: jwt.sign({ sub: userId, orgId, role }, SECRET_KEY, { expiresIn: '7d' })
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),   # "sub" (subject) is the JWT standard claim for user identity
        "org_id": str(org_id),
        "role": role,
        "exp": expire,         # "exp" is the standard expiry claim — jose validates this automatically
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    # Node parallel: jwt.verify(token, SECRET_KEY)
    # Raises JWTError if the token is invalid, expired, or tampered with.
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload
    except JWTError:
        raise  # caller (get_current_user dependency) handles this and returns 401
