from fastapi import APIRouter, status, Depends, Header, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from users.models import UserModel
from sqlalchemy.orm import Session
from core.database import get_db
from auth.services import get_refresh_token, login_user, register_user, verify_user_code, forgot_password, reset_password
from users.schemas import CreateUserRequest, VerifyCodeRequest
from auth.schemas import ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest
from core.security import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses={404: {"description": "Not found"}},
)

# Refresh token route
@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_access_token(refresh_token: str = Header(), db: Session = Depends(get_db)):
    return await get_refresh_token(token=refresh_token, db=db)

# Registration route
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: CreateUserRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return await register_user(data=data, db=db, background_tasks=background_tasks)

# Code verification route 
@router.post("/verify", status_code=status.HTTP_200_OK)
def verify_code(data: VerifyCodeRequest, db: Session = Depends(get_db)):
    return verify_user_code(email=data.email, code=data.code, db=db)

# login route
@router.post("/login", status_code=status.HTTP_200_OK)
async def login(data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return await login_user(data=data, db=db)

# Forgot password route
@router.post("/forgot-password", status_code=200)
async def forgot_password_route(data: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return await forgot_password(email=data.email, db=db, background_tasks=background_tasks)

# Reset password route
@router.post("/reset-password", status_code=200)
async def reset_password_route(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    return await reset_password(email=data.email, code=data.code, new_password=data.new_password, confirm_password=data.confirm_password, db=db)
 
# Change password route
@router.put("/change-password", status_code=status.HTTP_200_OK)
async def change_user_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) 
):
    return await change_password(user_id=current_user.id, data=data, db=db)