from sqlalchemy import Boolean, Column, Integer, String, DateTime, func
from datetime import datetime
from core.database import Base

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)  # Add username field
    email = Column(String(255), unique=True, index=True)
    password = Column(String(100))
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)
    verification_code_expiration = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True, default=None)
    registered_at = Column(DateTime, nullable=True, default=None)
    reset_password_code = Column(String, nullable=True)  
    reset_password_code_expiration = Column(DateTime, nullable=True)  
    updated_at = Column(DateTime, nullable=True, default=None, onupdate=datetime.now)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
