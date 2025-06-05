# src/api/deps_ws.py
from fastapi import WebSocket, status, Depends, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security.http import HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session
from Crud.auth import get_current_user    # your HTTP function
from database.db_session import get_db
from jose import jwt, JWTError
from Models import models
from Utils.config import ProductionConfig

settings = ProductionConfig()

bearer_scheme = HTTPBearer(auto_error=False)

# async def get_current_user_ws(
#     websocket: WebSocket,
#     db: Session = Depends(get_db),
# ):
#     """
#     1) Read the `Authorization: Bearer <token>` header from the WebSocket handshake.
#     2) Wrap it into HTTPAuthorizationCredentials.
#     3) Call your existing get_current_user to do all the work.
#     """
#     # manually run the HTTPBearer on the WebSocket scope
#     credentials: HTTPAuthorizationCredentials = await bearer_scheme.__call__(websocket)
#     if credentials is None or credentials.scheme.lower() != "bearer":
#         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#         return

#     try:
#         user_ctx = await get_current_user(credentials, db)
#         return user_ctx
#     except Exception:
#         # invalid token, expired, inactivity, etc.
#         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)



async def get_current_user_ws(token: str, db: Session):
    """
    Decode JWT 'sub' → user.id, fetch User.
    Raises if invalid.
    """
    try:
        print(f"\n\nTOKEN: {token}   \n\n")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print("payload:: ", payload)
        user_id: str = payload.get("user_id")
        print("user_id: ", user_id)
        if not user_id:
            raise JWTError()
    except JWTError:
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)
    return user