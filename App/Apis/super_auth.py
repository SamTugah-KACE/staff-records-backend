# Apis/routers/superadmin_auth.py
from fastapi import APIRouter, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from database.db_session import get_db
from Models.superadmin import SuperAdmin
from Utils.security import Security


router = APIRouter(prefix="/superadmin/auth", tags=["SuperAdminAuth"])

@router.post("/login", response_model=dict)
def superadmin_login(
    username: str = Form(...),
    password: str = Form(...),
    security_key: str = Form(...),
    db: Session = Depends(get_db)
):
    sa = db.query(SuperAdmin).filter_by(username=username, is_active=True).first()
    if not sa or not Security.verify_password(password, sa.hashed_password):
        raise HTTPException(401, "Invalid username or password")

    if not Security.verify_password(security_key, sa.security_key_hash):
        raise HTTPException(401, "Invalid security key")

    token = Security.create_access_token({"sub": str(sa.id), "role": "super_admin"})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": sa.username,
        "dashboard_url": "/superadmin/dashboard"
    }
