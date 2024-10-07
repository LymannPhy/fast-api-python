from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from starlette.authentication import AuthCredentials, UnauthenticatedUser
from datetime import timedelta, datetime
from jose import jwt, JWTError
from core.config import get_settings
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from users.models import UserModel

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # Updated from /auth/token to /auth/login

# Hash password
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Create an access token with expiration
async def create_access_token(data: dict, expiry: timedelta) -> str:
    payload = data.copy()
    expire_in = datetime.utcnow() + expiry
    payload.update({"exp": expire_in})
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

# Create a refresh token without expiration
async def create_refresh_token(data: dict) -> str:
    return jwt.encode(data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

# Decode the JWT token and return the payload
def get_token_payload(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        print(f"Token decoding failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# Get the current authenticated user from the token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserModel:
    payload = get_token_payload(token)
    if not payload or type(payload) is not dict:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get('id')
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# Authentication class for Starlette middleware integration
class JWTAuth:
    async def authenticate(self, conn):
        guest = AuthCredentials(['unauthenticated']), UnauthenticatedUser()
        
        if 'authorization' not in conn.headers:
            return guest
        
        token = conn.headers.get('authorization').split(' ')[1]  # Extract Bearer token
        if not token:
            return guest
        
        try:
            user = get_current_user(token=token)
        except HTTPException:
            return guest
        
        return AuthCredentials(['authenticated']), user

# Create a verification token for email verification
def create_verification_token(data: dict) -> str:
    expire_in = datetime.utcnow() + timedelta(hours=settings.EMAIL_TOKEN_EXPIRE_HOURS)
    payload = {"email": data["email"], "exp": expire_in}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
