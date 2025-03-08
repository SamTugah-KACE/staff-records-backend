import json
from sqlalchemy.dialects.postgresql import  JSONB
from sqlalchemy.orm import  Session
from sqlalchemy.exc import SQLAlchemyError
from database.db_session import BaseModel
from Models.models import DataBank
import logging
from datetime import datetime
from fastapi import FastAPI, APIRouter, Depends, HTTPException, BackgroundTasks, Query, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID 
from typing import List, Optional
from database.db_session import get_db  # Your database session dependency
from Crud.crud import CRUDBase as crud # Generic CRUD class
from Models.models import DataBank  # Import your models
from Schemas.schemas import DataBankSchema, DataCreateBankSchema  # Import your Pydantic schemas




# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)





def create_default_roles(db: Session):
    """
    Efficiently seeds default roles into the databank table.
    Ensures atomicity, handles duplicates, and appends new roles to the existing structure.
    """
    roles = [
        {"name": "Admin", "permissions": {"admin": True}},
        {"name": "User", "permissions": {"admin": False}},
    ]

    try:
        print("\n\ndb:: ", db)
        print("\n\nDatabank:: ", DataBank)
        with db.begin():  # Begin a transaction
            # Fetch or create the databank entry for roles
            databank_entry = db.query(DataBank).filter(DataBank.data_name == "roles").first()
            print("databank_entry:: ", databank_entry)
            if not databank_entry:
                # If no existing entry, create a new one
                databank_entry = DataBank(data_name="roles", data=roles)
                db.add(databank_entry)
            else:
                # Check for duplicates and append new roles
                existing_roles = databank_entry.data
                new_roles = [
                    role for role in roles
                    if not any(existing_role["name"] == role["name"] for existing_role in existing_roles)
                ]
                if new_roles:
                    databank_entry.data.extend(new_roles)  # Append only unique roles

            # Commit changes
            db.commit()
            logger.info("Default roles seeded successfully.")

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"An error occurred while seeding default roles: {str(e)}")
        raise RuntimeError("Failed to seed default roles. Please check the logs.") from e
    

app = APIRouter()



from sqlalchemy.ext.mutable import MutableList

@app.post("/data-bank/", response_model=DataCreateBankSchema, status_code=status.HTTP_201_CREATED)
async def create_data_bank(
    data_name: str = Form(...),
    data: str = Form(...),  # Accept JSON string from form data
    db: Session = Depends(get_db),
):
    """
    Dynamic API to create or update entries in the DataBank table.
    Ensures uniqueness for incoming data and appends to existing data if the data_name exists.
    If the data_name does not exist, it creates a new entry.
    """
    try:
        # Parse `data` string into a dictionary or list
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid data format. Expected a valid JSON string.",
            )

        # Ensure parsed_data is a list for uniform processing
        if not isinstance(parsed_data, list):
            parsed_data = [parsed_data]

        # Fetch the databank entry for the given data_name
        databank_entry = db.query(DataBank).filter(DataBank.data_name == data_name).first()

        if databank_entry:
            # Debugging: Ensure data is correctly initialized
            if databank_entry.data is None:
                databank_entry.data = []

            # Debugging: Check data types and contents
            logger.debug(f"Existing data: {databank_entry.data}")
            logger.debug(f"New data: {parsed_data}")

            # Append only unique entries to the existing data
            def dict_to_tuple(d):
                return tuple(sorted((k, dict_to_tuple(v) if isinstance(v, dict) else v) for k, v in d.items()))

            existing_set = {dict_to_tuple(entry) for entry in databank_entry.data}
            new_data = [
                item for item in parsed_data
                if dict_to_tuple(item) not in existing_set
            ]

            logger.debug(f"Unique new data to append: {new_data}")

            if new_data:
                databank_entry.data.extend(new_data)
                db.commit()
                logger.info(f"Appended new data to existing data_name '{data_name}'.")
            else:
                logger.info(f"No new unique data to append for data_name '{data_name}'.")
        else:
            # Create a new entry if the data_name does not exist
            databank_entry = DataBank(data_name=data_name, data=parsed_data)
            db.add(databank_entry)
            db.commit()
            logger.info(f"Created new data_name '{data_name}' with initial data.")

        # Refresh and return the updated or newly created entry
        db.refresh(databank_entry)
        return DataCreateBankSchema(data_name=databank_entry.data_name, data=databank_entry.data)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the request. Please try again later.",
        )







@app.get("/fetch-all/", response_model=List[DataBankSchema])
def read_banks(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """
    List all default data
    """
    data = crud(DataBank)
    return data.get_multi(db, skip=skip, limit=limit)



@app.put("/data-bank/update/", response_model=DataCreateBankSchema, status_code=status.HTTP_200_OK)
async def update_data_bank(
    identifier: str = Form(...),  # Accept `data_name` or `id`
    key: str = Form(...),         # Key to identify the specific entry
    value: str = Form(...),       # Value of the key to match the specific entry
    data: str = Form(...),        # New data to update
    db: Session = Depends(get_db),
):
    """
    Dynamically update a specific entry in the DataBank based on `data_name` or `id`.
    Uses a provided key and value to locate the target entry in the `data` list.
    """
    try:
        # Parse the new data
        try:
            new_entry = json.loads(data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid data format. Expected a valid JSON string.",
            )

        if not isinstance(new_entry, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input: Expected a single dictionary for the new data.",
            )

        # Find the databank entry using `data_name` or `id`
        databank_entry = (
            db.query(DataBank)
            .filter(
                (DataBank.data_name == identifier) | (DataBank.id == identifier)
            )
            .first()
        )

        if not databank_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DataBank entry not found.",
            )

        # Find the index of the entry with the matching key-value pair
        existing_data = databank_entry.data
        index_to_update = next(
            (i for i, entry in enumerate(existing_data) if entry.get(key) == value),
            None
        )

        if index_to_update is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entry with `{key}`='{value}' not found.",
            )

        # Update the entry
        existing_data[index_to_update] = new_entry
        databank_entry.data = existing_data
        db.commit()
        db.refresh(databank_entry)

        return DataCreateBankSchema(data_name=databank_entry.data_name, data=databank_entry.data)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update the data. Please try again later.",
        )
