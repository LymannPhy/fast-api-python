from pydantic import BaseModel, EmailStr
from datetime import datetime

class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class VerifyCodeRequest(BaseModel):
    email: str
    code: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    is_verified: bool
    registered_at: datetime
    verified_at: datetime = None
    
    class Config:
        orm_mode = True 