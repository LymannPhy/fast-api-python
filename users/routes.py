from fastapi import APIRouter, status, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from core.database import get_db
from users.schemas import CreateUserRequest
from users.services import create_user_account, get_current_user
from core.security import oauth2_scheme
from users.responses import UserResponse
from users.models import UserModel

# Define two separate routers
guest_router = APIRouter(
    prefix="/guest",
    tags=["Guest"],
    responses={404: {"description": "Not found"}},
)

user_router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)

@guest_router.post('', status_code=status.HTTP_201_CREATED)
async def create_guest(data: CreateUserRequest, db: Session = Depends(get_db)):
    await create_user_account(data=data, db=db)
    payload = {"message": "Guest account has been successfully created."}
    return JSONResponse(content=payload)

# Update the /me route
@user_router.get('/me', response_model=UserResponse)
async def get_user_detail(current_user: UserModel = Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return current_user
