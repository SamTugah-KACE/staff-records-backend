# Apis/routers/superadmin_auth.py
from fastapi import APIRouter, Form, Response, HTTPException, Depends
from sqlalchemy.orm import Session
from database.db_session import get_db
from Models.superadmin import SuperAdmin
from Utils.security import Security
from Utils.config import ProductionConfig

settings = ProductionConfig()
global_security = Security(secret_key=settings.SECRET_KEY, algorithm=settings.ALGORITHM, token_expire_minutes=480)

router = APIRouter(prefix="/superadmin/auth", tags=["SuperAdminAuth"])

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
    
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": sa.username,
        "dashboard_url": "/superadmin/dashboard"
    }
