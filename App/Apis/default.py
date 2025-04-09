import json
from sqlalchemy.dialects.postgresql import  JSONB
from sqlalchemy.orm import  Session
from sqlalchemy.exc import SQLAlchemyError
from database.db_session import BaseModel
from Models.models import DataBank
import logging
from datetime import datetime
from fastapi import FastAPI, APIRouter, Depends, HTTPException, BackgroundTasks, Query, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID 
from typing import List, Optional
from database.db_session import get_db  # Your database session dependency
from Crud.crud import CRUDBase as crud # Generic CRUD class
from Models.models import DataBank  # Import your models
from Schemas.schemas import DataBankSchema, DataCreateBankSchema  # Import your Pydantic schemas




# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Standardized permissions as provided.
standard_permissions = [
    # --- Employee Records Management ---
    "employee:create",          # Create new employee records
    "employee:read",            # View employee details
    "employee:update",          # Update employee records
    "employee:delete",          # Delete employee records
    "employee:archive",         # Archive employee records
    "employee:transfer",        # Transfer employee between departments

    # --- Organizational & Role Management ---
    "organization:read",        # View organization details and settings
    "organization:update",      # Modify organization configurations
    "role:manage",              # Create, update, delete roles and assign permissions
    "user:assignRole",          # Assign roles to users
    "audit:read",               # View audit logs

    # --- Attendance and Time Tracking ---
    "attendance:record",        # Record or adjust attendance entries
    "attendance:read",          # View attendance records
    "attendance:update",        # Update attendance information
    "leave:apply",              # Apply for leave
    "leave:approve",            # Approve leave applications
    "leave:manage",             # Manage leave requests (cancel/update)

    # --- Payroll and Benefits Administration ---
    "payroll:process",          # Initiate and oversee payroll processing
    "payroll:read",             # View payroll details and payslips
    "payroll:update",           # Adjust payroll data prior to processing
    "benefits:manage",          # Administer employee benefit programs
    "payroll:report",           # Generate payroll reports

    # --- Recruitment & Onboarding ---
    "recruitment:create",       # Post new job listings and openings
    "recruitment:read",         # View recruitment data and applicant details
    "recruitment:update",       # Update job postings or applicant status
    "recruitment:delete",       # Remove outdated recruitment data
    "onboarding:manage",        # Manage onboarding for new hires

    # --- Performance Management ---
    "performance:review:create",    # Initiate performance review cycles
    "performance:review:read",      # Access performance review records
    "performance:review:update",    # Modify performance reviews as needed
    "performance:goal:manage",      # Set and track employee performance goals

    # --- Security and Compliance ---
    "security:read",            # View security logs and alerts
    "security:update",          # Update security configurations (e.g., policies, MFA)
    "compliance:read",          # Access compliance reports and audit data
    "compliance:update",        # Update compliance-related settings

    # --- Reporting and Analytics ---
    "report:generate",          # Create custom HR reports
    "report:read",              # View pre-generated or dynamic report data

    # --- Dashboard Routing for Dynamic UI ---
    "hr:dashboard",             # Access the HR Manager Dashboard view
    "department:head:dashboard",# Access the Department Head Dashboard view
    "staff:dashboard",          # Access the generic Staff Dashboard view
    "admin:dashboard",          # Access the Admin Dashboard view
    "manager:dashboard",        # Access the Manager Dashboard view
    "branch:manager:dashboard", # Access the Branch Manager Dashboard view
    "finance:dashboard",        # Access the Finance Dashboard view
    
    "hr:dashboard:read",        # View HR Dashboard data
    "hr:dashboard:update",      # Update HR Dashboard settings
    "hr:dashboard:create",      # Create new HR Dashboard entries
    "hr:dashboard:delete",      # Delete HR Dashboard entries
    
    "hr:dashboard:archive",     # Archive HR Dashboard entries
    "hr:dashboard:transfer",    # Transfer HR Dashboard entries
    
    "hr:dashboard:report",      # Generate HR Dashboard reports
    "hr:dashboard:analytics",   # Access HR Dashboard analytics
    "hr:dashboard:permissions", # Manage HR Dashboard permissions
    "hr:dashboard:settings",    # Update HR Dashboard settings
    "hr:dashboard:notifications",# Manage HR Dashboard notifications
    "hr:dashboard:alerts",      # View HR Dashboard alerts
    "hr:dashboard:logs",        # Access HR Dashboard logs
    "hr:dashboard:history",     # View HR Dashboard history
    "hr:dashboard:comments",    # Manage HR Dashboard comments
    "hr:dashboard:feedback",    # Provide feedback on HR Dashboard entries
    "hr:dashboard:reviews",     # Manage HR Dashboard reviews
    "hr:dashboard:ratings",     # Rate HR Dashboard entries
    "hr:dashboard:tags",        # Tag HR Dashboard entries
    "hr:dashboard:categories",  # Categorize HR Dashboard entries
    "hr:dashboard:groups",      # Group HR Dashboard entries
    "hr:dashboard:filters",     # Filter HR Dashboard entries
    "hr:dashboard:search",      # Search HR Dashboard entries
    "hr:dashboard:sort",        # Sort HR Dashboard entries
    "hr:dashboard:export",      # Export HR Dashboard entries
    "hr:dashboard:import",      # Import HR Dashboard entries
    "hr:dashboard:sync",        # Sync HR Dashboard entries
    "hr:dashboard:backup",      # Backup HR Dashboard entries
    "hr:dashboard:restore",     # Restore HR Dashboard entries
    "hr:dashboard:clone",       # Clone HR Dashboard entries
    "hr:dashboard:duplicate",   # Duplicate HR Dashboard entries
    "hr:dashboard:merge",       # Merge HR Dashboard entries
    "hr:dashboard:split",       # Split HR Dashboard entries
    "hr:dashboard:combine",     # Combine HR Dashboard entries
    "hr:dashboard:link",        # Link HR Dashboard entries
    "hr:dashboard:unlink",      # Unlink HR Dashboard entries
    "hr:dashboard:connect",     # Connect HR Dashboard entries
    "hr:dashboard:disconnect",  # Disconnect HR Dashboard entries
    "hr:dashboard:integrate",   # Integrate HR Dashboard entries
    "hr:dashboard:api",         # Access HR Dashboard API
    "hr:dashboard:webhook",     # Manage HR Dashboard webhooks
    "hr:dashboard:events",      # Manage HR Dashboard events
    "hr:dashboard:triggers",    # Manage HR Dashboard triggers
    "hr:dashboard:actions",     # Manage HR Dashboard actions
    "hr:dashboard:workflows",   # Manage HR Dashboard workflows
    "hr:dashboard:processes",   # Manage HR Dashboard processes
    "hr:dashboard:tasks",       # Manage HR Dashboard tasks
    "hr:dashboard:jobs",        # Manage HR Dashboard jobs
    "hr:dashboard:queues",      # Manage HR Dashboard queues
    "hr:dashboard:threads",     # Manage HR Dashboard threads
    "hr:dashboard:workers",     # Manage HR Dashboard workers
    "hr:dashboard:services",    # Manage HR Dashboard services
    "hr:dashboard:applications",# Manage HR Dashboard applications
    "hr:dashboard:platforms",   # Manage HR Dashboard platforms




    ]



def create_default_permissions(db: Session):
    """
    Efficiently seeds default roles into the databank table.
    Ensures atomicity, handles duplicates, and appends new roles to the existing structure.
    """
    

    try:
        # print("\n\ndb:: ", db)
        # print("\n\nDatabank:: ", DataBank)
        with db.begin():  # Begin a transaction
            # Fetch or create the databank entry for roles
            databank_entry = db.query(DataBank).filter(DataBank.data_name == "permissions").first()
            # print("databank_entry:: ", databank_entry)
            if not databank_entry:
                # If no existing entry, create a new one
                databank_entry = DataBank(data_name="permissions", data=standard_permissions)
                db.add(databank_entry)
            else:
                # Check for duplicates and append new roles
                # existing_ = databank_entry.data
                # new_data = [
                #     permission for permission in standard_permissions
                #     if permission not in existing_  # Ensure uniqueness
                #     and isinstance(permission, str)  # Ensure it's a string
                #     and permission not in existing_  # Check if the permission is not already present
                #     if not any(existing_permission["name"] == permission["name"] for existing_permission in existing_)
                # ]
                # if new_data:
                #     databank_entry.data.extend(new_data)  # Append only unique permissions
                # Update the existing entry to include any missing permissions.
                existing_perms = set(databank_entry.data if databank_entry.data else [])
                updated_perms = existing_perms.union(set(standard_permissions))
                databank_entry.data = list(updated_perms)
                logger.info("Updated existing standard permissions in the DataBank entry.")

            # Commit changes
            db.commit()
            logger.info("Default roles seeded successfully.")

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"An error occurred while seeding default roles: {str(e)}")
        raise RuntimeError("Failed to seed default roles. Please check the logs.") from e
    

app = APIRouter()



from sqlalchemy.ext.mutable import MutableList

@app.post("/data-bank/", response_model=DataCreateBankSchema, status_code=status.HTTP_201_CREATED)
async def create_data_bank(
    data_name: str = Form(...),
    data: str = Form(...),  # Accept JSON string from form data
    db: Session = Depends(get_db),
):
    """
    Dynamic API to create or update entries in the DataBank table.
    Ensures uniqueness for incoming data and appends to existing data if the data_name exists.
    If the data_name does not exist, it creates a new entry.
    """
    try:
        # Parse `data` string into a dictionary or list
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid data format. Expected a valid JSON string.",
            )

        # Ensure parsed_data is a list for uniform processing
        if not isinstance(parsed_data, list):
            parsed_data = [parsed_data]

        # Fetch the databank entry for the given data_name
        databank_entry = db.query(DataBank).filter(DataBank.data_name == data_name).first()

        if databank_entry:
            # Debugging: Ensure data is correctly initialized
            if databank_entry.data is None:
                databank_entry.data = []

            # Debugging: Check data types and contents
            logger.debug(f"Existing data: {databank_entry.data}")
            logger.debug(f"New data: {parsed_data}")

            # Append only unique entries to the existing data
            def dict_to_tuple(d):
                return tuple(sorted((k, dict_to_tuple(v) if isinstance(v, dict) else v) for k, v in d.items()))

            existing_set = {dict_to_tuple(entry) for entry in databank_entry.data}
            new_data = [
                item for item in parsed_data
                if dict_to_tuple(item) not in existing_set
            ]

            logger.debug(f"Unique new data to append: {new_data}")

            if new_data:
                databank_entry.data.extend(new_data)
                db.commit()
                logger.info(f"Appended new data to existing data_name '{data_name}'.")
            else:
                logger.info(f"No new unique data to append for data_name '{data_name}'.")
        else:
            # Create a new entry if the data_name does not exist
            databank_entry = DataBank(data_name=data_name, data=parsed_data)
            db.add(databank_entry)
            db.commit()
            logger.info(f"Created new data_name '{data_name}' with initial data.")

        # Refresh and return the updated or newly created entry
        db.refresh(databank_entry)
        return DataCreateBankSchema(data_name=databank_entry.data_name, data=databank_entry.data)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the request. Please try again later.",
        )







@app.get("/fetch-all/", response_model=List[DataBankSchema])
def read_banks(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """
    List all default data
    """
    data = crud(DataBank)
    return data.get_multi(db, skip=skip, limit=limit)



@app.put("/data-bank/update/", response_model=DataCreateBankSchema, status_code=status.HTTP_200_OK)
async def update_data_bank(
    identifier: str = Form(...),  # Accept `data_name` or `id`
    key: str = Form(...),         # Key to identify the specific entry
    value: str = Form(...),       # Value of the key to match the specific entry
    data: str = Form(...),        # New data to update
    db: Session = Depends(get_db),
):
    """
    Dynamically update a specific entry in the DataBank based on `data_name` or `id`.
    Uses a provided key and value to locate the target entry in the `data` list.
    """
    try:
        # Parse the new data
        try:
            new_entry = json.loads(data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid data format. Expected a valid JSON string.",
            )

        if not isinstance(new_entry, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input: Expected a single dictionary for the new data.",
            )

        # Find the databank entry using `data_name` or `id`
        databank_entry = (
            db.query(DataBank)
            .filter(
                (DataBank.data_name == identifier) | (DataBank.id == identifier)
            )
            .first()
        )

        if not databank_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DataBank entry not found.",
            )

        # Find the index of the entry with the matching key-value pair
        existing_data = databank_entry.data
        index_to_update = next(
            (i for i, entry in enumerate(existing_data) if entry.get(key) == value),
            None
        )

        if index_to_update is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entry with `{key}`='{value}' not found.",
            )

        # Update the entry
        existing_data[index_to_update] = new_entry
        databank_entry.data = existing_data
        db.commit()
        db.refresh(databank_entry)

        return DataCreateBankSchema(data_name=databank_entry.data_name, data=databank_entry.data)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update the data. Please try again later.",
        )
