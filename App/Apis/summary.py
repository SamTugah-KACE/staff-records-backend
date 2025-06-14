import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from database.db_session import SessionLocal, get_db
from Models.models import ( Department, User, Employee)
from Models.Tenants.organization import (Organization, Branch, Rank, PromotionPolicy, Tenancy, Bill, Payment)
from Models.Tenants.role import Role
from Schemas.schemas import OrganizationSummarySchema, SummaryCounts, OrganizationSchema, OrganizationCountSummarySchema
from notification.socket import manager


router = APIRouter(prefix="/organizations", tags=["Summary"])


# def push_summary_update(db: Session, org_id: UUID):
#      # Compute counts
#     branch_ct   = db.query(Branch).filter(Branch.organization_id == org_id).count()
#     dept_ct     = db.query(Department).filter(Department.organization_id == org_id).count()
#     rank_ct     = db.query(Rank).filter(Rank.organization_id == org_id).count()
#     role_ct     = db.query(Role).filter(Role.organization_id == org_id).count()
#     user_ct     = db.query(User).filter(User.organization_id == org_id).count()
#     emp_ct      = db.query(Employee).filter(Employee.organization_id == org_id).count()
#     policy_ct   = db.query(PromotionPolicy).filter(PromotionPolicy.organization_id == org_id).count()
#     tenancy_ct  = db.query(Tenancy).filter(Tenancy.organization_id == org_id).count()
    
#     bill_ct     = (
#         db.query(Bill)
#           .join(Tenancy, Bill.tenancy_id == Tenancy.id)
#             .filter(Tenancy.organization_id == org_id)
#             .count()
#     )
#     payment_ct  = (
#         db.query(Payment)
#           .join(Bill, Payment.bill_id == Bill.id)
#           .join(Tenancy, Bill.tenancy_id == Tenancy.id)
#             .filter(Tenancy.organization_id == org_id)
#             .count()
#     )
#     # counts = SummaryCounts(
#     #     branches=branch_ct,
#     #     departments=dept_ct,
#     #     ranks=rank_ct,
#     #     roles=role_ct,
#     #     users=user_ct,
#     #     employees=emp_ct,
#     #     promotion_policies=policy_ct,
#     #     tenancies=tenancy_ct,
#     #     bills=bill_ct,
#     #     payments=payment_ct
#     # )
#     counts = {
#       "branches":   branch_ct,
#       "departments":dept_ct,
#       "ranks": rank_ct,
#       "roles":role_ct,
#       "users": user_ct,
#       "employees": emp_ct,
#       "promotion_policies": policy_ct,
#       "tenancies": tenancy_ct,
#       "bills":bill_ct,
#       "payments": payment_ct 

#       # … all your other counts …
#     }
#     # broadcast to every HR summary socket in that org
#     # manager.broadcast_json(str(org_id), {"type":"update", "payload": {"counts": counts}})
#     manager.broadcast(
#       str(org_id),
#       json.dumps({"type":"update", "payload": {"counts": counts}})
#     )

# === 1️⃣  Sync helper, for push_summary_update  ===
def build_summary_payload_sync(db: Session, org_id: UUID):
    """
    Helper function to build the summary payload for an organization.
    This is used in the WebSocket endpoint to send the initial summary.
    """
    # Fetch the organization
    org = db.query(Organization).get(org_id)
    print("Building summary for org, org object:", org)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Compute counts
    branch_ct   = db.query(Branch).filter(Branch.organization_id == org_id).count()
    dept_ct     = db.query(Department).filter(Department.organization_id == org_id).count()
    rank_ct     = db.query(Rank).filter(Rank.organization_id == org_id).count()
    role_ct     = db.query(Role).filter(Role.organization_id == org_id).count()
    user_ct     = db.query(User).filter(User.organization_id == org_id).count()
    emp_ct      = db.query(Employee).filter(Employee.organization_id == org_id).count()
    policy_ct   = db.query(PromotionPolicy).filter(PromotionPolicy.organization_id == org_id).count()
    tenancy_ct  = db.query(Tenancy).filter(Tenancy.organization_id == org_id).count()
    
    bill_ct     = (
        db.query(Bill)
          .join(Tenancy, Bill.tenancy_id == Tenancy.id)
            .filter(Tenancy.organization_id == org_id)
            .count()
    )
    payment_ct  = (
        db.query(Payment)
          .join(Bill, Payment.bill_id == Bill.id)
          .join(Tenancy, Bill.tenancy_id == Tenancy.id)
            .filter(Tenancy.organization_id == org_id)
            .count()
    )
   
    counts = {
      "branches":   branch_ct,
      "departments":dept_ct,
      "ranks": rank_ct,
      "roles":role_ct,
      "users": user_ct,
      "employees": emp_ct,
      "promotion_policies": policy_ct,
      "tenancies": tenancy_ct,
      "bills":bill_ct,
      "payments": payment_ct 

      # … all your other counts …
    }

    return{"counts": counts}


async def _build_summary_payload(db: Session, org_id: UUID):
    """
    Helper function to build the summary payload for an organization.
    This is used in the WebSocket endpoint to send the initial summary.
    """
    # Fetch the organization
    org = db.query(Organization).get(org_id)
    print("Building summary for org, org object:", org)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Compute counts
    branch_ct   = db.query(Branch).filter(Branch.organization_id == org_id).count()
    dept_ct     = db.query(Department).filter(Department.organization_id == org_id).count()
    rank_ct     = db.query(Rank).filter(Rank.organization_id == org_id).count()
    role_ct     = db.query(Role).filter(Role.organization_id == org_id).count()
    user_ct     = db.query(User).filter(User.organization_id == org_id).count()
    emp_ct      = db.query(Employee).filter(Employee.organization_id == org_id).count()
    policy_ct   = db.query(PromotionPolicy).filter(PromotionPolicy.organization_id == org_id).count()
    tenancy_ct  = db.query(Tenancy).filter(Tenancy.organization_id == org_id).count()
    
    bill_ct     = (
        db.query(Bill)
          .join(Tenancy, Bill.tenancy_id == Tenancy.id)
            .filter(Tenancy.organization_id == org_id)
            .count()
    )
    payment_ct  = (
        db.query(Payment)
          .join(Bill, Payment.bill_id == Bill.id)
          .join(Tenancy, Bill.tenancy_id == Tenancy.id)
            .filter(Tenancy.organization_id == org_id)
            .count()
    )
    # counts = SummaryCounts(
    #     branches=branch_ct,
    #     departments=dept_ct,
    #     ranks=rank_ct,
    #     roles=role_ct,
    #     users=user_ct,
    #     employees=emp_ct,
    #     promotion_policies=policy_ct,
    #     tenancies=tenancy_ct,
    #     bills=bill_ct,
    #     payments=payment_ct
    # )

    counts = {
      "branches":   branch_ct,
      "departments":dept_ct,
      "ranks": rank_ct,
      "roles":role_ct,
      "users": user_ct,
      "employees": emp_ct,
      "promotion_policies": policy_ct,
      "tenancies": tenancy_ct,
      "bills":bill_ct,
      "payments": payment_ct 

      # … all your other counts …
    }
    # return OrganizationSummarySchema(
    #     organization=OrganizationSchema.from_orm(org),
    #     counts=counts
    # )
    # manager.broadcast(
    #   str(org_id),
    #   json.dumps({"type":"update", "payload": {"counts": counts}})
    # )
    return counts
    # return OrganizationCountSummarySchema(
    #     counts=counts
    # )

# === 2️⃣  Async helper, for your WS initial send  ===
async def build_summary_payload_async(db: Session, org_id: UUID) -> dict:
    # you can simply wrap the sync version in a threadpool so you don't block the loop:
    from anyio import to_thread
    return await to_thread.run_sync(build_summary_payload_sync, db, org_id)


# def push_summary_update(organization_id):
#     """Sync background task to rebuild summary and broadcast it."""
#     db = SessionLocal()
#     try:
#         payload = _build_summary_payload(db, organization_id)
#         if payload is None:
#             return
#         message = json.dumps({"type": "update", "payload": payload})
#         manager.broadcast(str(organization_id), message)
#     finally:
#         db.close()



def push_summary_update(organization_id):
     """Sync background task to rebuild summary and broadcast it."""
     db = SessionLocal()
     try:
        payload = build_summary_payload_sync(db, organization_id)
        if not payload:
             return
        manager.broadcast(str(organization_id), json.dumps({
             "type": "update",
            "payload": payload
         }))
     finally:
         db.close()

# async def push_summary_update(db: Session, org_id: UUID):
#     counts_payload = await _build_summary_payload(db, org_id)  # returns {"counts": {...}}
#     message = {"type": "update", "payload": counts_payload}
#     # Use our helper which wraps send_json
#     # asyncio.create_task(manager.broadcast_json(str(org_id), message))
#     # This will actually await send_json on *all* sockets
#     await manager.broadcast_json(str(org_id), message)



@router.get("/{org_id}/summary", response_model=OrganizationCountSummarySchema)
def get_organization_summary(
    org_id: UUID,
    db: Session = Depends(get_db)
):
    # 1. Fetch the org (will be serialized via OrganizationSchema)
    org = db.query(Organization).get(org_id)
    if not org:
        raise HTTPException(404, detail="Organization not found")

    # 2. Compute all the counts
    #    We filter each model by organization_id
    branch_ct   = db.query(Branch).filter(Branch.organization_id == org_id).count()
    dept_ct     = db.query(Department).filter(Department.organization_id == org_id).count()
    rank_ct     = db.query(Rank).filter(Rank.organization_id == org_id).count()
    role_ct     = db.query(Role).filter(Role.organization_id == org_id).count()
    user_ct     = db.query(User).filter(User.organization_id == org_id).count()
    emp_ct      = db.query(Employee).filter(Employee.organization_id == org_id).count()
    policy_ct   = db.query(PromotionPolicy).filter(PromotionPolicy.organization_id == org_id).count()
    tenancy_ct  = db.query(Tenancy).filter(Tenancy.organization_id == org_id).count()
    # bills/payments join through tenancy → bill → payment
    bill_ct     = (
        db.query(Bill)
          .join(Tenancy, Bill.tenancy_id == Tenancy.id)
          .filter(Tenancy.organization_id == org_id)
          .count()
    )
    payment_ct  = (
        db.query(Payment)
          .join(Bill, Payment.bill_id == Bill.id)
          .join(Tenancy, Bill.tenancy_id == Tenancy.id)
          .filter(Tenancy.organization_id == org_id)
          .count()
    )

    counts = SummaryCounts(
        branches=branch_ct,
        departments=dept_ct,
        ranks=rank_ct,
        roles=role_ct,
        users=user_ct,
        employees=emp_ct,
        promotion_policies=policy_ct,
        tenancies=tenancy_ct,
        bills=bill_ct,
        payments=payment_ct
    )

    # return OrganizationSummarySchema(
    #     organization=org,
    #     counts=counts
    # )

    return OrganizationCountSummarySchema(counts=counts)
    # return counts
