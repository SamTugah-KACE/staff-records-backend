from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from fastapi import FastAPI, APIRouter, Depends, HTTPException, BackgroundTasks, Query, Request, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID 
from typing import List, Optional
from database.db_session import get_db  # Your database session dependency
from Crud.crud import CRUDBase  # Generic CRUD class
from Crud.branch import *
from Crud.department import *
from Models.Tenants.organization import *  # Import your models
from Models.Tenants.role import Role  # Import your models
from Models.models import ( User,  Employee, AcademicQualification,
                        ProfessionalQualification, EmploymentHistory,
                        EmergencyContact, NextOfKin, FileStorage, AuditLog,
                        SystemSetting, Dashboard, Department)  # Import your models
from Schemas.schemas import (OrganizationCreateSchema, OrganizationSchema,
                             BranchCreate, BranchOut, BranchUpdate,
                             DepartmentCreate, DepartmentUpdate, DepartmentOut,

                            
                            RoleCreateSchema,
                         RoleSchema, UserCreateSchema, UserSchema, TenancyCreateSchema,
                         TenancySchema, TermsAndConditionsSchema, BillSchema,
                         PaymentSchema, EmployeeCreateSchema, EmployeeSchema,
                         AcademicQualificationCreateSchema, AcademicQualificationSchema,
                         ProfessionalQualificationCreateSchema, ProfessionalQualificationSchema,
                         EmploymentHistoryCreateSchema, EmploymentHistorySchema,
                         EmergencyContactCreateSchema, EmergencyContactSchema,
                         NextOfKinCreateSchema, NextOfKinSchema, FileStorageSchema,
                         AuditLogSchema, SystemSettingSchema, DashboardSchema)

from Utils.util import   get_create_user_url, get_organization_acronym  # Import your utility classes
import json
from Service.gcs_service import GoogleCloudStorage
from Utils.config import DevelopmentConfig, get_config
from Service.service import upload_to_google_cloud
import logging
from Service.file_service import upload_file
from Utils.file_handler import get_gcs_client
from Utils.serialize_4_json import serialize_for_json



# Create the FastAPI app
app = APIRouter()

config = DevelopmentConfig()  # Load the development configuration

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


current_date = date.today()
next_year = current_date + relativedelta(years=5)

# Instantiate generic CRUD classes
organization_crud = CRUDBase(Organization)
role_crud = CRUDBase(Role)
user_crud = CRUDBase(User)
tenancy_crud = CRUDBase(Tenancy)
employee_crud = CRUDBase(Employee)
academic_qualification_crud = CRUDBase(AcademicQualification)
professional_qualification_crud = CRUDBase(ProfessionalQualification)
employment_history_crud = CRUDBase(EmploymentHistory)
emergency_contact_crud = CRUDBase(EmergencyContact)
next_of_kin_crud = CRUDBase(NextOfKin)
system_setting_crud = CRUDBase(SystemSetting)





@app.get("/slug/{slug}")
def get_org_by_slug(slug: str, db: Session = Depends(get_db)):
    # Here we assume that access_url is stored as "https://gi-kace-solutions.onrender.com/{slug}"
    # One option is to filter using a LIKE condition:
    org = db.query(Organization).filter(Organization.access_url.ilike(f"%/{slug}")).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@app.get("/create-url", summary="Fetch create user submit button request API URL")
async def get_user_create_url(request: Request):
    """
    Returns the backend host URL with '/api/users/create' appended.
    """
    url = get_create_user_url(request)
    return {"user_create_url": url}


@app.post("/create-form/",  response_model=OrganizationSchema, status_code=status.HTTP_201_CREATED)
async def create_organization_form(
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    organizational_email: str = Form(...),
    country: str = Form(...),
    type: str = Form(...),
    nature: str = Form(...),
    employee_range: str = Form(...),
    subscription_plan: Optional[str] = Form("Basic"),
    logos: Optional[List[UploadFile]] = File(None),  # Organization logos
    user_images: Optional[List[UploadFile]] = File(None),  # User profile images
    tenancies: Optional[str] = Form(json.dumps([
            # {
            #     "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            #     "start_date": "2025-01-01",
            #     "billing_cycle": "Monthly",
            #     "terms_and_conditions_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            #     "terms_and_conditions": [
            #         {
            #             "title": "Default Terms",
            #             "content": {"agreement": "Sample agreement text"},
            #             "version": "1.0",
            #             "is_active": True
            #         }
            #     ]
            # }
        ])),  # JSON string for tenancies
    roles: Optional[str] = File(json.dumps([
    #     {
    #   "name": "Administrator",
    #   "permissions": {"read": "all", "write": "all", "delete": "all"},
    #   "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    # },
    # {
    #     "name": "HR", 
    #     "permissions": {"admin": False, "Deputy":True, "read": "all", "write": "all", "delete": "all"},
    #     "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6" 
    #     },
    # {
    #     "name": "User", 
    #     "permissions": {"admin": False, "Deputy": False, "read": "all", "write": "null", "delete": "soft delete"},
    #     "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6" 
    #     },
    ])),  # JSON string for roles
    employees: Optional[str] = Form(json.dumps([
    #     {
    #     "title": "Mr",
    #     "first_name": "Sam",
    #     "middle_name":"Kwaku",
    #     "last_name": "Badu",
    #     "date_of_birth": "1980-01-01",
    #     "email": "vboat54@gmail.com",
    #     "contact_info": {},
    #     "hire_date": str(current_date),
    #     "termination_date": str(next_year),
    #     "custom_data": {
    #         "has_previous_name": True,
    #         "previous_name": "Sam Kwaku Boateng",
    #         "Nationality": "Ghanaian",
    #         "National_ID": "GHA123456789",
    #     },
    #     "staff_id": "1234567890",
    #     "profile_image_path": "google.com/sam",
    #     "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    # },
    # {
    #     "title": "Mrs",
    #     "first_name": "Mary",
    #     "middle_name":"",
    #     "last_name": "Adwubi",
    #     "date_of_birth": "1980-01-01",
    #     "email": "mary@example.com",
    #     "contact_info": {},
    #     "hire_date": str(current_date),
    #     "termination_date": str(next_year),
    #     "custom_data": {
    #         "has_previous_name": False,
    #         "previous_name": "",
    #         "Nationality": "Ghanaian",
    #         "National_ID": "GHA987654321",
    #     },
    #     "profile_image_path": "google.com/mary",
    #     "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    # }
    
    ])),
    users: Optional[str] = Form(json.dumps([
                # {
                #     "username": "",
                #     "email": "vboat54@gmail.com",   
                #     "hashed_password": "",
                #     "role_id": "123e4567-e89b-12d3-a456-426614174000",
                #     "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", 
                #     "image_path": "google.com/sam"
                    
                # },
                # {
                #      "username": "",
                #     "email": "mary@example.com",   
                #     "hashed_password": "",
                #     "role_id": "123e4567-e89b-12d3-a456-426614174000",
                #     "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", 
                #     "image_path": "google.com/mary"

                # }

            ])),  # JSON string for users
    settings: Optional[str] = Form(json.dumps([
        # {
        #     "setting_name": "dashboard_theme",
        #     "setting_value": {         "color": "blue",         "font_size": "12px"       } ,
        #     "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        # }
        ])),  # JSON string for settings
    db: Session = Depends(get_db),
        # email_smtp_config: dict = Depends(get_smtp_config),
    config: DevelopmentConfig = Depends(get_config),  # Inject config
    ):
    

    try:
        bucket_name = config.BUCKET_NAME

        # Parse JSON strings for nested fields
        tenancies_data = json.loads(tenancies) if tenancies else []
        roles_data = json.loads(roles) if roles else []
        employee_data = json.loads(employees) if employees else []
        users_data = json.loads(users) if users else []
        settings_data = json.loads(settings) if settings else []

       

         # Validate parsed JSON data
        for field_name, field_value in {
            "tenancies": tenancies_data,
            "roles": roles_data,
            "employees": employee_data,
            "users": users_data,
            "settings": settings_data,
        }.items():
            if not isinstance(field_value, list):
                raise HTTPException(status_code=400, detail=f"Invalid JSON format for '{field_name}'")

        # Initialize Google Cloud Storage
        gcs_client = GoogleCloudStorage(bucket_name)

       
        logo_urls={}
        # Process uploaded files for logos
        if logos:
            logo_files = [{"filename": file.filename, "content": await file.read()} for file in logos]
          
            logo_urls = gcs_client.upload_to_gcs(files=logo_files, folder=f"organizations/{get_organization_acronym(name)}/logos") or {}
          

        # Process uploaded files for user profile images
        image_urls={}
        if user_images:
            if len(user_images) != len(users_data):
                raise HTTPException(
                    status_code=400,
                    detail="The number of user images does not match the number of users."
                )

            user_files = [{"filename": file.filename, "content": await file.read()} for file in user_images]
            image_urls = gcs_client.upload_to_gcs(files=user_files, folder=f"organizations/{get_organization_acronym(name)}/user_profiles") or {}

             # Attach image paths to users
            for i, user in enumerate(users_data):
                user["image_path"] = image_urls.get(user_files[i]["filename"], "https://example.com/default-profile-image.png")

            #Attach image paths to employees
            for i, employee in enumerate(employee_data):
                employee["profile_image_path"] = image_urls.get(user_files[i]["filename"],  "https://example.com/default-profile-image.png")
       
       # Fallback for Default logos and images
        logo_urls = logo_urls or {
            "primary": "https://example.com/default-logo-primary.png",
            "secondary": "https://example.com/default-logo-secondary.png",
        }

        # Fallback for default image paths if upload_to_gcs returned empty
        for user in users_data:
            user.setdefault("image_path", "https://example.com/default-profile-image.png")
        
        for employee in employee_data:
            employee.setdefault("profile_image_path", "https://example.com/default-profile-image.png")


        # Prepare organization schema
        organization_data = OrganizationCreateSchema(
            name=name,
            org_email=organizational_email,
            country=country,
            type=type,
            nature=nature,
            employee_range=employee_range,
            access_url="",
            subscription_plan=subscription_plan,
            image_path=image_urls,
            logos=logo_urls,  # Placeholder for logos URLs
            tenancies=tenancies_data,
            roles=roles_data, 
            employees=employee_data,
            users=users_data,
            settings=settings_data,
        )

        
            
        # Call the CRUD function
        organization = await organization_crud.create_with_nested(
            background_tasks, db, obj_in=organization_data
        )


        return organization
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON format in 'users' or 'tenancies'")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")



# @app.post("/new/", response_model=OrganizationSchema, status_code=status.HTTP_201_CREATED)
# async def create_organization_endpoint(
#     background_tasks: BackgroundTasks,
#     organization: OrganizationCreateSchema,
#     db: Session = Depends(get_db),
    
# ):
#     """
#     Endpoint to create a new organization.
#     """
#     return await organization_crud.create_with_nested(background_tasks,db, obj_in=organization)




@app.get("/fetch/{organization_id}", response_model=OrganizationSchema)
def read_organization(organization_id: UUID, db: Session = Depends(get_db)):
    """
    Read an organization by ID
    """
    org = organization_crud.get(db, id=organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrganizationSchema.model_validate(org)


@app.get("/batch/", response_model=List[OrganizationSchema])
def read_organizations(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """
    List all organizations
    """
    return organization_crud.get_multi(db, skip=skip, limit=limit)



######original
@app.patch("/v2/upd/{organization_id}", response_model=OrganizationSchema)
async def update_organization(
    organization_id: UUID,
    organization_update: Optional[str] = Form(...),  # Accept JSON string for updates
    logos: Optional[List[UploadFile]] = File(None),  # Upload files for logos
    user_images: Optional[List[UploadFile]] = File(None),  # Upload files for user profile images
    db: Session = Depends(get_db),
):
    """
    Update an organization by ID with support for partial updates, nested updates, and file uploads.
    """
    try:
        # Fetch the organization
        org = db.query(Organization).filter(Organization.id == organization_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Parse the update payload
        if organization_update:
            try:
                organization_data = json.loads(organization_update)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail="Invalid JSON format for organization_update") from e
        else:
            organization_data = {}

        # Inject organization_id into payload for nested models
        organization_data["organization_id"] = str(organization_id)

        # Initialize Google Cloud Storage (or your storage provider)
        gcs_client = GoogleCloudStorage(config.BUCKET_NAME)

        # Process uploaded logos if provided
        if logos:
            logo_files = [{"filename": file.filename, "content": await file.read()} for file in logos]
            uploaded_logo_urls = gcs_client.upload_to_gcs(
                files=logo_files,
                folder=f"organizations/{get_organization_acronym(org.name)}/logos"
            )
            # organization_data["logos"] = {
            #     file.filename: url for file, url in zip(logos, uploaded_logo_urls)
            # }
            organization_data["logos"] =uploaded_logo_urls
        else:
            # Maintain existing data if logos are not provided
            organization_data.pop("logos", None)
        

        # logo_urls={}
        # # Process uploaded files for logos
        # if logos:
        #     logo_files = [{"filename": file.filename, "content": await file.read()} for file in logos]
          
        #     logo_urls = gcs_client.upload_to_gcs(files=logo_files, folder=f"organizations/{get_organization_acronym(name)}/logos") or {}
          

        # Process uploaded user images if provided
        if user_images:
            user_files = [{"filename": file.filename, "content": await file.read()} for file in user_images]
            uploaded_image_urls = gcs_client.upload_to_gcs(
                files=user_files,
                folder=f"organizations/{get_organization_acronym(org.name)}/user_profiles"
            )
            uploaded_image_urls_list = list(uploaded_image_urls.values())
            for i, user in enumerate(organization_data.get("users", [])):
                if i < len(uploaded_image_urls_list):
                    user["image_path"] = uploaded_image_urls_list[i]
        else:
            # Ensure user image paths are not overwritten if no new images are provided
            for user in organization_data.get("users", []):
                user.pop("image_path", None)

        # Perform the update using the `update_with_nested` function
        updated_organization = organization_crud.update_with_nested(
            db=db,
            db_obj=org,
            obj_in=organization_data  # Pass the dynamic dictionary
        )

        return updated_organization

    except HTTPException as e:
        logger.error(f"HTTP exception during update: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("Unexpected error during update_organization.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")



@app.delete("/v2/delete/{id}", response_model=None)
def delete_record(
    id: UUID,
    confirm: bool = Query(False, description="Confirm cascading deletion of related records."),
    db: Session = Depends(get_db),
):
    """
    Deletes a record and its related references.

    - If the record has related references, pass `confirm=True` to cascade delete.
    - Returns 404 if the record is not found.
    - Returns 400 if there are related references and `confirm` is not set to `True`.
    """
    try:
        organization_crud.delete_with_references(db=db, id=id, confirm=confirm)
        return {"detail": f"Record with ID {id} successfully deleted."}
    except HTTPException as e:
        logger.error(f"HTTP exception during deletion: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("Unexpected error during record deletion.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")



#Branches
@app.post("/{org_id}/branches", response_model=BranchOut)
def create_organization_branch(org_id: uuid.UUID, branch_in: BranchCreate, db: Session = Depends(get_db)):
    branch = create_branch(db, branch_in, organization_id=org_id)
    return branch

@app.get("/{org_id}/branches", response_model=list[BranchOut])
def list_organization_branches(org_id: uuid.UUID, db: Session = Depends(get_db), skip: int = 0, limit: int = 10):
    return get_branches(db, organization_id=org_id, skip=skip, limit=limit)

@app.get("/{org_id}/branches/{branch_id}", response_model=BranchOut)
def get_branch_endpoint(org_id: uuid.UUID, branch_id: uuid.UUID, db: Session = Depends(get_db)):
    branch = get_branch(db, branch_id)
    if not branch or branch.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch

@app.patch("/{org_id}/branches/{branch_id}", response_model=BranchOut)
def update_branch_endpoint(org_id: uuid.UUID, branch_id: uuid.UUID, branch_in: BranchUpdate, db: Session = Depends(get_db)):
    branch = get_branch(db, branch_id)
    if not branch or branch.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Branch not found")
    data = update_branch(db, branch, branch_in)
    return data

@app.delete("/{org_id}/branches/{branch_id}")
def delete_branch_endpoint(org_id: uuid.UUID, branch_id: uuid.UUID, db: Session = Depends(get_db)):
    branch = get_branch(db, branch_id)
    if not branch or branch.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Branch not found")
    delete_branch(db, branch)
    return {"detail": "Branch deleted successfully"}




# @app.put("/upd/{organization_id}", response_model=OrganizationSchema)
# def update_organization(
#     organization_id: UUID,
#     organization_update: OrganizationCreateSchema,
#     logo: Optional[UploadFile] = File(None),
#     db: Session = Depends(get_db),
# ):
#     """
#     Update an organization by ID and handle nested updates.
#     """
#     org = organization_crud.get(db, id=organization_id)
#     if not org:
#         raise HTTPException(status_code=404, detail="Organization not found")

#     update_data = organization_update.dict(exclude_unset=True)
#     if logo:
#         update_data["logos"] = logo

    
#     return organization_crud.update_with_nested(db, db_obj=org, obj_in=update_data)




# @app.put("/v2/upd/{organization_id}", response_model=OrganizationSchema)
# async def update_organization(
#     organization_id: UUID,
#     organization_update: Optional[str] = Form(...),  # Accept JSON string for updates
#     logos: Optional[List[UploadFile]] = File(None),  # Upload files for logos
#     user_images: Optional[List[UploadFile]] = File(None),  # Upload files for user profile images
#     db: Session = Depends(get_db),
# ):
#     try:
#         org = db.query(Organization).filter(Organization.id == organization_id).first()
#         if not org:
#             raise HTTPException(status_code=404, detail="Organization not found")

#         if organization_update:
#             try:
#                 organization_data = json.loads(organization_update)
#             except json.JSONDecodeError as e:
#                 raise HTTPException(status_code=400, detail="Invalid JSON format for organization_update") from e
#         else:
#             organization_data = {}

#         config = DevelopmentConfig()
#         bucket_name = config.BUCKET_NAME
#         gcs_client = GoogleCloudStorage(bucket_name)

#         if logos:
#             logo_files = [{"filename": file.filename, "content": await file.read()} for file in logos]
#             uploaded_logo_urls = gcs_client.upload_to_gcs(
#                 files=logo_files,
#                 folder=f"organizations/{org.name}/logos"
#             )
#             organization_data["logos"] = serialize_for_json({
#                 file.filename: url for file, url in zip(logos, uploaded_logo_urls)
#             })
        

#         # Process uploaded user images
#         if user_images:
#             user_files = [{"filename": file.filename, "content": await file.read()} for file in user_images]
#             uploaded_image_urls = gcs_client.upload_to_gcs(
#                 files=user_files,
#                 folder=f"organizations/{org.name}/user_profiles"
#             )
#             uploaded_image_urls_list = list(uploaded_image_urls.values())
#             for i, user in enumerate(organization_data.get("users", [])):
#                 if i < len(uploaded_image_urls_list):
#                     user["image_path"] = uploaded_image_urls_list[i]

#           # Perform the update using the `update_with_nested` function
#         updated_organization = organization_crud.update_with_nested(
#             db=db,
#             db_obj=org,
#             obj_in=organization_data
#         )
#         return updated_organization

#     except HTTPException as e:
#         logger.error(f"HTTP exception during update: {e.detail}")
#         raise e
#     except Exception as e:
#         logger.exception("Unexpected error during update_organization.")
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")










