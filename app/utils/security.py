from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# CryptContext configures which hashing algorithm to use
# bcrypt is the industry standard for passwords — deliberately slow
# "deliberately slow" is a feature, not a bug — makes brute force attacks
# take years instead of seconds
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password functions ─────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """
    Convert a plain text password to a bcrypt hash.

    "mypassword123" → "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36..."

    The hash includes:
    - The algorithm ($2b$)
    - The work factor ($12$ — how many rounds of hashing)
    - A random salt (prevents rainbow table attacks)
    - The actual hash

    All of this is stored in one string — passlib handles it automatically.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain password matches a stored hash.
    Returns True if match, False if not.

    We never "decrypt" the hash — we hash the input again
    and compare. That's how one-way hashing works.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT functions ──────────────────────────────────────────────

def create_access_token(user_id: int) -> str:
    """
    Create a signed JWT token containing the user's ID.

    The token encodes:
    - sub (subject): the user_id — who this token belongs to
    - exp (expiry): when the token stops being valid
    """
    expiry = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRY_MINUTES
    )

    payload = {
        "sub": str(user_id),   # "sub" is standard JWT claim for subject
        "exp": expiry
    }

    # jwt.encode signs the payload with our secret key
    # If anyone changes the payload, this signature becomes invalid
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return token


def decode_access_token(token: str) -> Optional[int]:
    """
    Verify a JWT token and extract the user_id from it.

    Returns user_id if valid, None if invalid or expired.

    This function handles:
    - Invalid signature (someone tampered with the token)
    - Expired token (past the exp timestamp)
    - Malformed token (not a valid JWT at all)
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = int(payload.get("sub"))
        return user_id

    except JWTError:
        # JWTError covers all failure cases:
        # expired, invalid signature, malformed
        return None