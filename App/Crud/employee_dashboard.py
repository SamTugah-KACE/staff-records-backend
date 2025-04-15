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
    employment_details = dict(
        employee_type=bio_data.employee_type,
        rank=bio_data.rank,
        department=bio_data.department,
        dynamic_models=None,
    )
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
