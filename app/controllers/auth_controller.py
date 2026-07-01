import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.schemas.auth_schema import UserRegister, UserLogin, TokenResponse
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_refresh_token_expiry,
)

logger = logging.getLogger(__name__)


class AuthController:

    @staticmethod
    def register(payload: UserRegister, db: Session) -> User:
        logger.info("Register attempt — username=%s", payload.username)

        if UserRepository.find_by_username(payload.username, db):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{payload.username}' is already taken",
            )
        if UserRepository.find_by_email(payload.email, db):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{payload.email}' is already registered",
            )

        user = UserRepository.create(payload, hash_password(payload.password), db)
        logger.info("User registered successfully — id=%s", user.id)
        return user

    @staticmethod
    def login(payload: UserLogin, db: Session) -> TokenResponse:
        logger.info("Login attempt — username=%s", payload.username)

        user = UserRepository.find_by_username(payload.username, db)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        access_token = create_access_token(data={"sub": user.username})
        refresh_token = create_refresh_token()
        expiry = get_refresh_token_expiry()

        UserRepository.save_refresh_token(user, refresh_token, expiry, db)
        logger.info("Login successful — username=%s", payload.username)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    def refresh(refresh_token: str, db: Session) -> TokenResponse:
        logger.info("Token refresh attempt")

        user = UserRepository.find_by_refresh_token(refresh_token, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if not user.refresh_token_expiry_time:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has no expiry — please log in again",
            )

        # Normalize to UTC for comparison
        expiry = user.refresh_token_expiry_time
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        if expiry < datetime.now(timezone.utc):
            UserRepository.clear_refresh_token(user, db)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired — please log in again",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        new_access_token = create_access_token(data={"sub": user.username})
        new_refresh_token = create_refresh_token()
        new_expiry = get_refresh_token_expiry()

        UserRepository.save_refresh_token(user, new_refresh_token, new_expiry, db)
        logger.info("Token refreshed — username=%s", user.username)
        return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)

    @staticmethod
    def logout(current_user: User, db: Session) -> None:
        logger.info("Logout — username=%s", current_user.username)
        UserRepository.clear_refresh_token(current_user, db)
