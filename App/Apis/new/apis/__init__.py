from fastapi import APIRouter

from Apis.new.apis.academic_qualification import academic_qualification_router
from Apis.new.apis.department import department_router
from Apis.new.apis.emergency_contact import emergency_contact_router
from Apis.new.apis.employee_dynamic_data import employee_dynamic_data_router
from Apis.new.apis.employee_payment_details import employee_payment_details_router
from Apis.new.apis.employee_type import employee_type_router
from Apis.new.apis.next_of_kin import next_of_kin_router
from Apis.new.apis.professional_qualification import professional_qualification_router
from Apis.new.apis.promotion_request import promotion_request_router
from Apis.new.apis.salary_payment import salary_payment_router

employee_specific_routers = APIRouter()

employee_specific_routers.include_router(academic_qualification_router, tags=["Academic Qualification"])
employee_specific_routers.include_router(emergency_contact_router, tags=["Emergency Contact"])
employee_specific_routers.include_router(employee_dynamic_data_router, tags=["Employee Dynamic Data"])
employee_specific_routers.include_router(next_of_kin_router, tags=["Next Of Kin"])
employee_specific_routers.include_router(professional_qualification_router, tags=["Professional Qualification"])
