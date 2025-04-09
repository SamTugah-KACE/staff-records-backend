# dashboard_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from Crud.crud_dashboard import (
    create_dashboard,
    update_dashboard,
    get_dashboards_by_org,
    get_dashboard_by_id,
    compileDynamicSubmitCode,
)
from Schemas.schemas import DashboardCreateSchema, DashboardSchema
from Crud.auth import get_db, require_permissions  # RBAC dependency from earlier

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])

@router.post("/", response_model=DashboardSchema, status_code=status.HTTP_201_CREATED)
async def create_dashboard_endpoint(
    dashboard_in: DashboardCreateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions(["employee:create:dashboard"]))
):
    """
    Create a new dashboard entry.
    
    Only users with permission `role:manage_dashboard` (or an equivalent) can create a dashboard.
    """
    try:
        form_design = dashboard_in.dashboard_data  # Expecting a dict with "fields"
        form_fields = form_design.get("fields", [])
        # Obtain the API URL from configuration or prefetch logic:
        api_url = f"https://staff-records-backend.onrender.com/api/organizations/create-url"
        compiledCode = compileDynamicSubmitCode(form_fields, api_url)
        form_design["submitCode"] = compiledCode
        dashboard_in.dashboard_data = form_design
        new_dashboard = create_dashboard(db, dashboard_in)
        return new_dashboard
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create dashboard: {str(e)}"
        )

@router.put("/{dashboard_id}", response_model=DashboardSchema, status_code=status.HTTP_200_OK)
async def update_dashboard_endpoint(
    dashboard_id: UUID = Path(..., description="ID of the dashboard to update"),
    updated_data: dict = None,  # Can also create a dedicated update schema for validations
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions(["employee:update:dashboard"]))
):
    """
    Update an existing dashboard.
    
    Only users with appropriate permissions can update dashboard settings.
    """
    try:
        
        updated_dashboard = update_dashboard(db, dashboard_id, updated_data)
        return updated_dashboard
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update dashboard: {str(e)}"
        )

@router.get("/", response_model=List[DashboardSchema], status_code=status.HTTP_200_OK)
async def list_dashboards(
    organization_id: UUID = Query(..., description="Organization id to fetch dashboards for"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions(["dashboard:view"]))
):
    """
    Retrieve all dashboards for a specific organization.
    """
    try:
        
        dashboards = get_dashboards_by_org(db, organization_id)
        return dashboards
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboards: {str(e)}"
        )

@router.get("/{dashboard_id}", response_model=DashboardSchema, status_code=status.HTTP_200_OK)
async def get_dashboard_endpoint(
    dashboard_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions(["employee:read:dashboard"]))
):
    """
    Retrieve a dashboard by ID.
    """
    try:
        
        dashboard = get_dashboard_by_id(db, dashboard_id)
        return dashboard
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard: {str(e)}"
        )
