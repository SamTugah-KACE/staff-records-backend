# crud_dashboard.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

from Models.models import Dashboard
from Schemas.schemas import DashboardCreateSchema

def create_dashboard(db: Session, dashboard_in: DashboardCreateSchema) -> Dashboard:
    """
    Create a new dashboard record for the given organization.
    """
    new_dashboard = Dashboard(**dashboard_in.dict())
    db.add(new_dashboard)
    db.commit()
    db.refresh(new_dashboard)
    return new_dashboard

def update_dashboard(db: Session, dashboard_id: UUID, updated_data: dict) -> Dashboard:
    """
    Update an existing dashboard record with partial or full changes.
    """
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise ValueError("Dashboard not found")
    for key, value in updated_data.items():
        setattr(dashboard, key, value)
    db.commit()
    db.refresh(dashboard)
    return dashboard

def get_dashboards_by_org(db: Session, organization_id: UUID):
    """
    Retrieve all dashboards for the specified organization.
    """
    dashboards = db.query(Dashboard).filter(
        Dashboard.organization_id == organization_id
    ).all()
    return dashboards

def get_dashboard_by_id(db: Session, dashboard_id: UUID) -> Dashboard:
    """
    Retrieve a specific dashboard by its ID.
    """
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise ValueError("Dashboard not found")
    return dashboard
