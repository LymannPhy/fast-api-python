from fastapi import FastAPI
from fastapi.responses import JSONResponse
from users.routes import guest_router, user_router  # Import both routers
from auth.route import router as auth_router
from core.security import JWTAuth
from starlette.middleware.authentication import AuthenticationMiddleware

app = FastAPI()

# Include both guest and user routers
app.include_router(guest_router)
app.include_router(user_router)
app.include_router(auth_router)

# Add Middleware
app.add_middleware(AuthenticationMiddleware, backend=JWTAuth())
