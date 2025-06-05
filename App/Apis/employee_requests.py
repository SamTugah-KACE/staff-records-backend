# src/api/employee_data_inputs.py
import json
from typing import List
from uuid import UUID
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from Service.storage_service import BaseStorage
from database.db_session import get_db
from Crud import employee_data_input
from Schemas import schemas
# from Utils.security import get_current_active_user, get_current_active_admin
from Utils.storage_utils import get_storage_service

router = APIRouter(prefix="/employee-data-inputs", tags=["Employee Data Inputs"])

@router.post(
    "/",
    response_model=schemas.EmployeeDataInput,
    status_code=status.HTTP_201_CREATED
)
async def create_input(
    employee_id: str = Form(...),
    organization_id: str = Form(...),
    data_type: str = Form(...),
    request_type: str = Form(...),
    data: str = Form(...),                    # JSON string
    files: List[UploadFile] = File(None),       # optional attachments
    db: Session = Depends(get_db),
    storage: BaseStorage = Depends(get_storage_service),
    # current_user=Depends(deps.get_current_active_user),
):
    # obj_in = schemas.EmployeeDataInputCreate(
    #     employee_id=employee_id,
    #     data_type=data_type,
    #     request_type=request_type,
    #     data=schemas.parse_raw_as(schemas.Any, data)  # parse JSON
    # )
    # return employee_data_input.create_data_input(db=db, organization_id=organization_id, obj_in=obj_in, files=files, storage=storage)

    # parse the incoming JSON string into a native Python object
    try:
        data_dict = json.loads(data)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`data` must be a valid JSON string"
        )
    print("\n\ndata_dict", data_dict)
    print("\n\nfiles", files)
    obj_in = schemas.EmployeeDataInputCreate(
        employee_id=employee_id,
        organization_id=UUID(organization_id),
        data_type=data_type,
        request_type=request_type,
        data=data_dict
    )

    return await employee_data_input.create_or_update_data_input(
         db=db,
         organization_id=organization_id,
         obj_in=obj_in,
         files=files,
         storage=storage
     )


# @router.post(
#     "/",
#     response_model=schemas.EmployeeDataInput,
#     status_code=status.HTTP_201_CREATED,
# )
# async def create_input(
#     *,
#     obj_in: schemas.EmployeeDataInputCreate = Body(...),
#     files: List[UploadFile] = File([]),
#     db: Session = Depends(get_db),
#     storage=Depends(get_storage_service),
# ):
#     # obj_in now has all five required fields
#     return employee_data_input.create_data_input(
#         db=db,
#         organization_id=str(obj_in.organization_id),
#         obj_in=obj_in,
#         files=files,
#         storage=storage
#     )


@router.get(
    "/",
    response_model=List[schemas.EmployeeDataInput]
)
def list_data_inputs(
    employee_id: UUID = Query(..., description="Filter by employee_id"),
    db: Session = Depends(get_db),
):
    # Return all change‐requests for that employee
    return employee_data_input.get_data_inputs_by_employee_order_by_date(db, employee_id)


@router.get(
    "/{id}",
    response_model=schemas.EmployeeDataInput
)
def read_input(
    id: str,
    db: Session = Depends(get_db),
):
    db_obj = employee_data_input.get_data_input(db, id)
    print("db_obj", db_obj)
    # Check if the object exists or is None
    # If it doesn't exist, raise an HTTPException with a 404 status code
    # if db_obj is None: return {}
    if not db_obj:
        # ⚠️ must *raise* the exception, not return it
        raise HTTPException(status_code=404, detail=" Data input Not found")
    return db_obj


# @router.get(
#     "/",
#     response_model=List[schemas.EmployeeDataInput]
# )
# def read_inputs(
#     skip: int = 0,
#     limit: int = 100,
#     db: Session = Depends(get_db),
#     # current_user=Depends(deps.get_current_active_user),
# ):
#     return employee_data_input.get_data_inputs(db, skip=skip, limit=limit)


@router.patch(
    "/{id}",
    response_model=schemas.EmployeeDataInput
)
def update_input(
    id: str,
    obj_in: schemas.EmployeeDataInputUpdate,
    db: Session = Depends(get_db),
    # current_user=Depends(deps.get_current_active_admin),
):
    return employee_data_input.update_data_input(db=db, id=id, obj_in=obj_in)

@router.delete(
    "/{id}",
    response_model=schemas.EmployeeDataInput
)
def delete_input(
    id: str,
    db: Session = Depends(get_db),
    # current_user=Depends(deps.get_current_active_admin),
):
    return employee_data_input.delete_data_input(db, id)
