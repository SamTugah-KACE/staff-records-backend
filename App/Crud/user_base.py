import asyncio
import json
from fastapi import HTTPException, Depends, BackgroundTasks, UploadFile
from fastapi.responses import FileResponse
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing import Optional, Dict, List
from uuid import UUID
from passlib.context import CryptContext
import secrets
from pydantic import EmailStr
from smtplib import SMTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import logging
from jinja2 import Template
import pandas as pd
import io

import urllib.parse

from Models.Tenants.organization import Organization

from Models.models import Employee, User
from Utils.rate_limiter import RateLimiter
from Schemas.schemas import OrganizationCreateSchema, EmployeeCreateSchema
from Models.Tenants.role import Role
import os
from datetime import datetime
import re
from Crud.adv import RoleCache
from Utils.util import Validator
from Utils.config import DevelopmentConfig
from Utils.security import Security
import aiohttp
from Service.gcs_service import GoogleCloudStorage
from Service.email_service import EmailService, get_email_template
from aiohttp import ClientTimeout, FormData



rate_limiter = RateLimiter(max_attempts=5, period=60)  # 5 attempts per 60 seconds

settings = DevelopmentConfig()



# from fastapi import HTTPException, UploadFile, BackgroundTasks
# from sqlalchemy.orm import Session
# from uuid import UUID
# from typing import Optional, Dict
# import json
# import requests
# import aiohttp

# from utils.security import generate_random_string, hash_password
# from utils.cloud_storage import GoogleCloudStorage
# from utils.email_service import EmailService
# from models import User, Employee, Role
# from settings import FACIAL_AUTH_API_URL, BUCKET_NAME



# Configure Logger
# LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Secure Email Configuration
SMTP_CREDENTIALS = {
    "sender_email": os.getenv("SMTP_SENDER_EMAIL"),
    "sender_password": os.getenv("SMTP_SENDER_PASSWORD"),
    "smtp_host": os.getenv("SMTP_HOST"),
    "smtp_port": int(os.getenv("SMTP_PORT", 587)),
}



# Default Permissions for Roles
DEFAULT_PERMISSIONS = {
    "staff": {"create_task": True, "view_task": True, "update_task": False, "delete_task": False},
    "manager": {"create_task": True, "view_task": True, "update_task": True, "delete_task": False},
}

# Constants for Random Username and Password Generation
CHARACTER_SET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
USERNAME_LENGTH = 8
PASSWORD_LENGTH = 12

# Helper function to generate random string
def generate_random_string(length: int) -> str:
    return ''.join(secrets.choice(CHARACTER_SET) for _ in range(length))


# Audit Logging
async def log_audit(db: AsyncSession, audit_model, action: str, performed_by: UUID, table_name: str, record_id: Optional[UUID]):
    """
    Logs an audit entry in the database.
    """
    audit_entry = audit_model(
        action=action,
        performed_by=performed_by,
        table_name=table_name,
        record_id=record_id,
    )
    db.add(audit_entry)
    await db.commit()



# Email Sending with BackgroundTasks and Retry Logic
def send_email(to_email: str, subject: str, body: str, background_tasks: BackgroundTasks):
    def email_task():
        for attempt in range(3):
            try:
                sender_email = "your_email@example.com"  # Replace with your email
                sender_password = "your_email_password"  # Replace with your email password

                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = to_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'html'))

                with smtplib.SMTP('smtp.example.com', 587) as server:  # Replace with your SMTP server and port
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.send_message(msg)

                logger.info(f"Email sent to {to_email}")
                return
            except SMTPException as e:
                logger.error(f"Attempt {attempt + 1}: Failed to send email to {to_email}: {str(e)}")
                if attempt == 2:
                    raise HTTPException(status_code=500, detail=f"Failed to send email after 3 attempts: {str(e)}")

    background_tasks.add_task(email_task)


# Email Sending with AsyncExecutor
async def send_email_async(to_email: str, subject: str, body: str, db: AsyncSession, audit_model, performed_by: UUID):
    for attempt in range(3):
        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_CREDENTIALS["sender_email"]
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP(SMTP_CREDENTIALS["smtp_host"], SMTP_CREDENTIALS["smtp_port"]) as server:
                server.starttls()
                server.login(SMTP_CREDENTIALS["sender_email"], SMTP_CREDENTIALS["sender_password"])
                server.send_message(msg)

            logger.info(f"Email sent to {to_email}")
            # Log audit for email success
            await log_audit(db, audit_model, "email_sent", performed_by, "emails", None)
            return
        except smtplib.SMTPException as e:
            logger.error(f"Email attempt {attempt + 1} to {to_email} failed: {str(e)}")
            if attempt == 2:
                # Log audit for email failure
                await log_audit(db, audit_model, "email_failed", performed_by, "emails", None)
                raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

# Permissions Retrieval from Database
def get_permissions_from_db(db: AsyncSession, role_name: str) -> Dict[str, bool]:
    """
    Fetch role permissions dynamically from the database.
    """
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role {role_name} not found.")
    return role.permissions



# Validation for Uploaded File
def validate_file_structure(data: pd.DataFrame, required_columns: List[str]):
    for column in required_columns:
        if column not in data.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required column: {column}"
            )


# # Email Validation
# def is_valid_email(email: str) -> bool:
#     return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

# # DOB Validation
# def is_valid_dob(dob: datetime) -> bool:
#     today = datetime.today()
#     return dob < today and (today.year - dob.year) <= 120

# CRUD Functions for User Creation
class UserCRUD:
    def __init__(self, user_model, role_model, org_model, employee_model, audit_model):
        self.user_model = user_model
        self.role_model = role_model
        self.org_model = org_model
        self.employee_model = employee_model
        self.audit_model = audit_model
        self.role_cache = RoleCache()

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    async def log_audit(
        self,
        db: AsyncSession,
        action: str,
        performed_by: Optional[UUID],
        table_name: str,
        record_id: Optional[UUID],
    ):
        audit_entry = self.audit_model(
            action=action,
            performed_by=performed_by,
            table_name=table_name,
            record_id=record_id,
        )
        db.add(audit_entry)
        await db.commit()  if not None else db.commit()
    
    def extract_url(self, data_str):

        # Given string
        # data_str = '{"download (4).jpeg": "https://storage.googleapis.com/developers-bucket/test-app/organizations/Ghana-India Kofi Annan Centre of Excellence in ICT/user_profiles/download (4).jpeg"}'

        # Regular expression to find a URL
        # match = re.search(r'https?://[^\s"}]+', data_str)

        try:
            # Regular expression to match a complete URL inside quotes
            match = re.search(r'https?://.*?(?=["}])', data_str)

            # Extract URL if found
            url = match.group(0) if match else None

            print(url)
            return url
        except Exception as e:
            print("url extraction error: ", e)


    def get(
        self, db: Session, identifier: str, organization_id: str
    ):
        """
        Retrieve a single record by its ID.

        :param db: Database session
        :param id: Record ID
        :return: Single record or None
        """
        try:

              # Attempt to convert the identifier to a UUID.
            try:
                user_uuid = UUID(identifier)
                is_uuid = True
            except ValueError:
                is_uuid = False
            
            # Query user by ID or Email
            if is_uuid:
                user = db.query(User).filter(
                    (User.id == user_uuid) | (User.email == identifier),
                    User.organization_id == organization_id
                ).first()
            else:
                user = db.query(User).filter(
                (User.email == identifier),
                User.organization_id == organization_id
            ).first()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Query related employee using user's email
            employee = db.query(Employee).filter(
                Employee.email == user.email,
                Employee.organization_id == organization_id
            ).first()

            #role data
            role = db.query(Role).filter(
                Role.id==user.role_id,
                Role.organization_id == user.organization_id
            ).first()

            org = db.query(Organization).filter(
                Organization.id== user.organization_id
            ).first()

            print("profile_iamge_path: ", employee.profile_image_path)
            if employee.profile_image_path:
                if isinstance(employee.profile_image_path, dict):
                    print("herer")
                    indx = self.extract_url(employee.profile_image_path)
                    gcs = GoogleCloudStorage(bucket_name=settings.BUCKET_NAME)
                    decoded_file_path = urllib.parse.unquote(indx)
                    image = gcs.download_from_gcs(decoded_file_path, show_image=True)
                else:
                    indx = self.extract_url({employee.profile_image_path})
                    print("her: ", indx)
                    try:
                        gcs = GoogleCloudStorage(bucket_name=settings.BUCKET_NAME)
                        decoded_file_path = urllib.parse.unquote(indx)
                        image = gcs.download_from_gcs(decoded_file_path, show_image=True)
                    except Exception as r:
                        print("err: ", r)

            elif not employee.profile_image_path.strip():
                indx = "https://"


            print(f""" 
                    username email: {user.email}
                    "role": {role.name}
                    employee email: {employee.email}\n=======================================================================\n
                    profile image: {indx}
                    organization: {org.name}
                 """)

            data =  {
                "user": {
                    "user_id": user.id,
                    "Role":role.name,
                    "Permissions": role.permissions 
                    # "id": user.id,
                    # "email": user.email,
                    # "organization_id": user.organization_id,
                    # Add other user fields if needed
                },
                "employee": {
                    "id":employee.id,
                    "title": employee.title,
                    "first_name": employee.first_name,
                    "middle_name": employee.middle_name,
                    "last_name":employee.last_name,
                    "gender":employee.gender,
                    "email": employee.email if employee else None,
                    "organization": org.name,
                    "contact_info": employee.contact_info,
                    "custom_data": employee.custom_data,
                    "profile_image": "" if not indx else indx
                    # Add other employee fields if needed
                }, 
                # "image": image
            }

            return data
            # return image
            # return  {
                # "data": data,
            # return    FileResponse(image, media_type="image/jpeg", filename=os.path.basename(indx)) 

            # }

        except Exception as e:
            print("error occurred",e)
            raise HTTPException(status_code=500, detail=f"error occurred with message:\n {str(e)}")

    
    def enroll_user_for_facial_auth(self, username: str, image: UploadFile):
        """
        Send the user image directly to the facial authentication API.
        """
        try:
            response = requests.post(
                f"{settings.FACIAL_AUTH_API_URL}/users/create",
                data={"username": username},
                files={"file": (image.filename, image.file.read())},
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Facial authentication enrollment failed: {str(e)}")
    

    async def create_user(
            self,
        background_tasks: BackgroundTasks,
        db: Session,
        employee_data: dict,
        role_id: UUID,
        organization_id: UUID,
        image_file: List[UploadFile],
        created_by: Optional[UUID] = None,
    ) -> Dict[str, str]:
        """
        Creates a user based on an existing employee record with bio authentication & secure image storage.
        """

        # Step 0: **Check if Organization Exists**
        org = db.query(Organization).filter(Organization.id == organization_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Can't Sign Up User under unknown Organization.")


        # Step 1: **Check if Employee Exists Based on Email**
        email = employee_data.get("email")
        employee = db.query(Employee).filter(Employee.email == email).first()
        if not employee:

            # Step 2: **Check if User Already Exists**
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="User account already exists for this employee.")

            
            # Step 3: **Check if Ro,e ID  Exists**
            findRole = db.query(Role).filter(Role.id == role_id).first()
            if not findRole:
                raise HTTPException(status_code=404, detail="Role Not Found.")
            

            existing_role = db.query(User).filter(User.role_id == role_id).first()
            if existing_role:
                raise HTTPException(status_code=400, detail="Role Already Assigned to Another User")
            
            
            # Step 4: **Check for Required Employee Fields**
            required_fields = ["first_name", "last_name", "date_of_birth", "email"]
            for field in required_fields:
                if not employee_data.get(field):
                    raise HTTPException(status_code=400, detail=f"Missing required field: {field}")


            # Step 5: **Generate Credentials**
            user_name =  f"{employee_data.get('first_name').lower()}{employee_data.get('last_name').lower()}{Security.generate_random_string(4)}" or Security.generate_random_string(6)
            password = Security.generate_random_string(6)
            hashed_password = self.hash_password(password)

            
                

            # Step 7: **Upload Image to Google Cloud Storage**
            folder = f"organizations/{org.name}/user_profiles"
            gcs = GoogleCloudStorage(bucket_name=settings.BUCKET_NAME)


            if image_file:
                logo_files = [{"filename": file.filename, "content": await file.read()} for file in image_file]
            
                image_url = gcs.upload_to_gcs(files=logo_files, folder=folder) or {}

                # Step 6: **Send Image File to External Bio Authentication API**
                # image_bytes = await image_file[0].read()
                # async with aiohttp.ClientSession(timeout=ClientTimeout(total=120)) as session:
                #     form = FormData()
                #     form.add_field("username", user_name)
                #     form.add_field("file", image_bytes, filename="image.jpg", content_type=image_file[0].content_type)

                #     try:
                #         logger.info(f"Sending facial auth request for {user_name} to {settings.FACIAL_AUTH_API_URL}")
                #         async with session.post(settings.FACIAL_AUTH_API_URL, data=form) as response:
                #             bio_auth_result = await response.json()
                #             logger.info(f"Response received: {bio_auth_result}")
                #             if response.status != 200:
                #                 raise HTTPException(status_code=500, detail=f"Bio authentication failed: {bio_auth_result}")
                            
                #             if response.status == 502:
                #                 logger.info(f"Response received: {response.status}: \nMeans the issue has to do with the external api itself not from the call.")
                #                 print(f"Response received: {response.status}: \nMeans the issue has to do with the external api itself not from the call.")
                #     except asyncio.TimeoutError:
                #         logger.error(f"Facial authentication timeout for {user_name}")
                #         raise HTTPException(status_code=504, detail="Facial authentication service timeout. Please try again.")

            
            # Step 8: **Create Employee Record**
            employee_record = Employee(
                first_name=employee_data["first_name"],
                middle_name=employee_data.get("middle_name"),
                last_name=employee_data["last_name"],
                title=employee_data.get("title", "Other"),
                gender=employee_data.get("gender", "Other"),
                date_of_birth=employee_data["date_of_birth"],
                marital_status=employee_data.get("marital_status", "Other"),
                email=email,
                contact_info=json.dumps(employee_data.get("contact_info", {})),
                hire_date=employee_data.get("hire_date"),
                termination_date=employee_data.get("termination_date"),
                is_active=True,
                custom_data=json.dumps(employee_data.get("custom_data", {})),
                profile_image_path=json.dumps(image_url),
                organization_id=organization_id,
            )
            db.add(employee_record)
            db.commit()
            db.refresh(employee_record)

            # Log user creation
            # await self.log_audit(db, "CREATE", created_by, "employees" ,employee_record.id)


            # Step 9: **Create User & Employee Image Paths**
            user_record = User(
            username= user_name,
            email= email,
            hashed_password= hashed_password,
            role_id = role_id,
            organization_id = organization_id,
            is_active = True,
            image_path = json.dumps(image_url),  # Store in User model
            )
            # new_user = User(**user_data)
            db.add(user_record)
            db.commit()
            db.refresh(user_record)

        

            # Log user creation
            # self.log_audit(db, "CREATE", created_by, "users" ,user_record.id)

            email_service = EmailService()  # Instantiate the email service
            # Send email with credentials
            email_body = get_email_template(user_name, password, org.access_url)
            await email_service.send_email(background_tasks, recipients=[email], subject="Account Credentials", html_body=email_body)

        

            return {
                "id": user_record.id,
                "message": "User created successfully",
                "image_path": image_url,
            }
            # raise HTTPException(status_code=404, detail="Employee record not found. Register employee first.")
        else:
            logger.error(f"\n\nAn Employee with the Email '{employee_data.get('email')}' already exists.")
            raise HTTPException(status_code=404, detail="Email Already Exists.")

        
        
    

    async def update_user(
        self,
        background_tasks: BackgroundTasks,
        db: Session,
        user_id: UUID,
        username: Optional[str] = None,
        email: Optional[str] = None,
        role_id: Optional[UUID] = None,
        image_file: Optional[UploadFile] = None
    ) -> Dict[str, str]:
        """
        Dynamically updates a user's details while ensuring security, efficiency, and business logic integrity.

        :param background_tasks: BackgroundTasks for async email notifications.
        :param db: Database session.
        :param user_id: The ID of the user being updated.
        :param username: (Optional) New username.
        :param email: (Optional) New email.
        :param role_id: (Optional) New role ID.
        :param image_file: (Optional) New profile image file.
        :return: Dictionary containing a success message.
        """

        if not user_id:
            raise HTTPException(status_code=400, detail="User Identifier (user_id) is required.")

        # Fetch user and employee records
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        employee = db.query(Employee).filter(Employee.email == user.email).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Associated employee record not found.")

        update_fields = {}

        # 🚫 **Ensure Organization ID is Immutable**
        organization_id = user.organization_id
        organization = db.query(Organization).filter(Organization.id == organization_id).first()

        if not organization:
            raise HTTPException(status_code=404, detail="Associated organization not found.")

        # ✅ **Handle Email Updates**
        if email and email != user.email:
            email_exists = db.query(User).filter(User.email == email, User.id != user_id).first()
            if email_exists:
                raise HTTPException(status_code=400, detail="Email is already in use.")

            update_fields["email"] = email
            employee.email = email  # Ensure Employee email syncs with User

        # ✅ **Handle Username Updates & External API Trigger**
        if username and username != user.username:
            username_exists = db.query(User).filter(User.username == username, User.id != user_id).first()
            if username_exists:
                raise HTTPException(status_code=400, detail="Username is already taken.")

            # Retrieve existing image from Google Cloud Storage
            gcs = GoogleCloudStorage(bucket_name=settings.BUCKET_NAME)
            image_data = gcs.download_from_gcs(user.image_path) if user.image_path else None

            # Call External API for Facial Authentication Username Update
            if image_data:
                async with aiohttp.ClientSession(timeout=ClientTimeout(total=120)) as session:
                    form = FormData()
                    form.add_field("new_username", username)
                    form.add_field("file", image_data, filename="image.jpg", content_type="image/jpeg")

                    try:
                        async with session.put(f"{settings.FACIAL_AUTH_API_URL}/update/{user.username}", data=form) as response:
                            if response.status == 502:
                                logger.warning(f"External API deployment issue detected: {response.status}. Issue is with the API, not the request.")
                            elif response.status != 200:
                                raise HTTPException(status_code=500, detail="Failed to update facial authentication system.")
                    except asyncio.TimeoutError:
                        raise HTTPException(status_code=504, detail="External API timeout. Please try again.")

            update_fields["username"] = username

        # ✅ **Handle Role Updates**
        if role_id and role_id != user.role_id:
            role = db.query(Role).filter(Role.id == role_id, Role.organization_id == organization_id).first()
            if not role:
                raise HTTPException(status_code=400, detail="Invalid role ID for this organization.")

            update_fields["role_id"] = role_id

        # ✅ **Handle Profile Image Updates**
        if image_file:
            gcs = GoogleCloudStorage(bucket_name=settings.BUCKET_NAME)

            # Delete old image from Google Cloud if it exists
            if user.image_path:
                gcs.delete_from_gcs(user.image_path)

            # Upload new image
            folder = f"organizations/{organization.name}/user_profiles"
            new_image_url = gcs.upload_to_gcs(
                [{"filename": image_file.filename, "content": await image_file.read()}],
                folder
            )

            update_fields["image_path"] = new_image_url
            employee.profile_image_path = new_image_url  # Ensure Employee profile image is updated

        # ✅ **Apply Updates if Any**
        if update_fields:
            for field, value in update_fields.items():
                setattr(user, field, value)

            db.commit()
        else:
            raise HTTPException(status_code=400, detail="No valid update fields provided.")

        # ✅ **Send Email Notification**
        email_service = EmailService()
        email_body = f"Hello {user.username},\n\nYour account details have been successfully updated.\n\nRegards,\nTeam"
        background_tasks.add_task(email_service.send_email, recipients=[user.email], subject="Account Update", html_body=email_body)

        return {"message": "User updated successfully."}



        


    async def authenticate_user(db: Session, username: str, password: str, request) -> Dict:
        """
        Authenticates a user while enforcing rate limits and logging failed login attempts.
        """
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Apply rate limit before authentication
        rate_limiter.check_rate_limit(db, user, request)

        # Verify password
        if not Security.verify_password(password, user.hashed_password):
            rate_limiter.log_failed_attempt(user, request)  # Log failed attempt
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Reset failed login attempts on success
        rate_limiter.reset_attempts(user)

        # Generate JWT Token
        token_data = {
            "user_id": str(user.id),
            "username": user.username,
            "role_id": str(user.role_id),
            "organization_id": str(user.organization_id),
        }
        token = Security.generate_token(token_data)

        return {
            "username": user.username,
            "email": user.email,
            "token": token,
            "token_expiration": datetime.datetime.utcnow() + datetime.timedelta(seconds=3600),
            "role": user.role.name,
            "permissions": user.role.permissions,
            "organization_id": user.organization_id,
            "organization_name": user.organization.name,
            "access_url": user.organization.access_url,
            "dashboard_data": user.organization.dashboards,
            "settings_name": user.organization.settings,
        }
        


    async def create_ceo_account(
        self,
        db: AsyncSession,
        organization_data: OrganizationCreateSchema,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, str]:
        """
        Creates an organization, CEO role, and CEO user account.
        Automatically sends an email with username and password.
        """
        try:
            # Step 1: Create Organization
            organization = self.org_model(**organization_data.dict())
            db.add(organization)
            await db.commit()
            await db.refresh(organization)

            # Step 2: Create CEO Role
            permissions = get_permissions_from_db(db, "CEO")
            # role_data = {
            #     "name": "CEO",
            #     "permissions": permissions,
            #     "organization_id": organization.id,
            # }
              # Step 2: Create CEO Role
            role_data = await self.role_cache.get_or_create_role(
                db, self.role_model, "CEO", permissions, organization.id
            )
            role = self.role_model(**role_data)
            db.add(role)
            await db.commit()
            await db.refresh(role)

            # Step 3: Create CEO User
            username = generate_random_string(USERNAME_LENGTH)
            password = generate_random_string(PASSWORD_LENGTH)
            hashed_password = self.hash_password(password)

            user_data = {
                "username": username,
                "email": organization_data.email,
                "hashed_password": hashed_password,
                "role_id": role.id,
                "organization_id": organization.id,
                "is_active": True,
            }
            user = self.user_model(**user_data)
            db.add(user)
            await db.commit()
            await db.refresh(user)

            # Step 4: Send Email to CEO
            email_body = (
                f"<h1>Welcome to the System!</h1>"
                f"<p>Your account has been created with the following details:</p>"
                f"<ul><li>Username: {username}</li><li>Password: {password}</li></ul>"
                f"<p>Please log in and change your password immediately.</p>"
            )
            # send_email(
            #     to_email=organization_data.email,
            #     subject="Your Account Details",
            #     body=email_body,
            #     background_tasks=background_tasks,
            # )

            background_tasks.add_task(
                send_email_async, organization_data.email, "Your Account Details", email_body, db, self.audit_model, user.id
            )

            # # Log Audit
            # await self.log_audit(db, "create_ceo_account", user.id, "users", user.id)

            # Log Audit
            await log_audit(db, self.audit_model, "create_ceo_account", user.id, "users", user.id)

            return {"message": "CEO account created successfully.", "username": username, "password": password}

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create CEO account: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create CEO account: {str(e)}"
            )

    async def create_employee_user(
        self,
        db: AsyncSession,
        employee_data: EmployeeCreateSchema,
        performed_by: Optional[UUID],
        background_tasks: BackgroundTasks,
    ) -> Dict[str, str]:
        """
        Creates a user account for an existing employee.
        Automatically sends an email with username and password.
        """
        try:
            # Fetch Employee Details
            employee = (
                await db.query(self.employee_model)
                .filter(self.employee_model.id == employee_data.employee_id)
                .first()
            )
            if not employee:
                raise HTTPException(status_code=404, detail="Employee not found")

            # Check if User Already Exists
            existing_user = (
                await db.query(self.user_model)
                .filter(self.user_model.email == employee.email)
                .first()
            )
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="User account already exists for this employee",
                )

            # Generate Username and Password
            username = generate_random_string(USERNAME_LENGTH)
            password = generate_random_string(PASSWORD_LENGTH)
            hashed_password = self.hash_password(password)

            # Create User Account
            user_data = {
                "username": username,
                "email": employee.email,
                "hashed_password": hashed_password,
                "role_id": employee.role_id,
                "organization_id": employee.organization_id,
                "is_active": True,
            }
            user = self.user_model(**user_data)
            db.add(user)
            await db.commit()
            await db.refresh(user)

            # Send Email to Employee
            email_body = (
                f"<h1>Your Account Details</h1>"
                f"<p>Your account has been created with the following details:</p>"
                f"<ul><li>Username: {username}</li><li>Password: {password}</li></ul>"
                f"<p>Please log in and change your password immediately.</p>"
            )
            # send_email(
            #     to_email=employee.email,
            #     subject="Your Account Details",
            #     body=email_body,
            #     background_tasks=background_tasks,
            # )

            background_tasks.add_task(
                send_email_async, employee.email, "Your Account Details", email_body, db, self.audit_model, user.id
            )

            # Log Audit
            # await self.log_audit(db, "create_employee_user", performed_by, "users", user.id)

            # Log Audit
            await log_audit(db, self.audit_model, "create_employee_user_account", performed_by, "users", user.id)


            return {"message": "Employee account created successfully.", "username": username, "password": password}

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create employee user account: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create employee user account: {str(e)}",
            )
    
    async def bulk_create_users_from_file(
        self,
        db: AsyncSession,
        file: UploadFile,
        current_user: Dict,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Bulk create user accounts from a file.
        """
        if file.content_type not in ["text/csv", "application/vnd.ms-excel"]:
            raise HTTPException(
                status_code=400,
                detail="Only CSV and Excel files are supported."
            )

        results = []
        try:
            # Load file content
            content = file.file.read()
            if file.content_type == "text/csv":
                data = pd.read_csv(io.StringIO(content.decode("utf-8")))
            else:
                data = pd.read_excel(io.BytesIO(content))

            # Normalize column names
            data.columns = [col.lower().strip() for col in data.columns]

            # Validate file structure
            validate_file_structure(
                data,
                ["name", "dob", "email", "contact", "position"]
            )

            # Determine organization ID from the current user's session
            organization_id = current_user.get("organization_id")
            if not organization_id:
                raise HTTPException(
                    status_code=403,
                    detail="Current user's organization could not be determined. Ensure you are logged in."
                )

            semaphore = asyncio.Semaphore(10)

            async def process_row(row):
                async with semaphore:
                    try:
                        email = row.get("email")
                        if not email:
                            raise ValueError("Email is required but missing.")
                        
                        if not email or not Validator.is_valid_email(email):
                            return { "status": "failed", "error": "Invalid or missing email"}


                        # Check if user already exists
                        existing_user = await db.query(self.user_model).filter(
                            self.user_model.email == email
                        ).first()
                        if existing_user:
                            return {"email": email, "status": "failed", "error": "User already exists"}
                        
                        dob = row.get("dob")
                        if not Validator.is_valid_dob(dob):
                            return { "status": "failed", "error": "Invalid DOB"}

                        # Generate username and password
                        username = generate_random_string(USERNAME_LENGTH)
                        password = generate_random_string(PASSWORD_LENGTH)
                        hashed_password = self.hash_password(password)

                        # Determine role and permissions
                        position = row.get("position", "staff")
                        job_description = row.get("job_description", DEFAULT_PERMISSIONS.get("staff"))

                        # Check if the role already exists
                        # role = await db.query(self.role_model).filter(
                        #     self.role_model.name == position,
                        #     self.role_model.organization_id == organization_id
                        # ).first()

                        # Retrieve or create role
                        role = await self.role_cache.get_or_create_role(
                            db, self.role_model, position, job_description, organization_id
                        )

                        if not role:
                            role = self.role_model(
                                name=position,
                                permissions=job_description,
                                organization_id=organization_id,
                            )
                            db.add(role)
                            await db.commit()
                            await db.refresh(role)

                        # Create user record
                        user = self.user_model(
                            username=username,
                            email=email,
                            hashed_password=hashed_password,
                            role_id=role.id,
                            organization_id=organization_id,
                            is_active=True,
                        )
                        db.add(user)
                        await db.commit()
                        await db.refresh(user)

                        # Send email notification
                        email_body = (
                            f"<h1>Your Account Details</h1>"
                            f"<p>Your account has been created with the following details:</p>"
                            f"<ul><li>Username: {username}</li><li>Password: {password}</li></ul>"
                            f"<p>Please log in and change your password immediately.</p>"
                        )
                        # send_email(
                        #     to_email=email,
                        #     subject="Your Account Details",
                        #     body=email_body,
                        #     background_tasks=background_tasks,
                        # )
                        background_tasks.add_task(send_email_async, email, "Account Details", email_body, db, self.audit_model, current_user["id"])
                        # Log audit for successful user creation
                        await self.log_audit(
                            db=db,
                            action="bulk_user_creation_success",
                            performed_by=current_user["id"],
                            table_name="users",
                            record_id=user.id,
                        )

                        return {"email": email, "status": "success", "username": username, "password": password}

                    except Exception as e:
                        logger.error(f"Failed to create user for email {row.get('email')}: {str(e)}")
                        return {"email": row.get("email"), "status": "failed", "error": str(e)}

            # Process rows concurrently
            tasks = [process_row(row) for _, row in data.iterrows()]
            results = await asyncio.gather(*tasks)

            return {"message": "Bulk user creation completed.", "results": results}

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to bulk create users: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Bulk user creation failed: {str(e)}"
            )
        

        
    # async def bulk_create_users_from_file(
    #     self,
    #     db: AsyncSession,
    #     file: UploadFile,
    #     current_user: Dict,
    #     background_tasks: BackgroundTasks,
    # ) -> Dict[str, List[Dict[str, str]]]:
    #     """
    #     Bulk create user accounts from a file.
    #     Extract relevant data and automatically assign missing fields where necessary.
    #     """
    #     if file.content_type not in ["text/csv", "application/vnd.ms-excel"]:
    #         raise HTTPException(
    #             status_code=400,
    #             detail="Only CSV and Excel files are supported."
    #         )

    #     results = []
    #     try:
    #         # Load file content
    #         content = file.file.read()
    #         if file.content_type == "text/csv":
    #             data = pd.read_csv(io.StringIO(content.decode("utf-8")))
    #         else:
    #             data = pd.read_excel(io.BytesIO(content))

    #         # Normalize column names
    #         data.columns = [col.lower().strip() for col in data.columns]

    #         # Mapping columns to expected fields
    #         column_map = {
    #             "name": ["name", "first name", "middle name", "last name", "surname"],
    #             "dob": ["date of birth", "dob", "d.o.b"],
    #             "email": ["email", "email address", "e-mail", "e-mail address"],
    #             "contact": ["contact", "phone", "phone number", "telephone"],
    #             "position": ["position", "role", "rank"],
    #             "job_description": ["job description", "job", "tasks"]
    #         }

    #         def get_column(data: pd.DataFrame, possible_names: List[str]) -> pd.Series:
    #             """Retrieve the column data for the first matching name in possible_names."""
    #             for name in possible_names:
    #                 if name in data.columns:
    #                     return data[name]
    #             return pd.Series([None] * len(data), name="unknown")

    #         # Extract columns
    #         name_col = get_column(data, column_map["name"])
    #         dob_col = get_column(data, column_map["dob"])
    #         email_col = get_column(data, column_map["email"])
    #         contact_col = get_column(data, column_map["contact"])
    #         position_col = get_column(data, column_map["position"])
    #         job_description_col = get_column(data, column_map["job_description"])

    #         # Determine organization ID from the current user's session
    #         organization_id = current_user.get("organization_id")
    #         if not organization_id:
    #             raise HTTPException(
    #                 status_code=403,
    #                 detail="Current user's organization could not be determined. Ensure you are logged in."
    #             )

    #         # Iterate through rows and create users
    #         for idx, row in data.iterrows():
    #             try:
    #                 email = email_col.iloc[idx]
    #                 if not email:
    #                     raise ValueError("Email is required but missing.")

    #                 # Check if user already exists
    #                 existing_user = await db.query(self.user_model).filter(
    #                     self.user_model.email == email
    #                 ).first()
    #                 if existing_user:
    #                     results.append(
    #                         {
    #                             "email": email,
    #                             "status": "failed",
    #                             "error": "User already exists",
    #                         }
    #                     )
    #                     # Log audit for failed user creation
    #                     await self.log_audit(
    #                         db=db,
    #                         action="bulk_user_creation_failed",
    #                         performed_by=current_user["id"],
    #                         table_name="users",
    #                         record_id=None,
    #                     )
    #                     continue

    #                 # Generate username and password
    #                 username = generate_random_string(USERNAME_LENGTH)
    #                 password = generate_random_string(PASSWORD_LENGTH)
    #                 hashed_password = self.hash_password(password)

    #                 # Determine role and permissions
    #                 position = position_col.iloc[idx] or "staff"
    #                 job_description = job_description_col.iloc[idx]

    #                 # Check if the role already exists
    #                 role = await db.query(self.role_model).filter(
    #                     self.role_model.name == position,
    #                     self.role_model.organization_id == organization_id
    #                 ).first()

    #                 if not role:
    #                     # Insert role with default permissions if it doesn't exist
    #                     role_permissions = job_description or {
    #                         "create_task": True,
    #                         "view_task": True,
    #                         "update_task": False,
    #                         "delete_task": False,
    #                     }

    #                     role_data = {
    #                         "name": position,
    #                         "permissions": role_permissions,
    #                         "organization_id": organization_id,
    #                     }
    #                     role = self.role_model(**role_data)
    #                     db.add(role)
    #                     await db.commit()
    #                     await db.refresh(role)

    #                 # Create user record
    #                 user_data = {
    #                     "username": username,
    #                     "email": email,
    #                     "hashed_password": hashed_password,
    #                     "role_id": role.id,
    #                     "organization_id": organization_id,
    #                     "is_active": True,
    #                 }
    #                 user = self.user_model(**user_data)
    #                 db.add(user)
    #                 await db.commit()
    #                 await db.refresh(user)

    #                 # Send email notification
    #                 email_body = (
    #                     f"<h1>Your Account Details</h1>"
    #                     f"<p>Your account has been created with the following details:</p>"
    #                     f"<ul><li>Username: {username}</li><li>Password: {password}</li></ul>"
    #                     f"<p>Please log in and change your password immediately.</p>"
    #                 )
    #                 send_email(to_email=email, subject="Your Account Details", body=email_body, background_tasks=background_tasks)

    #                 # Append success result
    #                 results.append(
    #                     {
    #                         "email": email,
    #                         "status": "success",
    #                         "username": username,
    #                         "password": password,
    #                     }
    #                 )

    #                 # Log audit for successful user creation
    #                 await self.log_audit(
    #                     db=db,
    #                     action="bulk_user_creation_success",
    #                     performed_by=current_user["id"],
    #                     table_name="users",
    #                     record_id=user.id,
    #                 )

    #             except Exception as e:
    #                 logger.error(f"Failed to create user for email {email}: {str(e)}")
    #                 results.append(
    #                     {
    #                         "email": email,
    #                         "status": "failed",
    #                         "error": str(e),
    #                     }
    #                 )
    #                 # Log audit for failed user creation
    #                 await self.log_audit(
    #                     db=db,
    #                     action="bulk_user_creation_failed",
    #                     performed_by=current_user["id"],
    #                     table_name="users",
    #                     record_id=None,
    #                 )

    #         return {"message": "Bulk user creation completed.", "results": results}

    #     except Exception as e:
    #         await db.rollback()
    #         logger.error(f"Failed to bulk create users: {str(e)}")
    #         raise HTTPException(
    #             status_code=500,
    #             detail=f"Bulk user creation failed: {str(e)}"
    #         )


