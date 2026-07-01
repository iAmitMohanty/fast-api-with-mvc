from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: str | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    token: str
    expiresAt: str
    userId: str
    userName: str
    displayName: str
    refreshToken: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
