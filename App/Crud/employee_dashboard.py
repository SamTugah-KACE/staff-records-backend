from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from Models.models import Employee, SalaryPayment, PromotionRequest
from Schemas.schemas import EmployeeDashboardSchema


def get_employee_dashboard_info(db: Session, employee_id: UUID) -> EmployeeDashboardSchema:
    employee_query = (
        db.query(Employee)
        .options(
            joinedload(Employee.rank),
            joinedload(Employee.employee_type),
            joinedload(Employee.department),
            joinedload(Employee.dynamic_data),
            joinedload(Employee.academic_qualifications),
            joinedload(Employee.professional_qualifications),
            joinedload(Employee.employment_history),
            joinedload(Employee.emergency_contacts),
            joinedload(Employee.next_of_kins),
            joinedload(Employee.payment_details),
        )
        .filter(Employee.id == employee_id)
        .first()
    )

    response = dict(
        bio_data=employee_query,
        qualifications=dict(
            academic_qualifications=employee_query.academic_qualifications,
            professional_qualifications=employee_query.professional_qualifications,
        ),
        employment_history=employee_query.employment_history,
        emergency_contacts=employee_query.emergency_contacts,
        next_of_kins=employee_query.next_of_kins,
        payment_details=employee_query.payment_details,
        salary_payments=db.query(SalaryPayment).filter(SalaryPayment.employee_id == employee_id).all(),
        promotion_requests=db.query(PromotionRequest).filter(PromotionRequest.employee_id == employee_id).all(),
        employment_details=dict(),
    )

    # build employment details payload
    if employee_query.employee_type: response['employment_details']['employee_type'] = dict(
        type_code=employee_query.employee_type.type_code,
        description=employee_query.employee_type.description,
        default_criteria=employee_query.employee_type.default_criteria,
    )
    if employee_query.rank: response['employment_details']['rank'] = dict(
        id=employee_query.rank.id,
        organization_id=employee_query.rank.organization_id,
        name=employee_query.rank.name,
        min_salary=employee_query.rank.min_salary,
        max_salary=employee_query.rank.max_salary,
        currency=employee_query.rank.currency,
        conversion_info=employee_query.rank.conversion_info,
    )
    if employee_query.department: response['employment_details']['department'] = dict(
        id=employee_query.department.id,
        organization_id=employee_query.department.organization_id,
        name=employee_query.department.name,
        branch_id=employee_query.department.branch_id,
        department_head=employee_query.department.department_head_id
    )
    if employee_query.dynamic_data: response['employment_details']['dynamic_models'] = [dict(
        data_category=i.data_category,
        data=i.data,
    ) for i in employee_query.dynamic_data]

    return EmployeeDashboardSchema(**response)
