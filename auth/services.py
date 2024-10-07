from users.models import UserModel
from fastapi.exceptions import HTTPException
from core.security import verify_password, get_password_hash
from core.config import get_settings
from datetime import timedelta, datetime
from auth.responses import TokenResponse
from core.security import create_access_token, create_refresh_token, get_token_payload
from fastapi import Depends, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from auth.utils import send_verification_email, generate_verification_code, generate_code_expiration, send_password_reset_email
from auth.schemas import UserCreateRequest, ChangePasswordRequest

settings = get_settings()    

async def get_refresh_token(token: str, db: Session):   
    payload = get_token_payload(token=token)
    user_id = payload.get('id')
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return await _get_user_token(user=user, refresh_token=token)

    
def _verify_user_access(user: UserModel):
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Your account is inactive. Please contact support.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Your account is unverified. We have resent the account verification email.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def _get_user_token(user: UserModel, refresh_token: str = None):
    payload = {"id": user.id}
    
    access_token_expiry = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = await create_access_token(payload, access_token_expiry)
    
    if not refresh_token:
        refresh_token = await create_refresh_token(payload)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=access_token_expiry.total_seconds()  # total_seconds for precision
    )


async def login_user(data: OAuth2PasswordRequestForm, db: Session):
    user = db.query(UserModel).filter(
        (UserModel.username == data.username) | (UserModel.email == data.username)
    ).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Username or email is not registered with us.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=400,
            detail="Invalid login credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _verify_user_access(user)
    return await _get_user_token(user)


async def register_user(data: UserCreateRequest, db: Session, background_tasks: BackgroundTasks):
    existing_user = db.query(UserModel).filter(
        (UserModel.email == data.email) | (UserModel.username == data.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=422,
            detail="Username or email is already registered with us."
        )

    verification_code = generate_verification_code()
    expiration_time = generate_code_expiration(minutes=15)  # Code expires in 15 minutes

    new_user = UserModel(
        username=data.username,
        email=data.email,
        password=get_password_hash(data.password),
        verification_code=verification_code,
        verification_code_expiration=expiration_time,
        is_active=False,  # Inactive until verified
        is_verified=False,
        registered_at=datetime.utcnow(),  # UTC for consistency
        updated_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send verification code via email
    background_tasks.add_task(
        send_verification_email,
        email=new_user.email,
        username=new_user.username,
        verification_code=verification_code
    )

    return new_user

def verify_user_code(email: str, code: str, db: Session):
    """
    Verifies the user's code and activates the account if valid.
    """
    user = db.query(UserModel).filter(UserModel.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="User is already verified")

    if user.verification_code != code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    if user.verification_code_expiration < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification code has expired")

    # Mark the user as verified
    user.is_verified = True
    user.is_active = True
    user.verification_code = None  # Clear the code after verification
    user.verification_code_expiration = None
    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    return {"message": "Account verified successfully"}


# Forgot password service
async def forgot_password(email: str, db: Session, background_tasks: BackgroundTasks):
    """
    Service to handle forgot password functionality by sending a reset code.
    """
    user = db.query(UserModel).filter(UserModel.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    # Generate reset password code and expiration time
    reset_code = generate_verification_code() 
    expiration_time = generate_code_expiration(minutes=15)  # Code expires in 15 minutes

    # Save reset password code and expiration time in the user record
    user.reset_password_code = reset_code
    user.reset_password_code_expiration = expiration_time
    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    # Send reset code via email for password reset
    background_tasks.add_task(
        send_password_reset_email, 
        email=user.email,
        username=user.username,
        reset_code=reset_code  # Pass the reset_code instead of verification_code
    )

    return {"message": "Password reset code sent to email."}


# Reset password service
async def reset_password(email: str, code: str, new_password: str, confirm_password: str, db: Session):
    """
    Service to handle resetting the password after the user provides the reset code.
    """
    # Check if the new password and confirm password match
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = db.query(UserModel).filter(UserModel.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify the reset password code
    if user.reset_password_code != code:
        raise HTTPException(status_code=400, detail="Invalid reset code")

    if user.reset_password_code_expiration < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset code has expired")

    # Hash new password and save it
    user.password = get_password_hash(new_password)
    user.reset_password_code = None  # Clear the reset code
    user.reset_password_code_expiration = None
    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    return {"message": "Password reset successfully"}


async def change_password(user_id: int, data: ChangePasswordRequest, db: Session):
    """
    Service to change the user's password after validating the current password.
    """
    # Fetch the user by their ID
    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify the current password
    if not verify_password(data.current_password, user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Check if new password and confirm password match
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="New password and confirm password do not match")

    # Hash the new password and update the user's password
    user.password = get_password_hash(data.new_password)
    user.updated_at = datetime.utcnow()

    # Commit the changes to the database
    db.commit()
    db.refresh(user)

    return {"message": "Password changed successfully"}

