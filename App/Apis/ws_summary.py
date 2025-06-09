from fastapi import Depends, Query, WebSocket, WebSocketDisconnect, APIRouter, status
from sqlalchemy.orm import Session
from Models.Tenants.organization import Organization
from database.db_session import get_db
from .deps_ws import get_current_user_ws
from notification.socket import manager
import json
from uuid import UUID
from .summary import _build_summary_payload
from Models.Tenants.role import Role


router = APIRouter(prefix="/organizations", tags=["WebSocket Summary"])

@router.websocket("/ws/summary/{organization_id}/{user_id}")
async def websocket_summary(
    websocket: WebSocket,
    organization_id: str,
    user_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    WebSocket that immediately pushes the organization-wide summary counts, 
    and will respond to "refresh" messages by re‐sending an updated snapshot.
    Clients connect to:
      wss://…/ws/summary/{org_id}/{user_id}?token=<jwt>
    """
    # 1) Authenticate
    try:
        user = await get_current_user_ws(token, db)
        print("user identified in ws summary:", user)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    print(f"WebSocket connection attempt for org_id={organization_id}, user_id={user_id}\n\n{str(user.organization_id) != organization_id or str(user.id) != user_id}")
    # 2) Tenant + identity check
    if str(user.organization_id) != organization_id or str(user.id) != user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 3) Accept & register
    await websocket.accept()
    await manager.register(organization_id, user_id, websocket)

    try:
        # 4) Validate org_id as a UUID, ensure it exists
        try:
            org_uuid = UUID(organization_id)
        except ValueError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            await manager.unregister(organization_id, user_id, websocket)
            return

        org = db.query(Organization).get(org_uuid)
        if not org:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            await manager.unregister(organization_id, user_id, websocket)
            return

        # 5) Build and send initial summary
        initial_payload = await _build_summary_payload(db, org_uuid)
        await websocket.send_text(json.dumps({"type": "initial", "payload": initial_payload}))

        # 6) Wait for client “refresh” messages to re‐send updated payload
        while True:
            data = await websocket.receive_text()
            if data == "refresh":
                new_payload = await _build_summary_payload(db, org_uuid)
                await websocket.send_text(json.dumps({"type": "update", "payload": new_payload}))
            else:
                continue

    except WebSocketDisconnect:
        await manager.unregister(organization_id, user_id, websocket)
    except Exception:
        if websocket.client_state.name != "CLOSED":
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        await manager.unregister(organization_id, user_id, websocket)