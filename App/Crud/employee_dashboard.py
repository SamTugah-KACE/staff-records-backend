import logging
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from Models.models import (
    Employee, AcademicQualification, ProfessionalQualification, EmploymentHistory,
    EmergencyContact, NextOfKin, EmployeePaymentDetail, SalaryPayment, PromotionRequest
)
from Schemas.schemas import EmployeeDashboardSchema


def get_employee_dashboard_info(db: Session, employee_id: UUID) -> EmployeeDashboardSchema:
    employee_query = (
        db.query(
            Employee,
            AcademicQualification,
            ProfessionalQualification,
            EmploymentHistory,
            EmergencyContact,
            NextOfKin,
            EmployeePaymentDetail,
            SalaryPayment,
            PromotionRequest,
        )
        # join & loads
        .options(
            joinedload(Employee.rank),
            joinedload(Employee.employee_type),
            joinedload(Employee.department),
        )
        # joins
        .outerjoin(AcademicQualification, AcademicQualification.employee_id == Employee.id)
        .outerjoin(ProfessionalQualification, ProfessionalQualification.employee_id == Employee.id)
        .outerjoin(EmploymentHistory, EmploymentHistory.employee_id == Employee.id)
        .outerjoin(EmergencyContact, EmergencyContact.employee_id == Employee.id)
        .outerjoin(NextOfKin, NextOfKin.employee_id == Employee.id)
        .outerjoin(EmployeePaymentDetail, EmployeePaymentDetail.employee_id == Employee.id)
        .outerjoin(SalaryPayment, SalaryPayment.employee_id == Employee.id)
        .outerjoin(PromotionRequest, PromotionRequest.employee_id == Employee.id)
        # filters
        .filter(Employee.id == employee_id)
        .first()
    )

    logging.info("employee query here")
    logging.info(employee_query)
    (
        bio_data,
        academic_qualifications,
        professional_qualifications,
        employment_histories,
        emergency_contacts,
        next_of_kins,
        employee_payment_details,
        salary_payments,
        promotion_requests,
    ) = employee_query

    qualifications = dict()  # todo

    employment_details = dict()
    if bio_data.employee_type: employment_details['employee_type'] = dict(
        type_code=bio_data.employee_type.type_code,
        description=bio_data.employee_type.description,
        default_criteria=bio_data.employee_type.default_criteria,
    )
    print("bio_data.rank here", bio_data.rank)
    if bio_data.rank: employment_details['rank'] = dict(
        id= bio_data.rank.id,
        organization_id=bio_data.rank.organization_id,
        name=bio_data.rank.name,
        min_salary=bio_data.rank.min_salary,
        max_salary=bio_data.rank.max_salary,
        currency=bio_data.rank.currency,
        conversion_info=bio_data.rank.conversion_info,
    )
    if bio_data.department: employment_details['department'] = dict(
        id= bio_data.department.id,
        organization_id=bio_data.department.organization_id,
        name=bio_data.department.name,
        branch_id=bio_data.department.branch_id,
        department_head=bio_data.department.department_head_id
    )
    employment_details['dynamic_models'] = None
    response = dict(
        bio_data=bio_data,
        qualifications=qualifications,
        employment_history=None,
        emergency_contacts=None,
        next_of_kins=None,
        payment_details=None,
        salary_payments=None,
        promotion_requests=None,
        employment_details=employment_details,
    )
    return EmployeeDashboardSchema(**response)
