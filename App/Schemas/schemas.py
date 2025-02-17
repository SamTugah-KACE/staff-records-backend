
import json
from pydantic import BaseModel, EmailStr, Field, field_validator, root_validator, model_validator
from typing import Optional, List, Dict, Union
from uuid import UUID
from datetime import datetime, date
from enum import Enum




# Enums
class Gender(str, Enum):
    male = "Male"
    female = "Female"
    other = "Other"

class MaritalStatus(str, Enum):
    single = "Single"
    married = "Married"
    divorced = "Divorced"
    widowed = "Widowed"
    separated = "Separated"
    other = "Other"

class Title(str, Enum):
    prof = 'Prof.'
    phd = 'PhD'
    dr = 'Dr.'
    mr = 'Mr.'
    mrs = 'Mrs.'
    ms = 'Ms.'
    esq = 'Esq.'
    hon = 'Hon.'
    rev = 'Rev.'
    msgr = 'Msgr.'
    sr = 'Sr.'
    other = 'Other'

class BillingCycle(str, Enum):
    monthly = "Monthly"
    annually = "Annually"

class TenancyStatus(str, Enum):
    active = "Active"
    terminated = "Terminated"
    pending = "Pending"

class PaymentStatus(str, Enum):
    unpaid = "Unpaid"
    paid = "Paid"
    overdue = "Overdue"

# Shared Base Schema
class BaseSchema(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[UUID]
    updated_by: Optional[UUID]

    class Config:
        orm_mode = True

# Organization Schemas
class OrganizationCreateSchema(BaseModel):
    name: str
    org_email: EmailStr
    country: str
    type: str
    nature: str
    employee_range: str
    access_url: str
    subscription_plan: Optional[str] = "Basic"
    logos: Optional[Dict] = {}
    tenancies:Optional[List["TenancyCreateSchema"]]
    roles: Optional[List["RoleCreateSchema"]] 
    employees: Optional[List["EmployeeCreateSchema"]]
    users: Optional[List["UserCreateSchema"]] 
    # dashboard: Optional[List["DashboardCreateSchema"]]
    settings: Optional[List["SystemSettingCreateSchema"]] 

    @field_validator("type")
    def validate_type(cls, value):
        if value not in ["Private", "Government", "Public", "NGO"]:
            raise ValueError("Type must be either 'Private', 'NGO', 'Government' or 'Public'")
        return value

class OrganizationSchema(BaseSchema):
    name: str
    org_email: EmailStr
    country: str
    type: str
    nature: str
    employee_range: str
    access_url: str
    subscription_plan: Optional[str]
    is_active: bool
    logos: Optional[Dict] = {}
    users: Optional[List["UserSchema"]] = []
    employees: Optional[List["EmployeeSchema"]] = []
    roles: Optional[List["RoleSchema"]] = []
    tenancies:Optional[List["TenancySchema"]] = []
    # dashboard: Optional[List["DashboardCreateSchema"]]
    settings: Optional[List["SystemSettingSchema"]] = []

    class Config:
        from_attributes = True  # Enable ORM object compatibility

# Role Schemas
class RoleCreateSchema(BaseModel):
    name: str
    permissions: Optional[Dict] = {}
    organization_id: Optional[UUID]
    

    @field_validator("name")
    def validate_name(cls, value):
        if not value:
            raise ValueError("Role name cannot be empty")
        return value

class RoleSchema(BaseSchema):
    name: str
    permissions: Optional[Dict]
    organization_id: Optional[UUID]

    class Config:
        from_attributes = True

# User Schemas
class UserCreateSchema(BaseModel):
    username: Optional[str]
    email: EmailStr
    hashed_password: Optional[str] 
    role_id: Optional[UUID]
    organization_id: Optional[UUID]
    image_path: Optional[str]
    # dashboard: Optional[List["DashboardCreateSchema"]]

    # @field_validator("hashed_password")
    # def validate_password(cls, value):
    #     if len(value) < 8:
    #         raise ValueError("Password must be at least 8 characters long")
    #     return value

class UserSchema(BaseSchema):
    username: str
    email: EmailStr
    is_active: bool
    organization_id: UUID
    role_id: Optional[UUID]
    image_path: Optional[str]
    # dashboard: Optional[List["DashboardCreateSchema"]]

    class Config:
        from_attributes = True

# Tenancy Schemas
class TenancyCreateSchema(BaseModel):
    organization_id: UUID
    start_date: date
    billing_cycle: Optional[str] = "Monthly"
    terms_and_conditions_id: Optional[UUID]
    terms_and_conditions: Optional[List["TermsAndConditionsCreateSchema"]]

class TenancySchema(BaseSchema):
    organization_id: UUID
    start_date: date
    end_date: Optional[date]
    billing_cycle: str
    status: str
    terms_and_conditions_id: Optional[UUID]

    @field_validator("billing_cycle")
    def validate_billing_cycle(cls, value):
        if value not in ["Monthly", "Annually"]:
            raise ValueError("Billing cycle must be 'Monthly' or 'Annually'")
        return value
    
    class Config:
        from_attributes = True



# Terms and Conditions Schemas
class TermsAndConditionsCreateSchema(BaseModel):
    title: str
    content: Dict
    version: Optional[str]
    is_active: Optional[bool] = True


class TermsAndConditionsSchema(BaseSchema):
    title: str
    content: Dict
    version: str
    is_active: bool

    class Config:
        from_attributes = True

# Billing Schemas
class BillCreateSchema(BaseModel):
    tenancy_id: UUID
    amount: float
    due_date: date
    status: PaymentStatus

class BillSchema(BaseSchema):
    tenancy_id: UUID
    amount: float
    due_date: date
    status: PaymentStatus

    class Config:
        from_attributes = True

#Payment Schema
class PaymentCreateSchema(BaseModel):
    bill_id: UUID
    amount_paid: float
    payment_date: datetime
    payment_method: str
    transaction_id: str
    status: PaymentStatus

class PaymentSchema(BaseSchema):
    bill_id: UUID
    amount_paid: float
    payment_date: datetime
    payment_method: str
    transaction_id: str
    status: PaymentStatus

# Employee Schemas
class EmployeeCreateSchema(BaseModel):
    first_name: str
    middle_name: Optional[str]
    last_name: str
    title: Optional[str] = Title.other.value
    gender: Optional[str] = Gender.other.value
    date_of_birth: Optional[date]
    marital_status: Optional[str] = MaritalStatus.other.value
    email: EmailStr
    contact_info: Optional[Dict]
    hire_date: Optional[date]
    termination_date: Optional[date]
    is_active: Optional[bool] = True
    custom_data: Optional[Dict]
    profile_image_path: Optional[str]
    organization_id: UUID


    @model_validator(mode="before")
    def parse_json_if_string(cls, values):
        if isinstance(values, str):
            try:
                return json.loads(values)
            except Exception as e:
                raise ValueError("Invalid JSON provided") from e
        return values

class EmployeeSchema(BaseSchema):
    first_name: str
    middle_name: Optional[str]
    last_name: str
    title: Optional[str] = Title.other.value
    gender: Optional[str] = Gender.other.value
    date_of_birth: Optional[date]
    marital_status: Optional[str] = MaritalStatus.other.value
    email: EmailStr
    contact_info: Optional[Dict]
    hire_date: Optional[date]
    termination_date: Optional[date]
    is_active: Optional[bool]
    custom_data: Optional[Dict]
    profile_image_path: Optional[str]
    organization_id: UUID


    class Config:
        from_attributes = True

# Academic Qualification Schemas
class AcademicQualificationCreateSchema(BaseModel):
    employee_id: UUID
    degree: str
    institution: str
    year_obtained: int
    details: Optional[Dict] = {}
    certificate_path: Optional[str]

    @field_validator("year_obtained")
    def validate_year_obtained(cls, value):
        current_year = datetime.now().year
        if not (1900 <= value <= current_year):
            raise ValueError("Year obtained must be between 1900 and the current year")
        return value


class AcademicQualificationSchema(BaseSchema):
    employee_id: UUID
    degree: str
    institution: str
    year_obtained: int
    details: Optional[Dict]
    certificate_path: Optional[str]





# Professional Qualification Schemas
class ProfessionalQualificationCreateSchema(BaseModel):
    employee_id: UUID
    qualification_name: str
    institution: str
    year_obtained: int
    details: Optional[Dict] = {}
    license_path: Optional[str]

    @field_validator("year_obtained")
    def validate_year_obtained(cls, value):
        current_year = datetime.now().year
        if not (1900 <= value <= current_year):
            raise ValueError("Year obtained must be between 1900 and the current year")
        return value

# Professional Qualification Schemas
class ProfessionalQualificationSchema(BaseSchema):
    employee_id: UUID
    qualification_name: str
    institution: str
    year_obtained: int
    details: Optional[Dict]
    license_path: Optional[str]

# Employment History Schemas
class EmploymentHistoryCreateSchema(BaseModel):
    employee_id: UUID
    job_title: str
    company: str
    start_date: date
    end_date: Optional[date]
    details: Optional[Dict] = {}
    documents_path: Optional[str]

    @field_validator("end_date")
    def validate_end_date(cls, value, values):
        start_date = values.get("start_date")
        if value and start_date and value < start_date:
            raise ValueError("End date cannot be earlier than the start date")
        return value
    

# Employment History Schemas
class EmploymentHistorySchema(BaseSchema):
    employee_id: UUID
    job_title: str
    company: str
    start_date: date
    end_date: Optional[date]
    details: Optional[Dict]
    documents_path: Optional[str]


# Emergency Contact Schemas
class EmergencyContactCreateSchema(BaseModel):
    employee_id: UUID
    name: str
    relation: str
    phone: str
    address: Optional[str]
    details: Optional[Dict] = {}

    @field_validator("phone")
    def validate_phone(cls, value):
        if len(value) < 10 or not value.isdigit():
            raise ValueError("Phone number must be at least 10 digits and numeric")
        return value
    

class EmergencyContactSchema(BaseSchema):
    employee_id: UUID
    name: str
    relation: str
    phone: str
    address: Optional[str]
    details: Optional[Dict]


# Next of Kin Schemas
class NextOfKinCreateSchema(BaseModel):
    employee_id: UUID
    name: str
    relation: str
    phone: str
    address: Optional[str]
    details: Optional[Dict] = {}

    @field_validator("phone")
    def validate_phone(cls, value):
        if len(value) < 10 or not value.isdigit():
            raise ValueError("Phone number must be at least 10 digits and numeric")
            
        return value

    class NextOfKinSchema(BaseSchema):
        employee_id: UUID
        name: str
        relation: str
        phone: str
        address: Optional[str]
        details: Optional[Dict]



# Employment History Schemas
class EmploymentHistoryCreateSchema(BaseModel):
    employee_id: UUID
    job_title: str
    company: str
    start_date: date
    end_date: Optional[date]
    details: Optional[Dict] = {}
    documents_path: Optional[str]

    @field_validator("end_date")
    def validate_end_date(cls, value, values):
        start_date = values.get("start_date")
        if value and start_date and value < start_date:
            raise ValueError("End date cannot be earlier than the start date")
        return value

class EmploymentHistorySchema(BaseSchema):
    employee_id: UUID
    job_title: str
    company: str
    start_date: date
    end_date: Optional[date]
    details: Optional[Dict]
    documents_path: Optional[str]

# Next of Kin Schemas
class NextOfKinSchema(BaseSchema):
    employee_id: UUID
    name: str
    relation: str
    phone: str
    address: Optional[str]
    details: Optional[Dict]

# File Storage Schema
class FileStorageSchema(BaseSchema):
    file_name: str
    file_path: str
    file_type: str
    uploaded_by_id: Optional[UUID]
    record_id: UUID
    record_type: str
    organization_id: UUID

# Audit Log Schema
class AuditLogSchema(BaseSchema):
    action: str
    table_name: str
    record_id: UUID
    performed_by: Optional[UUID]
    timestamp: datetime


# System Setting Schema
class SystemSettingCreateSchema(BaseModel):
    setting_name: str
    setting_value: Dict
    organization_id: Optional[UUID] 

class SystemSettingSchema(BaseSchema):
    setting_name: str
    setting_value: Dict
    organization_id: Optional[UUID] 

    class Config:
        from_attributes = True

# Dashboard Schema
class DashboardCreateSchema(BaseModel):
    dashboard_name: str
    dashboard_data: Dict
    access_url: str
    organization_id: UUID


class DashboardSchema(BaseSchema):
    dashboard_name: str
    dashboard_data: Dict
    access_url: str
    organization_id: UUID


    class Config:
        from_attributes = True


class DataCreateBankSchema(BaseModel):
    data_name: str
    data: Union[Dict, List]  # Accepts both dictionary and list
    # organization_id: Optional[UUID] = None

    # class Config:
    #     from_attributes = True


class DataBankSchema(BaseSchema):
    data_name: str
    data:  Union[Dict, List]
    # organization_id: Optional[UUID] = None


    class Config:
        from_attributes = True




# Nested Schemas Example
class OrganizationDetailSchema(OrganizationSchema):
    users: List[UserSchema] = []
    roles: List[RoleSchema] = []
    settings: List[SystemSettingSchema] = []
