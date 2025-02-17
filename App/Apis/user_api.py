from datetime import date
import json
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks, Query, Form, status
from pydantic import EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict
from uuid import UUID
from database.db_session import get_db, get_async_db  # Dependency injection
from Models.Tenants.organization import Organization
from Models.Tenants.role import Role
from Models.models import (
    User,
    Employee,
    AcademicQualification,
    EmploymentHistory,
    EmergencyContact,
    NextOfKin,
    FileStorage,
    AuditLog
)
from Schemas.schemas import (
    OrganizationCreateSchema, OrganizationSchema,
    RoleCreateSchema, RoleSchema,
    UserCreateSchema, UserSchema,
    EmployeeCreateSchema, EmployeeSchema,
    AcademicQualificationCreateSchema, AcademicQualificationSchema,
    EmploymentHistoryCreateSchema,  EmploymentHistorySchema,
    NextOfKinCreateSchema,  NextOfKinSchema,
    FileStorageSchema, 
)
from Crud.user_base import UserCRUD as userbase
from Crud.async_base import CRUDBase as AsyncCRUDBase
# from Crud.base import CRUDBase


# ✅ Initialize UserCRUD instance
userbase = userbase(
    user_model=User,
    role_model=Role,
    org_model=Organization,
    employee_model=Employee,
    audit_model=AuditLog
)




router = APIRouter()



@router.post("/create", response_model=Dict, status_code=status.HTTP_201_CREATED)
async def create_user(
    
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    first_name: str = Form(...),
    middle_name: Optional[str] = Form(None),
    last_name: str = Form(...),
    title: Optional[str] = Form("Other"),
    gender: Optional[str] = Form("Other"),
    date_of_birth: date = Form(...),
    marital_status: Optional[str] = Form("Other"),
    email: EmailStr = Form(...),
    contact_info: Optional[str] = Form(json.dumps({})),
    hire_date: Optional[date] = Form(None),
    termination_date: Optional[date] = Form(None),
    organization_id: UUID = Form(...),
    role_id: UUID = Form(...),
    image_file: List[UploadFile] = File(...),
    custom_data: Optional[str] = Form(json.dumps({})),
    created_by: Optional[UUID] = Form(None),
):
    """
    Creates a user based on an existing employee record with bio authentication & secure image storage.
    """

    # 🔹 **Convert JSON string inputs to dictionaries safely**
    try:
        contact_info_dict = json.loads(contact_info) if contact_info else {}
        custom_data_dict = json.loads(custom_data) if custom_data else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in contact_info or custom_data")
    

    employee_data = {
        "first_name":first_name,
        "middle_name":middle_name,
        "last_name": last_name,
        "title": title,
        "gender": gender,
        "date_of_birth": date_of_birth,
        "marital_status": marital_status,
        "email": email,
        "contact_info": contact_info_dict,
        "hire_date": hire_date,
        "termination_date": termination_date,
        "custom_data": custom_data_dict,
        "organization_id": organization_id,
    
    }


    result = await userbase.create_user(
        background_tasks=background_tasks,db=db, employee_data=employee_data, 
        role_id=role_id, organization_id=organization_id, image_file=image_file, created_by=created_by)
    

    return result



@router.patch("/update/{user_id}", response_model=Dict)
async def update_user_api(
    user_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    role_id: Optional[UUID] = Form(None),
    image_file: Optional[UploadFile] = File(None)
):
    """
    API for updating user details dynamically.

    :param user_id: The UUID of the user to be updated.
    :param username: (Optional) New username.
    :param email: (Optional) New email.
    :param role_id: (Optional) New role ID.
    :param image_file: (Optional) New profile image file.
    :return: Dictionary containing success message.
    """
    print("\n\nlocals(): \n",locals())

    return await userbase.update_user(
        background_tasks,
        db,
        user_id,
        username,
        email,
        role_id,
        image_file
    )


@router.get("/get-user/{identifier}/{organization_id}", response_model=dict)
def read_user_data(identifier: str, organization_id: str, db: Session = Depends(get_db)):
    """
    Read a User by his/her Organization's Identifier

    Retrieve user by ID or email along with related employee data 
    using the email as a reference in the employees table.

    """
    
    return userbase.get(db, identifier, organization_id)




    