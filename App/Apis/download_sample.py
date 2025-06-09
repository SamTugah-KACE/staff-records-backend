import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from Models.Tenants.organization import Organization
from database.db_session import get_db


logger = logging.getLogger(__name__)

# Configuration from environment variables
EXCEL_FILE_NAME = os.getenv("EXCEL_FILE_NAME", "sample_staff_records.xlsx")
EXCEL_FILE_NAME_SINGLE = os.getenv("EXCEL_FILE_NAME_SINGLE", "sample_staff_recordS_.xlsx")
BASE_DIR = Path(__file__).resolve().parent
FILE_PATH = BASE_DIR / EXCEL_FILE_NAME



router = APIRouter()


@router.get(
    "/sample-file/{organization_id}",
    # response_class=FileResponse,
    tags=["Download Sample File"],
    summary="Download the Excel file",
    response_description="The Excel file"
)
async def download_excel(
    organization_id: str,  # Assuming organization_id is a string, adjust as necessary
    db: Session = Depends(get_db),  # Uncomment if you need database access
    # current_user: dict = Depends(require_permissions(["hr:dashboard:read"]))  # Uncomment if you need user permissions
):
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        logger.error("Organization not found: %s", organization_id)
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if org.nature.strip().lower() == "single managed":
        logger.info("Serving single organization file: %s", EXCEL_FILE_NAME_SINGLE)
        FILE_PATH = BASE_DIR / EXCEL_FILE_NAME_SINGLE
    else:
        logger.info("Serving multi-organization file: %s", EXCEL_FILE_NAME)
        FILE_PATH = BASE_DIR / EXCEL_FILE_NAME
    
    logger.info("Download request received for file: %s", FILE_PATH)


    # Check if the file exists
    if not FILE_PATH.exists():
        logger.error("File not found: %s", FILE_PATH)
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        logger.info("Serving file: %s", FILE_PATH)
        return FileResponse(
            path=str(FILE_PATH),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=EXCEL_FILE_NAME
        )
    except Exception as e:
        logger.exception("Error while sending the file: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error") from e