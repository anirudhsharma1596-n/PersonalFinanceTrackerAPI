# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas import UserCreate, UserResponse, Token
from app.utils.security import hash_password, verify_password, create_access_token
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ─────────────────────────────────────────
# POST /auth/register
# ─────────────────────────────────────────
@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.
    Validates email and username are not already taken.
    Stores hashed password — never the plain text.
    """

    # Check email not already registered
    if db.query(models.User).filter(
        models.User.email == payload.email
    ).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Check username not already taken
    if db.query(models.User).filter(
        models.User.username == payload.username
    ).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken"
        )

    user = models.User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password)
        # payload.password is the plain text
        # we hash it immediately and never store the original
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ─────────────────────────────────────────
# POST /auth/login
# ─────────────────────────────────────────
@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password, receive a JWT token.

    OAuth2PasswordRequestForm expects form data (not JSON) with:
    - username field (we treat this as email)
    - password field

    This is the OAuth2 standard — the field is called "username"
    even if you're using email. The Swagger UI /docs handles this
    automatically with a login form.
    """

    # Look up user by email
    # OAuth2PasswordRequestForm uses "username" field name
    # but we're using it to store the email
    user = db.query(models.User).filter(
        models.User.email == form_data.username
    ).first()

    # Same error whether user doesn't exist OR password is wrong
    # Never tell attackers which one failed — that leaks information
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user:
        raise invalid_credentials

    if not verify_password(form_data.password, user.hashed_password):
        raise invalid_credentials

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    # All checks passed — generate and return the token
    access_token = create_access_token(user_id=user.id)

    return Token(access_token=access_token)


# ─────────────────────────────────────────
# GET /auth/me
# ─────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
def get_me(current_user: models.User = Depends(get_current_active_user)):
    """
    Returns the currently authenticated user's profile.

    Notice how short this function is — all the heavy lifting
    (token validation, user loading) happens in the dependency.
    The route just returns what the dependency already loaded.

    This is the power of FastAPI's dependency injection.
    """
    return current_user