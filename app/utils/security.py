from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.config import settings
import hashlib
import base64
import bcrypt

# CryptContext configures which hashing algorithm to use
# bcrypt is the industry standard for passwords — deliberately slow
# "deliberately slow" is a feature, not a bug — makes brute force attacks
# take years instead of seconds

def _prepare_password(plain_password: str) -> bytes:
    """
    Pre-hash with SHA-256 to eliminate bcrypt's 72 byte limit.
    Returns bytes — bcrypt works with bytes natively.
    """
    password_bytes = plain_password.encode("utf-8")
    sha256_hash = hashlib.sha256(password_bytes).digest()
    return base64.b64encode(sha256_hash)

# ── Password functions ─────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """
    Hash a password using bcrypt directly.
    Returns a string for storage in PostgreSQL.
    """
    prepared = _prepare_password(plain_password)

    # bcrypt.hashpw needs bytes input and a salt
    # gensalt() generates a random salt with work factor 12 by default
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(prepared, salt)

    # decode to string for database storage
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a bcrypt hash.
    Returns True if match, False otherwise.
    """
    prepared = _prepare_password(plain_password)

    # bcrypt.checkpw handles the comparison safely
    # it's timing-attack resistant unlike plain == comparison
    return bcrypt.checkpw(prepared, hashed_password.encode("utf-8"))


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