# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.utils.security import decode_access_token

# OAuth2PasswordBearer tells FastAPI:
# "look for a Bearer token in the Authorization header"
# tokenUrl is where clients go to GET a token (our login endpoint)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),   # extracts token from header
    db: Session = Depends(get_db)
) -> models.User:
    """
    FastAPI dependency that validates the JWT and returns the current user.

    Any route that declares:
        current_user: User = Depends(get_current_user)
    ...is automatically protected. No token = 401. Invalid token = 401.

    This runs BEFORE the route function body executes.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
        # WWW-Authenticate header is part of the HTTP standard
        # tells the client what kind of auth is expected
    )

    # Step 1: Decode and validate the token
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception

    # Step 2: Load the user from database
    # We do this to confirm the user still exists and is still active
    # A token could be valid but the user account deleted or deactivated
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.is_active == True
    ).first()

    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Extends get_current_user with an active check.
    Use this instead of get_current_user in most routes.

    Separation of concerns:
    - get_current_user: validates token, loads user
    - get_current_active_user: confirms user account is active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    return current_user