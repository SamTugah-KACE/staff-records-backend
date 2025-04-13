from datetime import date
import io
import json
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks, Query, Form, status
from pydantic import EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional, List, Dict
from uuid import UUID
from Utils.util import sanitize_row_data
from Utils.field_mapping import map_employee_fields, merge_contact_info_fields
from Models.dynamic_models import EmployeeDynamicData, BulkUploadError  # dynamic table for unmatched data
from database.db_session import get_db, get_async_db  # Dependency injection
from Models.Tenants.organization import Branch, Organization
from Models.Tenants.role import Role
from Models.models import *
from Schemas.schemas import (
    CreateUserResponseSchema,
    GetUserResponseSchema,
    OrganizationCreateSchema, OrganizationSchema,
    RoleCreateSchema, RoleSchema,
    UpdateUserResponseSchema,
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


ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "docx", "txt"}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

# Mapping from model names to expected field names (all lowercase)
model_field_map = {
    "employee": {"first_name", "middle_name", "last_name", "title", "gender", "date_of_birth", "marital_status", "email", "contact_info", "hire_date", "termination_date", "profile_image_path", "staff_id", "last_promotion_date", "employee_type_id", "department_id", "rank_id"},
    "academic_qualification": {"degree", "institution", "year_obtained", "details", "certificate_path"},
    "professional_qualification": {"qualification_name", "institution", "year_obtained", "details", "license_path"},
    "employment_history": {"job_title", "company", "start_date", "end_date", "details", "documents_path"},
    "emergency_contact": {"name", "relation", "phone", "address", "details"},
    "next_of_kin": {"name", "relation", "phone", "address", "details"},
    "salary_payment": {"amount", "currency", "payment_date", "payment_method", "transaction_id", "status", "approved_by"},
    "employee_payment_detail": {"payment_mode", "bank_name", "account_number", "mobile_money_provider", "wallet_number", "additional_info", "is_verified"},
    "employee_type": {"type_code", "description", "default_criteria"},
    "department": {"name", "department_head_id", "branch_id"}
}

# Mapping from model name to model class
model_classes = {
    "employee": Employee,
    "academic_qualification": AcademicQualification,
    "professional_qualification": ProfessionalQualification,
    "employment_history": EmploymentHistory,
    "emergency_contact": EmergencyContact,
    "next_of_kin": NextOfKin,
    "salary_payment": SalaryPayment,
    "employee_payment_detail": EmployeePaymentDetail,
    "employee_type": EmployeeType,
    "department": Department
}



# --------------------------
# Bulk Insert Endpoint API
# --------------------------
@router.post("/bulk_insert_employee_data_api")
async def bulk_insert_employee_data_api(
    background_tasks: BackgroundTasks,
    organization_id: str = Form(...),
    file: UploadFile = File(...),
    
    db: Session = Depends(get_db)  # Replace with your get_db dependency
):
    result = userbase.bulk_insert_crud(organization_id, file, background_tasks, db)
    return result

# @router.post("/create", response_model=CreateUserResponseSchema, status_code=status.HTTP_201_CREATED)
# async def create_new_user(
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db),
#     first_name: str = Form(...),
#     middle_name: Optional[str] = Form(None),
#     last_name: str = Form(...),
#     title: Optional[str] = Form("Other"),
#     gender: Optional[str] = Form("Other"),
#     date_of_birth: date = Form(...),
#     marital_status: Optional[str] = Form("Other"),
#     email: EmailStr = Form(...),
#     contact_info: Optional[str] = Form(json.dumps({})),
#     hire_date: Optional[date] = Form(None),
#     termination_date: Optional[date] = Form(None),
#     organization_id: str = Form(...),
#     role_id: str = Form(...),
#     image_file: UploadFile = File(...),
#     custom_data: Optional[str] = Form(json.dumps({})),
#     created_by: Optional[str] = Form(None),
#     ):
#     """
#     Creates a user based on an existing employee record with bio authentication & secure image storage.
#     """

#     # 🔹 **Convert JSON string inputs to dictionaries safely**
#     try:
#         contact_info_dict = json.loads(contact_info) if contact_info else {}
#         custom_data_dict = json.loads(custom_data) if custom_data else {}
#     except json.JSONDecodeError:
#         raise HTTPException(status_code=400, detail="Invalid JSON format in contact_info or custom_data")
    
#     # ✅ Convert UUID fields manually
#     try:
#         organization_idd = UUID(organization_id)
#         role_idd = UUID(role_id)
#         created_byy = UUID(created_by) if created_by else None
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Invalid UUID format")

#     employee_data = {
#         "first_name":first_name,
#         "middle_name":middle_name,
#         "last_name": last_name,
#         "title": title,
#         "gender": gender,
#         "date_of_birth": date_of_birth if date_of_birth else None,
#         "marital_status": marital_status if marital_status else None,
#         "email": email,
#         "contact_info": contact_info_dict,
#         "hire_date": hire_date if hire_date else None,
#         "termination_date": termination_date if termination_date else None,
#         "custom_data": custom_data_dict,
#         "organization_id": organization_idd,
    
#     }


#     result = await userbase.create_user(
#         background_tasks=background_tasks,db=db, employee_data=employee_data, 
#         role_id=role_idd, organization_id=organization_idd, image_file=image_file if image_file else None, created_by=created_byy)
    
#     print("result -- :", result)
#     # Ensure that result contains strings for any UUID fields.
#     result["id"] = str(result["id"])
#     return result




@router.post("/create", response_model=CreateUserResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_new_employee(
    background_tasks: BackgroundTasks,
    first_name: str = Form(...),
    middle_name: Optional[str] = Form(None),
    last_name: str = Form(...),
    title: Optional[str] = Form("Other"),
    gender: Optional[str] = Form("Other"),
    date_of_birth: date = Form(None),
    marital_status: Optional[str] = Form("Other"),
    email: str = Form(...),
    contact_info: Optional[str] = Form(json.dumps({})),
    hire_date: Optional[date] = Form(None),
    termination_date: Optional[date] = Form(None),
    organization_id: str = Form(...),
    role_id: str = Form(...),
    image_file: Optional[UploadFile] = File(None),
    custom_data: Optional[str] = Form(json.dumps({})),
    employee_type: Optional[str] = Form(None),
    rank: Optional[str] = Form(None),
    assigned_dept: Optional[str] = Form(None),
    # Managerial assignment key: inferred from Role permissions.
    Role: Optional[str] = Form(None),
    academic_qualifications: Optional[str] = Form(None),
    professional_qualifications: Optional[str] = Form(None),
    payment_details: Optional[str] = Form(None),
    next_of_kin: Optional[str] = Form(None),
    created_by: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Creates a new employee using dynamic data from the manager's registration form.
    
    The UI can send keys using synonyms (e.g., "first name", "sex") and extra related
    data (academic_qualifications, professional_qualifications, payment_details, next_of_kin).
    """
    # Merge extra related JSON data.
    extra_data = {}
    for key, error_msg in [
        ("academic_qualifications", "Invalid JSON for academic qualifications"),
        ("professional_qualifications", "Invalid JSON for professional qualifications"),
        ("payment_details", "Invalid JSON for payment details"),
        ("next_of_kin", "Invalid JSON for next of kin")
    ]:
        field_val = locals().get(key)
        if field_val:
            try:
                extra_data[key] = json.loads(field_val)
            except Exception:
                raise HTTPException(status_code=400, detail=error_msg)
    
    try:
        custom_data_dict = json.loads(custom_data) if custom_data else {}
    except Exception:
        custom_data_dict = {}
    custom_data_dict.update(extra_data)
    
    employee_data = {
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "title": title,
        "sex": gender,
        "date_of_birth": date_of_birth.isoformat() if date_of_birth else None,
        "marital_status": marital_status,
        "email": email,
        "contact": contact_info,  # Accept as-is: plain text or JSON string.
        "hire_date": hire_date.isoformat() if hire_date else None,
        "termination_date": termination_date.isoformat() if termination_date else None,
        "employee_type": employee_type,
        "rank": rank,
        "assigned_dept": assigned_dept,
        "Role": Role,  # For managerial assignment inference.
        "custom_data": json.dumps(custom_data_dict),
    }
    
    print("\n\nemployee_data: \n", employee_data)
    # Validate the image file if provided
    if image_file and not allowed_image_file(image_file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed types: .jpg, .jpeg, .gif, .png")
    
    try:
        org_id = UUID(organization_id)
        role_uuid = UUID(role_id)
        created_by_uuid = UUID(created_by) if created_by else None
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid UUID provided.")
    
    # Map UI keys using the mapping utility.
    mapped_data = map_employee_fields(employee_data)
    # Merge any contact info fields (e.g. phone, address) into the "contact_info" key.
    normalized_data = merge_contact_info_fields(mapped_data)

    result = await userbase.create_user(
        background_tasks=background_tasks,
        db=db,
        employee_data=employee_data,
        role_id=role_id,
        organization_id=organization_id,
        image_file=image_file,
        created_by=created_by,
    )
    return result




@router.patch("/update/{user_id}", response_model=UpdateUserResponseSchema)
async def update_user_api(
    user_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    role_id: Optional[str] = Form(None),
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

    try:
        user_uuid = UUID(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    role_uuid = None
    if role_id:
        try:
            role_uuid = UUID(role_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid role_id format")
    

    # Validate the image file if provided
    if image_file and not allowed_image_file(image_file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed types: .jpg, .jpeg, .gif, .png")
    
    result = await userbase.update_user(
        background_tasks,
        db,
        user_uuid,
        username,
        email,
        role_uuid,
        image_file
    )
    return result
    # return {
    #     "message": "User updated successfully",
        
    # }


@router.get("/get-user/{identifier}/{organization_id}", response_model=GetUserResponseSchema)
def read_user_data(identifier: str, organization_id: str, db: Session = Depends(get_db)):
    """
    Read a User by his/her Organization's Identifier

    Retrieve user by ID or email along with related employee data 
    using the email as a reference in the employees table.

    """
    data = userbase.get(db, identifier, organization_id)
     # Convert any UUID fields in the returned dict:
    data["user"]["user_id"] = str(data["user"]["user_id"])
    data["employee"]["id"] = str(data["employee"]["id"])
    data["organization"]["id"] = str(data["organization"]["id"])
    
    return data



# ====================================================================
# 2. Get Employees (get_multi) Endpoint
# ====================================================================
# @router.get("/employees", response_model=dict)
# def get_employees_by_organization_id(
#     organization_id: str,
#     skip: int = Query(0, ge=0),
#     limit: int = Query(100, gt=0),
#     sort: Optional[str] = Query("asc", regex="^(asc|desc)$"),
#     db: Session = Depends(get_db)
# ) -> Dict[str, Any]:
#     """
#     Fetch all staff for the given organization, including full related data.
#     The endpoint returns:
#       - Employee basic info (with dynamic custom_data, academic/professional details, etc.)
#       - Related department, branch, employee_type, and rank details.
#       - Aggregated summary data (total staff, counts by branch and department).
#       - Sorting options by username (asc or desc).
#     """
#     # Confirm the organization exists.
#     org = db.query(Organization).filter(Organization.id == organization_id).first()
#     if not org:
#         raise HTTPException(status_code=404, detail="Organization not found.")

#     # Pre-fetch branches if the organization is branch managed.
#     branches_dict = {}
#     if "branch" in org.nature.lower() or org.nature.lower() == "multi-branch":
#         branches = db.query(Branch).filter(Branch.organization_id == organization_id).all()
#         branches_dict = {str(branch.id): branch for branch in branches}

#     # Get all active users (the User model flag 'is_active' is enforced here).
#     # We assume the Employee record is linked to a User via email.
#     users = db.query(User).filter(User.organization_id == organization_id).all()
#     users_dict = {user.email: user for user in users}

#     # Query employees using pagination.
#     employees = (
#         db.query(Employee)
#         .filter(Employee.organization_id == organization_id)
#         .offset(skip)
#         .limit(limit)
#         .all()
#     )
    
#     result = []
#     total_staff = 0
#     branch_summary: Dict[str, int] = {}
#     department_summary: Dict[str, int] = {}

#     for idx, emp in enumerate(employees, start=1):
#         total_staff += 1

#         # Build department info.
#         dept = None
#         if emp.department:
#             dept = {
#                 "id": str(emp.department.id),
#                 "name": emp.department.name,
#                 "department_head_id": str(emp.department.department_head_id) if emp.department.department_head_id else None,
#                 "branch_id": str(emp.department.branch_id) if emp.department.branch_id else None
#             }
#             # If branch managed, attach branch details.
#             if dept["branch_id"] and dept["branch_id"] in branches_dict:
#                 branch_obj = branches_dict[dept["branch_id"]]
#                 dept["branch_name"] = branch_obj.name
#                 dept["branch_location"] = branch_obj.location
#                 branch_summary[branch_obj.name] = branch_summary.get(branch_obj.name, 0) + 1
#             department_summary[dept["name"]] = department_summary.get(dept["name"], 0) + 1

#         # Employment details: employee type, rank, branch.
#         employment_details = {
#             "employee_type": {
#                 "id": str(emp.employee_type.id) if emp.employee_type else None,
#                 "type_code": emp.employee_type.type_code if emp.employee_type else None,
#                 "description": emp.employee_type.description if emp.employee_type else None,
#                 "default_criteria": emp.employee_type.default_criteria if emp.employee_type else None,
#             },
#             "rank": {
#                 "id": str(emp.rank.id) if emp.rank else None,
#                 "name": emp.rank.name if emp.rank else None,
#             },
#             # "branch": None
#         }
#         # if hasattr(emp, "branch") and emp.branch:
#         #     employment_details["branch"] = {
#         #         "id": str(emp.branch.id),
#         #         "name": emp.branch.name,
#         #         "location": emp.branch.location
#         #     }
#         # elif dept and dept.get("branch_id") and dept["branch_id"] in branches_dict:
#         #     branch_obj = branches_dict[dept["branch_id"]]
#         #     employment_details["branch"] = {
#         #         "id": str(branch_obj.id),
#         #         "name": branch_obj.name,
#         #         "location": branch_obj.location
#         #     }

#         # Retrieve additional collections.
#         def serialize_collection(collection, fields: List[str]) -> List[Dict[str, Any]]:
#             return [
#                 {field: getattr(item, field) for field in fields if hasattr(item, field)}
#                 for item in collection
#             ]
#         academic_qualifications = serialize_collection(emp.academic_qualifications, ["id", "degree", "institution", "year_obtained", "details", "certificate_path"]) if hasattr(emp, "academic_qualifications") else []
#         professional_qualifications = serialize_collection(emp.professional_qualifications, ["id", "qualification_name", "institution", "year_obtained", "details", "license_path"]) if hasattr(emp, "professional_qualifications") else []
#         employment_history = serialize_collection(emp.employment_history, ["id", "job_title", "company", "start_date", "end_date", "details", "documents_path"]) if hasattr(emp, "employment_history") else []
#         emergency_contacts = serialize_collection(emp.emergency_contacts, ["id", "name", "relation", "phone", "address", "details"]) if hasattr(emp, "emergency_contacts") else []
#         next_of_kin = serialize_collection(emp.next_of_kins, ["id", "name", "relation", "phone", "address", "details"]) if hasattr(emp, "next_of_kins") else []
#         payment_details = serialize_collection(emp.payment_details, ["id", "payment_mode", "bank_name", "account_number", "mobile_money_provider", "wallet_number", "additional_info", "is_verified"]) if hasattr(emp, "payment_details") else []

#         # Determine employee account status from associated User record.
#         user_obj = users_dict.get(emp.email)
#         status = "Active" if user_obj and user_obj.is_active else "Inactive"

#         emp_data = {
#             f"employee-row-# {idx}": {
#                 "id": str(emp.id),
#                 "first_name": emp.first_name,
#                 "middle_name": emp.middle_name,
#                 "last_name": emp.last_name,
#                 "email": emp.email,
#                 "contact_info": emp.contact_info,
#                 "custom_data": emp.custom_data,
#                 "profile_image_path": emp.profile_image_path,
#                 "hire_date": str(emp.hire_date) if emp.hire_date else None,
#                 "termination_date": str(emp.termination_date) if emp.termination_date else None,
#                 "status": status,
#                 "academic_qualifications": academic_qualifications,
#                 "professional_qualifications": professional_qualifications,
#                 "employment_history": employment_history,
#                 "emergency_contacts": emergency_contacts,
#                 "next_of_kin": next_of_kin,
#                 "payment_details": payment_details,
#             },
#             "department": dept,
#             "employment_details": employment_details
#         }
#         result.append(emp_data)

#     # Prepare organization info and summary.
#     organization_info = {
#         "id": str(org.id),
#         "name": org.name,
#         "org_email": org.org_email,
#         "country": org.country,
#         "access_url": org.access_url,
#         "nature": org.nature,
#         "type": org.type
#     }
#     summary = {
#         "total_staff": total_staff,
#         "branch_summary": branch_summary,
#         "department_summary": department_summary,
#     }
#     # Sort the result by first name (alphabetical order) if specified.
#     result_sorted = sorted(result, key=lambda x: x.get(list(x.keys())[0]).get("first_name"), reverse=(sort=="desc"))
#     return {"organization": organization_info, "summary": summary, "employees": result_sorted, "skip": skip, "limit": limit}

#########
@router.get("/employees", response_model=dict)
def get_employees_by_organization_id(
    organization_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0),
    sort: Optional[str] = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Fetch all staff for the given organization, including full related data.
    This endpoint returns:
      - Employee basic info (with dynamic custom_data, academic/professional details, etc.)
      - Related department, branch, employee_type, and rank details.
      - Aggregated summary data (total staff, counts by branch and department).
      - Sorting options by first name (asc or desc).
      - Integrated user account role details (role id and role name).
    """
    # Verify the organization exists.
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")

    # Pre-fetch branches if the organization is branch managed.
    branches_dict = {}
    if "branch" in org.nature.lower() or org.nature.lower() == "multi-branch":
        branches = db.query(Branch).filter(Branch.organization_id == organization_id).all()
        branches_dict = {str(branch.id): branch for branch in branches}

    # Retrieve all active users for the organization and index by email.
    users = db.query(User).filter(
        User.organization_id == organization_id,
        User.is_active == True
    ).all()
    users_dict = {user.email: user for user in users}

    # Paginate employee records.
    employees = (
        db.query(Employee)
        .filter(Employee.organization_id == organization_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    total_staff = 0
    branch_summary = {}
    department_summary = {}

    def serialize_collection(collection, fields: List[str]) -> List[Dict[str, Any]]:
        """Helper function to serialize a collection of related objects."""
        return [
            {field: getattr(item, field) for field in fields if hasattr(item, field)}
            for item in collection
        ]

    # Process each employee record.
    for idx, emp in enumerate(employees, start=1):
        total_staff += 1

        # Serialize department information.
        dept = None
        if emp.department:
            dept = {
                "id": str(emp.department.id),
                "name": emp.department.name,
                "department_head_id": str(emp.department.department_head_id) if emp.department.department_head_id else None,
                "branch_id": str(emp.department.branch_id) if emp.department.branch_id else None
            }
            # Add branch details if applicable.
            if dept["branch_id"] and dept["branch_id"] in branches_dict:
                branch_obj = branches_dict[dept["branch_id"]]
                dept["branch_name"] = branch_obj.name
                dept["branch_location"] = branch_obj.location
                branch_summary[branch_obj.name] = branch_summary.get(branch_obj.name, 0) + 1
            department_summary[dept["name"]] = department_summary.get(dept["name"], 0) + 1

        # Serialize employment details.
        employment_details = {
            "employee_type": {
                "id": str(emp.employee_type.id) if emp.employee_type else None,
                "type_code": emp.employee_type.type_code if emp.employee_type else None,
                "description": emp.employee_type.description if emp.employee_type else None,
                "default_criteria": emp.employee_type.default_criteria if emp.employee_type else None,
            },
            "rank": {
                "id": str(emp.rank.id) if emp.rank else None,
                "name": emp.rank.name if emp.rank else None,
            }
        }

        # Serialize collections.
        academic_qualifications = serialize_collection(
            getattr(emp, "academic_qualifications", []),
            ["id", "degree", "institution", "year_obtained", "details", "certificate_path"]
        )
        professional_qualifications = serialize_collection(
            getattr(emp, "professional_qualifications", []),
            ["id", "qualification_name", "institution", "year_obtained", "details", "license_path"]
        )
        employment_history = serialize_collection(
            getattr(emp, "employment_history", []),
            ["id", "job_title", "company", "start_date", "end_date", "details", "documents_path"]
        )
        emergency_contacts = serialize_collection(
            getattr(emp, "emergency_contacts", []),
            ["id", "name", "relation", "phone", "address", "details"]
        )
        next_of_kin = serialize_collection(
            getattr(emp, "next_of_kins", []),
            ["id", "name", "relation", "phone", "address", "details"]
        )
        payment_details = serialize_collection(
            getattr(emp, "payment_details", []),
            ["id", "payment_mode", "bank_name", "account_number", "mobile_money_provider", "wallet_number", "additional_info", "is_verified"]
        )

        # Retrieve user record to determine account status and role.
        user_obj = users_dict.get(emp.email)
        account_status = "Active" if user_obj and user_obj.is_active else "Inactive"
        role_details = None
        if user_obj and user_obj.role:
            role_details = {
                "id": str(user_obj.role.id),
                "name": user_obj.role.name
            }

        # Build employee data structure.
        emp_data = {
            f"employee_row_{idx}": {
                "id": str(emp.id),
                "first_name": emp.first_name,
                "middle_name": emp.middle_name,
                "last_name": emp.last_name,
                "email": emp.email,
                "contact_info": emp.contact_info,
                "custom_data": emp.custom_data,
                "profile_image_path": emp.profile_image_path,
                "hire_date": str(emp.hire_date) if emp.hire_date else None,
                "termination_date": str(emp.termination_date) if emp.termination_date else None,
                "status": account_status,
                "role": role_details,
                "academic_qualifications": academic_qualifications,
                "professional_qualifications": professional_qualifications,
                "employment_history": employment_history,
                "emergency_contacts": emergency_contacts,
                "next_of_kin": next_of_kin,
                "payment_details": payment_details,
            },
            "department": dept,
            "employment_details": employment_details
        }
        result.append(emp_data)

    # Organize organization and summary data.
    organization_info = {
        "id": str(org.id),
        "name": org.name,
        "org_email": org.org_email,
        "country": org.country,
        "access_url": org.access_url,
        "nature": org.nature,
        "type": org.type
    }
    summary = {
        "total_staff": total_staff,
        "branch_summary": branch_summary,
        "department_summary": department_summary,
    }

    # Sort the results by first name.
    result_sorted = sorted(
        result,
        key=lambda x: list(x.values())[0].get("first_name"),
        reverse=(sort == "desc")
    )

    return {
        "organization": organization_info,
        "summary": summary,
        "employees": result_sorted,
        "skip": skip,
        "limit": limit
    }








############################3
# @router.get("/employees", response_model=dict)
# def get_employees_by_organization_id(
#     organization_id: str,
#     skip: int = Query(0, ge=0),
#     limit: int = Query(100, gt=0),
#     db: Session = Depends(get_db)
# ) -> Dict[str, Any]:
#     # Verify that the organization exists.
#     org = db.query(Organization).filter(Organization.id == organization_id).first()
#     if not org:
#         raise HTTPException(status_code=404, detail="Organization not found.")

    
#     users = db.query(User).filter(User.organization_id == organization_id).all()
#     users_dict = {str(user.email): user for user in users}


#     # Pre-fetch branches if organization is branch managed.
#     branches_dict = {}
#     if "branch" in org.nature.lower() or org.nature.lower() == "multi-branch":
#         branches = db.query(Branch).filter(Branch.organization_id == organization_id).all()
#         # Build a dict for quick branch lookup using branch id as key.
#         branches_dict = {str(branch.id): branch for branch in branches}

#     # Query employees for the given organization using pagination.
#     employees = (
#         db.query(Employee)
#         .filter(Employee.organization_id == organization_id)
#         .offset(skip)
#         .limit(limit)
#         .all()
#     )
    
#     result = []
#     total_staff = 0
#     branch_summary: Dict[str, int] = {}
#     department_summary: Dict[str, int] = {}

#     for idx, emp in enumerate(employees, start=1):
#         total_staff += 1

#         # Department details.
#         dept = None
#         if emp.department:
#             dept = {
#                 "id": str(emp.department.id),
#                 "name": emp.department.name,
#                 "department_head_id": str(emp.department.department_head_id) if emp.department.department_head_id else None,
#                 "branch_id": str(emp.department.branch_id) if emp.department.branch_id else None
#             }
#             # If the organization is branch managed, add branch details from the pre-fetched branches.
#             if dept["branch_id"] and dept["branch_id"] in branches_dict:
#                 branch_obj = branches_dict[dept["branch_id"]]
#                 dept["branch_name"] = branch_obj.name
#                 dept["branch_location"] = branch_obj.location
#                 # Increment branch count.
#                 branch_summary[branch_obj.name] = branch_summary.get(branch_obj.name, 0) + 1

#             # Increment department summary.
#             department_summary[dept["name"]] = department_summary.get(dept["name"], 0) + 1

#         # Employment details (employee type, rank, branch if available).
#         employment_details = {
#             "employee_type": {
#                 "id": str(emp.employee_type.id) if emp.employee_type else None,
#                 "name": emp.employee_type.type_code if emp.employee_type else None,
#                 "description": emp.employee_type.description if emp.employee_type else None,
#             },
#             "rank": {
#                 "id": str(emp.rank.id) if emp.rank else None,
#                 "name": emp.rank.name if emp.rank else None,
#             },
#             # "branch": None
#         }
#         # If Employee has a direct branch relationship or via department branch_id.
#         if hasattr(emp, "branch") and emp.branch:
#             employment_details["branch"] = {
#                 "id": str(emp.branch.id),
#                 "name": emp.branch.name,
#                 "location": emp.branch.location
#             }
#         elif dept and dept.get("branch_id") and dept["branch_id"] in branches_dict:
#             branch_obj = branches_dict[dept["branch_id"]]
#             # employment_details["branch"] = {
#             #     "id": str(branch_obj.id),
#             #     "name": branch_obj.name,
#             #     "location": branch_obj.location
#             # }

#         # Gather additional related collections.
#         academic_qualifications = [
#             {
#                 "id": str(aq.id),
#                 "degree": aq.degree,
#                 "institution": aq.institution,
#                 "year_obtained": aq.year_obtained,
#                 "details": aq.details,
#                 "certificate_path": aq.certificate_path
#             }
#             for aq in emp.academic_qualifications
#         ] if hasattr(emp, "academic_qualifications") else []

#         professional_qualifications = [
#             {
#                 "id": str(pq.id),
#                 "qualification_name": pq.qualification_name,
#                 "institution": pq.institution,
#                 "year_obtained": pq.year_obtained,
#                 "details": pq.details,
#                 "license_path": pq.license_path
#             }
#             for pq in emp.professional_qualifications
#         ] if hasattr(emp, "professional_qualifications") else []

#         employment_history = [
#             {
#                 "id": str(eh.id),
#                 "job_title": eh.job_title,
#                 "company": eh.company,
#                 "start_date": str(eh.start_date) if eh.start_date else None,
#                 "end_date": str(eh.end_date) if eh.end_date else None,
#                 "details": eh.details,
#                 "documents_path": eh.documents_path
#             }
#             for eh in emp.employment_history
#         ] if hasattr(emp, "employment_history") else []

#         emergency_contacts = [
#             {
#                 "id": str(ec.id),
#                 "name": ec.name,
#                 "relation": ec.relation,
#                 "phone": ec.phone,
#                 "address": ec.address,
#                 "details": ec.details
#             }
#             for ec in emp.emergency_contacts
#         ] if hasattr(emp, "emergency_contacts") else []

#         next_of_kin = [
#             {
#                 "id": str(nok.id),
#                 "name": nok.name,
#                 "relation": nok.relation,
#                 "phone": nok.phone,
#                 "address": nok.address,
#                 "details": nok.details
#             }
#             for nok in emp.next_of_kins
#         ] if hasattr(emp, "next_of_kins") else []

#         payment_details = [
#             {
#                 "id": str(pd.id),
#                 "payment_mode": pd.payment_mode,
#                 "bank_name": pd.bank_name,
#                 "account_number": pd.account_number,
#                 "mobile_money_provider": pd.mobile_money_provider,
#                 "wallet_number": pd.wallet_number,
#                 "additional_info": pd.additional_info,
#                 "is_verified": pd.is_verified,
#             }
#             for pd in emp.payment_details
#         ] if hasattr(emp, "payment_details") else []

#         # Mark status based on associated User record (assumed one-to-one via relationship "user").
#         user_obj = users_dict[emp.email] if emp.email in users_dict else None
#         if user_obj:
#             status = "Active" if user_obj.is_active else "Inactive"
#         else:
#             status = None

#         emp_data = {
#             f"employee-row-# {idx}": {
#                 "id": str(emp.id),
#                 "first_name": emp.first_name,
#                 "middle_name": emp.middle_name,
#                 "last_name": emp.last_name,
#                 "email": emp.email,
#                 "contact_info": emp.contact_info,
#                 "custom_data": emp.custom_data,
#                 "profile_image_path": emp.profile_image_path,
#                 "hire_date": str(emp.hire_date) if emp.hire_date else None,
#                 "termination_date": str(emp.termination_date) if emp.termination_date else None,
#                 "status": status,
#                 "academic_qualifications": academic_qualifications,
#                 "professional_qualifications": professional_qualifications,
#                 "employment_history": employment_history,
#                 "emergency_contacts": emergency_contacts,
#                 "next_of_kin": next_of_kin,
#                 "payment_details": payment_details,
#             },
#             "department": dept,
#             "employment_details": employment_details,
            
#         }
#         result.append(emp_data)

#     organization= {
#                 "id": str(org.id),
#                 "name": org.name,
#                 "org_email": org.org_email,
#                 "country": org.country,
#                 "access_url": org.access_url,
#                 "nature": org.nature,
#                 "type": org.type
#             }
    
#     summary = {
#         "total_staff": total_staff,
#         "branch_summary": branch_summary,
#         "department_summary": department_summary,
#     }
#     return { "organization":organization, "summary": summary,  "employees": result, "skip": skip, "limit": limit }

    