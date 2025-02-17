from sqlalchemy import (
    Column, Index, String, Boolean, JSON, Date, DateTime, Integer, ForeignKey, DECIMAL,
    Table, create_engine, CheckConstraint, LargeBinary, event
)
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref, Session
from datetime import datetime, timedelta, timezone
from enum import Enum
# import uuid
from Models.Tenants.organization import Organization
from Service.email_service import EmailService, get_email_template
from Utils.security import Security
from database.db_session import BaseModel, get_db
from fastapi import HTTPException, BackgroundTasks

# Enums
class Gender(Enum):
    Male = "Male"
    Female = "Female"
    Other = "Other"

class MaritalStatus(Enum):
    Single = "Single"
    Married = "Married"
    Divorced = "Divorced"
    Widowed = "Widowed"
    Separated = "Separated"
    Other = "Other"

class Title(Enum):
    Prof = 'Prof.'
    Phd = 'PhD'
    Dr = 'Dr.'
    Mr = 'Mr.'
    Mrs = 'Mrs.'
    Ms = 'Ms.'
    Esq = 'Esq.'
    Hon = 'Hon.'
    Rev = 'Rev.'
    Msgr = 'Msgr.'
    Sr = 'Sr.'
    Other = 'Other'


# Calculate the range for the year constraint
current_year = datetime.now().year
min_year = current_year - 18
max_year = current_year - 60


# User Model
class User(BaseModel):
    __tablename__ = "users"

    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True )
    hashed_password = Column(String, nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True)
    image_path = Column(String, nullable=True)  # Path to the facial image for authentication
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_attempts = Column(Integer, default=0)
    

    organization = relationship("Organization", back_populates="users")
    role = relationship("Role", back_populates="users")
    # employee = relationship("Employee", back_populates="users")
    files = relationship(
        "FileStorage",
        primaryjoin="and_(FileStorage.record_id == User.id, FileStorage.record_type == 'users')",
        foreign_keys="[FileStorage.record_id, FileStorage.record_type]",
        viewonly=True,
    )

class Token(BaseModel):
    __tablename__ = "tokens"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, nullable=False)
    expiration_period = Column(DateTime, nullable=False)
    login_option = Column(String, nullable=False)
    last_activity = Column(DateTime, nullable=True)

# Employee Model
class Employee(BaseModel):
    __tablename__ = "employees"

    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    title = Column(String, default=Title.Other.value)
    gender = Column(String, default=Gender.Other.value)
    date_of_birth = Column(Date, nullable=True)
    marital_status = Column(String, default=MaritalStatus.Other.value)
    email = Column(String, nullable=False, unique=True)
    contact_info = Column(JSONB, nullable=True)
    hire_date = Column(Date, nullable=True)
    termination_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    custom_data = Column(JSONB, nullable=True)
    profile_image_path = Column(String, nullable=True)  # File path for profile image
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    organization = relationship("Organization", back_populates="employees")
    # users = relationship("User", back_populates="employee")
    academic_qualifications = relationship("AcademicQualification", back_populates="employee", cascade="all, delete-orphan")
    professional_qualifications = relationship("ProfessionalQualification", back_populates="employee", cascade="all, delete-orphan")
    employment_history = relationship("EmploymentHistory", back_populates="employee", cascade="all, delete-orphan")
    emergency_contacts = relationship("EmergencyContact", back_populates="employee", cascade="all, delete-orphan")
    next_of_kins = relationship("NextOfKin", back_populates="employee", cascade="all, delete-orphan")
    files = relationship(
        "FileStorage",
        primaryjoin="and_(FileStorage.record_id == Employee.id, FileStorage.record_type == 'employees')",
        foreign_keys="[FileStorage.record_id, FileStorage.record_type]",
        viewonly=True,
    )

    # =============================================================================
# Event Listener for Automatic User Creation
# =============================================================================
# NOTE: This listener is placed right after the models are defined. In a larger
# application you may move this into a separate module (e.g. events.py) and import
# it on startup.
@event.listens_for(Employee, "after_insert")
def create_user_for_employee(mapper, connection, target):
    """
    After an Employee record is inserted, create a corresponding User.
    Expects transient attributes _role_id and _plain_password on target.
    """
    # Retrieve the role id that was attached during employee creation.
    role_id = getattr(target, "_role_id", None)
    plain_password = getattr(target, "_plain_password", None)
    user_image = getattr(target, "_user_image", None)
    created_by = getattr(target, "_created_by", None)

    if role_id is None:
        # You may log a warning or decide to skip user creation.
        print(f"Employee {target.id} inserted with no role; skipping user creation.")
        return

    if plain_password is None:
        password_plain = Security.generate_random_string(6)
    else:
        password_plain = plain_password


    # Generate a username from the employee’s first name plus 4 random digits.
    username = f"{target.email}"
    hashed_pw = Security.hash_password(password_plain)

    # Insert the corresponding user record.
    user_table = User.__table__
    ins_stmt = user_table.insert().values(
        username=username,
        email=target.email,
        hashed_password=hashed_pw,
        role_id=role_id,
        organization_id=target.organization_id,
        is_active=True,
        image_path = user_image,
        created_by = created_by
        
    )
    connection.execute(ins_stmt)

    
    # In a production system, send the plain password securely (or force a reset).
    print(
        f"User created for Employee {target.id}: username '{username}' with initial password '{password_plain}'"
    )
    return {"data": f"User created for Employee {target.id}: username '{username}' with initial password '{password_plain}'"}


# Academic Qualification
class AcademicQualification(BaseModel):
    __tablename__ = "academic_qualifications"

    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    degree = Column(String, nullable=False)
    institution = Column(String, nullable=False)
    year_obtained = Column(Integer, nullable=False)
    details = Column(JSONB, nullable=True)
    certificate_path = Column(String, nullable=True)  # Path to the certificate file
   
    employee = relationship("Employee", back_populates="academic_qualifications")
    files = relationship(
        "FileStorage",
        primaryjoin="and_(FileStorage.record_id == AcademicQualification.id, FileStorage.record_type == 'academic_qualifications')",
        foreign_keys="[FileStorage.record_id, FileStorage.record_type]",
        viewonly=True,
    )

class ProfessionalQualification(BaseModel):
    __tablename__ = "professional_qualifications"

    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    qualification_name = Column(String, nullable=False)
    institution = Column(String, nullable=False)
    year_obtained = Column(Integer, nullable=False)
    details = Column(JSONB, nullable=True)
    license_path = Column(String, nullable=True)  # Path to the professional license

    # Relationships
    employee = relationship("Employee", back_populates="professional_qualifications")
    files = relationship(
        "FileStorage",
        primaryjoin="and_(FileStorage.record_id == ProfessionalQualification.id, FileStorage.record_type == 'professional_qualifications')",
        foreign_keys="[FileStorage.record_id, FileStorage.record_type]",
        viewonly=True,
    )

# Employment History
class EmploymentHistory(BaseModel):
    __tablename__ = "employment_history"

    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    job_title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    details = Column(JSONB, nullable=True)
    documents_path = Column(String, nullable=True)  # Path to related documentsy

    #Relationship
    employee = relationship("Employee", back_populates="employment_history")
    files = relationship(
        "FileStorage",
        primaryjoin="and_(FileStorage.record_id == EmploymentHistory.id, FileStorage.record_type == 'employment_history')",
        foreign_keys="[FileStorage.record_id, FileStorage.record_type]",
        viewonly=True,
    )

# Emergency Contact
class EmergencyContact(BaseModel):
    __tablename__ = "emergency_contacts"

    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    relation = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=True)
    details = Column(JSONB, nullable=True)

    employee = relationship("Employee", back_populates="emergency_contacts")

# Next of Kin
class NextOfKin(BaseModel):
    __tablename__ = "next_of_kin"

    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    relation = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=True)
    details = Column(JSONB, nullable=True)
 
    employee = relationship("Employee", back_populates="next_of_kins")

# File Storage
class FileStorage(BaseModel):
    __tablename__ = "file_storage"

    file_name = Column(String, nullable=False)  # Name of the file
    file_path = Column(String, nullable=False)  # Full path/URL to the file
    file_type = Column(String, nullable=False)  # e.g., Image, Document, PDF
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # User who uploaded
    record_id = Column(UUID(as_uuid=True), nullable=False)  # ID of the related record (e.g., employee, academic qualification)
    record_type = Column(String, nullable=False)  # Related table name (e.g., "employees", "academic_qualifications")
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

  
    # Relationships
    organization = relationship("Organization", back_populates="files")
    users = relationship("User", back_populates="files")

    

# Audit Log
class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    action = Column(String, nullable=False)
    table_name = Column(String, nullable=False)
    record_id = Column(UUID(as_uuid=True), nullable=False)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    timestamp = Column(DateTime(timezone=True), default=func.now())

    user = relationship("User", backref="audit_logs")


class SystemSetting(BaseModel):
    __tablename__ = "system_settings"

    setting_name = Column(String, nullable=False, unique=True)
    setting_value = Column(JSONB, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    organization = relationship("Organization", back_populates="settings")

class Dashboard(BaseModel):
    __tablename__ = "dashboards"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dashboard_name = Column(String, nullable=False)
    dashboard_data = Column(JSONB, nullable=False)
    access_url = Column(String, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    organization = relationship("Organization", back_populates="dashboards")


class DataBank(BaseModel):
    __tablename__ = "data_banks"

    data_name = Column(String, nullable=False)
    data = Column(MutableList.as_mutable(JSONB), nullable=False)
    # organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)

    # organization = relationship("Organization", back_populates="data_banks")


# Indexes
Index('idx_user_organization', User.organization_id, User.email, unique=True)
Index('idx_employee_organization', Employee.organization_id, Employee.email, unique=True)
