# Apis/routers/superadmin_auth.py
from fastapi import APIRouter, Form, Response, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from Crud.auth import get_current_user
from database.db_session import get_db
from Models.superadmin import SuperAdmin
from Utils.security import Security
from Utils.config import ProductionConfig
from cachetools import TTLCache
from uuid import uuid4



settings = ProductionConfig()
global_security = Security(secret_key=settings.SECRET_KEY, algorithm=settings.ALGORITHM, token_expire_minutes=480)

router = APIRouter(prefix="/superadmin/auth", tags=["SuperAdminAuth"])



# Store token<->user_id mapping for 10 minutes (or whatever timeout you prefer)
temporary_dashboard_links = TTLCache(maxsize=1000, ttl=600)  # 10 mins


@router.post("/login", response_model=dict)
def superadmin_login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    security_key: str = Form(...),
    db: Session = Depends(get_db)
):
    sa = db.query(SuperAdmin).filter_by(username=username, is_active=True).first()
    if not sa or not global_security.verify_password(password, sa.hashed_password):
        raise HTTPException(401, "Invalid username or password")

    if not global_security.verify_password(security_key, sa.security_key_hash):
        raise HTTPException(401, "Invalid security key")

    token = global_security.create_access_token({"sub": str(sa.id), "role": "super_admin"})
    
    # Set the JWT as an HttpOnly, Secure cookie
    # Here we name the cookie "access_token"; adjust domain/path as needed for production
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,        # only send over HTTPS in production
        samesite="lax",     # prevents CSRF, adjust per your needs
        max_age=60 * 60 * 8 # e.g. 8 hours
    )

    # Generate unique dashboard UUID
    dashboard_id = str(uuid4())
    temporary_dashboard_links[dashboard_id] = sa.id
    
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": sa.username,
        "dashboard_url": f"/dev/dashboard/{dashboard_id}",
    }



@router.get("/dashboard/{dashboard_id}")
def protected_dashboard(
    dashboard_id: str,
    token: str = Depends(get_current_user),  # Assuming you have a dependency to get the current user
):
    if dashboard_id not in temporary_dashboard_links:
        raise HTTPException(403, "Invalid or expired dashboard link")

    user_id = temporary_dashboard_links[dashboard_id]
    if str(token.get("sub")) != str(user_id):
        raise HTTPException(403, "You are not authorized to access this dashboard.")

    # Serve dashboard or return JSON data here
    return {"message": "Welcome to your dashboard"}

