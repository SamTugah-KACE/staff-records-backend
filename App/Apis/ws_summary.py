import asyncio
from fastapi import Depends, Query, WebSocket, WebSocketDisconnect, APIRouter, status
from sqlalchemy.orm import Session
from Models.Tenants.organization import Organization
from database.db_session import get_db
from .deps_ws import get_current_user_ws
from notification.socket import manager
import json
from uuid import UUID
from .summary import _build_summary_payload, build_summary_payload_async
from Models.Tenants.role import Role
from fastapi.encoders import jsonable_encoder


router = APIRouter()


@router.websocket("/ws/summary/{organization_id}/{user_id}")
async def websocket_summary(
    websocket: WebSocket,
    organization_id: str,
    user_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    # 1) Authenticate
    try:
        user = await get_current_user_ws(token, db)
        print("✅ user in ws_summary:", user.id, "org:", user.organization_id)
    except Exception:
        print("❌ auth failed, closing")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 2) Tenant + identity check
    if str(user.organization_id) != organization_id or str(user.id) != user_id:
        print("❌ tenant/user mismatch:", user.organization_id, organization_id, user.id, user_id)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 3) Accept & register
    await websocket.accept()
    await manager.register(organization_id, user_id, websocket)
    print("✅ websocket accepted & registered")

    try:
        # 4) Validate org exists (use filter().first())
        try:
            org_uuid = UUID(organization_id)
        except ValueError:
            print("❌ invalid UUID")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            await manager.unregister(organization_id, user_id, websocket)
            return

        org = db.query(Organization).filter(Organization.id == org_uuid).first()
        if not org:
            print("❌ organization not found in DB")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            await manager.unregister(organization_id, user_id, websocket)
            return
        print("✅ organization loaded:", org.id)

        # 5) Build & send initial summary
        # payload = await _build_summary_payload(db, org_uuid)
        payload = await build_summary_payload_async(db, org_uuid)
        # print("\n\nschema_obj:: ", schema_obj)
        # payload = jsonable_encoder(schema_obj)  # <-- turns Pydantic schema into plain dict
        # print("\n\njsonable thing")
        # payload = schema_obj
        message = {"type": "initial", "payload": payload}
        await websocket.send_json(message)
        print("✅ sent initial payload")

        try:
            while True:
                # await asyncio.sleep(3600)
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            await manager.unregister(organization_id, user_id, websocket)

        # 6) Wait for “refresh”
        # while True:
        #     data = await websocket.receive_text()
        #     if data == "refresh":
        #         schema_obj = await _build_summary_payload(db, org_uuid)
        #         payload = jsonable_encoder(schema_obj)
        #         await websocket.send_json({"type": "update", "payload": payload})
        #         print("✅ sent update payload")
        #     else:
        #         continue

    except WebSocketDisconnect:
        print("🔌 websocket disconnected by client")
        await manager.unregister(organization_id, user_id, websocket)

    except Exception as exc:
        print("🔥 unexpected error in ws_summary:", exc)
        if websocket.client_state.name != "CLOSED":
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        await manager.unregister(organization_id, user_id, websocket)


# @router.websocket("/ws/summary/{organization_id}/{user_id}")
# async def websocket_summary(
#     websocket: WebSocket,
#     organization_id: str,
#     user_id: str,
#     token: str = Query(...),
#     db: Session = Depends(get_db),
# ):
#     """
#     WebSocket that immediately pushes the organization-wide summary counts, 
#     and will respond to "refresh" messages by re‐sending an updated snapshot.
#     Clients connect to:
#       wss://…/ws/summary/{org_id}/{user_id}?token=<jwt>
#     """
#     # 1) Authenticate
#     try:
#         print("WebSocket summary connection attempt with token:", token)
#         if not token:
#             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#             return
#         user = await get_current_user_ws(token, db)
#         print("user identified in ws summary:", user)
#     except Exception:
#         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#         return

#     print(f"WebSocket connection attempt for org_id={organization_id}, user_id={user_id}\n\n{str(user.organization_id) != organization_id or str(user.id) != user_id}")
#     # 2) Tenant + identity check
#     if str(user.organization_id) != organization_id or str(user.id) != user_id:
#         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#         return

#     # 3) Accept & register
#     await websocket.accept()
#     await manager.register(organization_id, user_id, websocket)

#     try:
#         # 4) Validate org_id as a UUID, ensure it exists
#         try:
#             org_uuid = UUID(organization_id)
#         except ValueError:
#             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#             await manager.unregister(organization_id, user_id, websocket)
#             return

#         org = db.query(Organization).get(org_uuid)
#         if not org:
#             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#             await manager.unregister(organization_id, user_id, websocket)
#             return

#         # 5) Build and send initial summary
#         initial_payload = await _build_summary_payload(db, org_uuid)
#         print("Initial payload for WebSocket summary:", initial_payload)
#         await websocket.send_text(json.dumps({"type": "initial", "payload": initial_payload}))

#         # 6) Wait for client “refresh” messages to re‐send updated payload
#         while True:
#             data = await websocket.receive_text()
#             if data == "refresh":
#                 new_payload = await _build_summary_payload(db, org_uuid)
#                 await websocket.send_text(json.dumps({"type": "update", "payload": new_payload}))
#             else:
#                 continue

#     except WebSocketDisconnect:
#         await manager.unregister(organization_id, user_id, websocket)
#     except Exception:
#         if websocket.client_state.name != "CLOSED":
#             await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
#         await manager.unregister(organization_id, user_id, websocket)