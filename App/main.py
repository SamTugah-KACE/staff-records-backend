import asyncio
import datetime
import json
from typing import Dict, List
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from Apis.default import create_default_permissions
from Apis.routers import api
from database.db_session import temp_db, SessionLocal
from sqlalchemy.orm import Session
from notification.socket import manager
from Utils.daily_checks import schedule_daily_checks


# Initialize FastAPI app
app = FastAPI(
    title="Staff Management and Appraisal System",
    description="A robust system for managing staff records, appraisals, and related functionalities.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Static Files (if needed)
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS Configuration
origins = [
    "http://localhost:3000",  # React development
    "http://127.0.0.1:3000",
    "https://gi-kace-solutions.onrender.com",  # Update with production frontend URL
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api)

# Root Endpoint
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Staff Management and Appraisal System API!"}

@app.websocket("/ws/notifications/{organization_id}/{user_id}")
async def websocket_notifications(websocket: WebSocket, organization_id: str, user_id: str):
    """
    WebSocket for sending real-time notifications/reminders to a user.
    
    **Usage Example:**  
      Connect from the frontend to:  
      ws://<server>/ws/notifications/<organization_id>/<user_id>
      
    The server sends periodic reminders (e.g., about inactivity or token expiration).
    """
    await manager.connect(organization_id, websocket)
    try:
        while True:
            await asyncio.sleep(60)  # Send a reminder every 60 seconds.
            reminder = f"Reminder: User {user_id}, please stay active to avoid auto-logout."
            await manager.send_personal_message(reminder, websocket)
    except WebSocketDisconnect:
        manager.disconnect(organization_id, websocket)

# In-memory storage for pending chat messages.
pending_messages: Dict[str, List[Dict]] = {}



@app.websocket("/ws/chat/{organization_id}/{user_id}")
async def websocket_chat(websocket: WebSocket, organization_id: str, user_id: str):
    """
    WebSocket endpoint for real-time chat/messaging between users.
    
    **Usage Example:**  
      Connect from the frontend to:  
      ws://<server>/ws/chat/<organization_id>/<user_id>
      
    If the recipient is offline, messages are stored in memory (pending for up to 24 hours).
    After 24 hours, messages expire.
    """
    await manager.connect(organization_id, websocket)
    try:
        # Send any pending messages for the connected user.
        if user_id in pending_messages:
            for msg in pending_messages[user_id]:
                await websocket.send_text(msg["message"])
            # Retain only messages that are less than 24 hours old.
            pending_messages[user_id] = [msg for msg in pending_messages[user_id]
                                          if (datetime.datetime.utcnow() - msg["timestamp"]).total_seconds() < 86400]
        while True:
            data = await websocket.receive_text()
            # Expect data as JSON: {"recipient_id": "user_uuid", "message": "text"}
            data_obj = json.loads(data)
            recipient = data_obj.get("recipient_id")
            message = data_obj.get("message")
            sent = False
            # If the recipient is connected, deliver immediately.
            if recipient in manager.active_connections:
                for conn in manager.active_connections[recipient]:
                    await conn.send_text(message)
                sent = True
            # Otherwise, store the message in pending_messages.
            if not sent:
                pending_messages.setdefault(recipient, []).append({
                    "message": message,
                    "timestamp": datetime.datetime.utcnow()
                })
    except WebSocketDisconnect:
        manager.disconnect(organization_id, websocket)

# Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred. Please try again later."},
    )

# Startup Event
# @app.on_event("startup")
async def on_startup():
    """
    Actions to perform on application startup.
    Example: Initializing a temporary database, loading configurations, etc.
    """,
    try:
        # Initialize database schema
        temp_db()

        # Create a synchronous session
        db: Session = SessionLocal()
        try:
            create_default_permissions(db=db)
        finally:
            db.close()
        
        # Start the APScheduler job for daily checks.
        schedule_daily_checks()

        print("Application startup tasks completed.")

    except Exception as e:
        print(f"An error occurred during startup: {str(e)}")
        raise RuntimeError("Failed to start the application. Please check the logs.") from e
    

app.add_event_handler("startup", on_startup)
    


# Shutdown Event
# @app.on_event("shutdown")
async def on_shutdown():
    """
    Actions to perform on application shutdown.
    Example: Closing database connections, releasing resources, etc.
    """
    # app.state.db.close()
    print("Application shutdown tasks completed.")
    

app.add_event_handler("shutdown", on_shutdown)