import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


logger = logging.getLogger(__name__)

# Configuration from environment variables
EXCEL_FILE_NAME = os.getenv("EXCEL_FILE_NAME", "sample_staff_records.xlsx")
BASE_DIR = Path(__file__).resolve().parent
FILE_PATH = BASE_DIR / EXCEL_FILE_NAME



router = APIRouter()


@router.get(
    "/download-excel",
    summary="Download the Excel file",
    response_description="The Excel file"
)
async def download_excel():
    logger.info("Download request received for file: %s", FILE_PATH)
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