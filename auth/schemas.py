# auth/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Schema for user registration
class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

# Schema for user login
class UserLogin(BaseModel):
    username: str
    password: str

# Response schema after successful user creation or login
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    registered_at: Optional[datetime] = None

    class Config:
        orm_mode = True  # Allows returning ORM objects from database

# Token response for JWT authentication
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class VerifyCodeRequest(BaseModel):
    email: str
    code: str


class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str
    confirm_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

