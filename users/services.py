from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from users.models import UserModel
from core.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from core.security import get_password_hash
from jose import JWTError, jwt
from core.config import get_settings  

# Initialize settings
settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def create_user_account(data, db):
    try:
        # Check if the user already exists by email or username
        user = db.query(UserModel).filter(
            (UserModel.email == data.email) | (UserModel.username == data.username)
        ).first()
        
        if user:
            raise HTTPException(status_code=422, detail="Email or username is already registered with us.")

        new_user = UserModel(
            username=data.username, 
            email=data.email,
            password=get_password_hash(data.password),
            is_active=False,
            is_verified=False,
            registered_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except IntegrityError:
        db.rollback()  # Roll back the session on error
        raise HTTPException(status_code=400, detail="Database integrity error.")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # Use the settings for decoding the token
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
