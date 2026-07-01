import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User
from app.schemas.auth_schema import UserRegister


class UserRepository:

    @staticmethod
    def find_by_username(username: str, db: Session) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def find_by_email(email: str, db: Session) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def find_by_refresh_token(token: str, db: Session) -> Optional[User]:
        stmt = select(User).where(User.refresh_token == token)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create(payload: UserRegister, hashed_password: str, db: Session) -> User:
        user = User(
            id=str(uuid.uuid4()),
            username=payload.username,
            email=payload.email,
            hashed_password=hashed_password,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def save_refresh_token(user: User, token: str, expiry: datetime, db: Session) -> None:
        user.refresh_token = token
        user.refresh_token_expiry_time = expiry
        db.commit()

    @staticmethod
    def clear_refresh_token(user: User, db: Session) -> None:
        user.refresh_token = None
        user.refresh_token_expiry_time = None
        db.commit()
