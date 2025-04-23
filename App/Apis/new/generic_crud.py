import logging
from datetime import datetime
from typing import (
    Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Sequence
)
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, UUID4
from sqlalchemy import or_, desc, select, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status
from starlette.status import HTTP_400_BAD_REQUEST

from database.db_session import BaseModel as DbBaseModel

ModelType = TypeVar("ModelType", bound=DbBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for CRUD operations on database models.

    Provides common database operations with error handling and type safety.

    Type Parameters:
        ModelType: The SQLAlchemy model type
        CreateSchemaType: Pydantic model for creation operations
        UpdateSchemaType: Pydantic model for update operations
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize the repository with a specific model.

        Args:
            model: SQLAlchemy model class
        """
        self.model = model

    def get_one(self, db: Session, *, silent=False, **filters) -> Optional[ModelType]:
        """
        Retrieve a single record by matching a specific field value.

        example usage: user = get_one(db=db, id=<uuid>)
        """
        try:
            query = db.query(self.model)
            for k, v in filters.items():
                query = query.filter(getattr(self.model, k) == v)

            result = query.first()
            if not result and not silent: raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"{self.model.__name__} not found"
            )
            return result
        except SQLAlchemyError:
            logging.error(f"Database error fetching {self.model.__name__} with id={id}", exc_info=True)
            raise self._http_500_exception()
        except Exception:
            logging.exception(f"Error in get_by_field for {self.model.__name__}")
            raise self._http_500_exception()

    def get_by_id(self, db: Session, *, id: UUID4, silent=False) -> ModelType:
        """
        Retrieve a single record by its ID.
        """
        return self.get_one(db=db, id=id, silent=silent)

    def get_many_by_ids(self, db: Session, *, ids: list, silent=False) -> Optional[List[ModelType]]:
        """
        Retrieve multiple records by their IDs.
        """
        if not ids: return []
        try:
            found_objects = db.query(self.model).filter(self.model.id.in_(ids)).all()
            missing_ids = set(ids) - {obj.id for obj in found_objects}
            if missing_ids and not silent: raise self._http_400_exception(
                f"Records not found for ids: {missing_ids}"
            )
            return found_objects
        except Exception:
            logging.exception(f"Error in get_many_by_ids for {self.model.__name__}")
            raise self._http_500_exception()

    def get_all(
            self, *,
            db: Session,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[List[str]] = None,
    ) -> List[ModelType]:
        """
        Get all records from db with pagination and ordering.

        To order in descending order for any field, prefix the field with a hyphen

        example usage: users = get_all(db=db, order_by = ["rank", "-created_at"])
        """
        try:
            query = db.query(self.model)
            query = self._get_ordering(query=query, order_by=order_by)
            result = query.offset(skip).limit(limit).all()
            return result
        except HTTPException:
            raise
        except SQLAlchemyError:
            logging.error(f"Database error in get_all for {self.model.__name__}", exc_info=True)
            raise self._http_500_exception()
        except:
            logging.exception(f"Unexpected error in get_all {self.model.__name__}")
            raise self._http_500_exception()

    def get_by_filters(
            self, *,
            db: Session,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[List[str]] = None,
            **filters: Any
    ) -> Sequence[ModelType]:
        query = db.query(self.model)
        try:
            for field, value in filters.items():
                if value is not None:
                    query = query.filter(getattr(self.model, field) == value)

            query = self._get_ordering(query=query, order_by=order_by)
            query = query.offset(skip).limit(limit)
            result = db.execute(query)
            return result.scalars().all()

        except HTTPException:
            raise
        except AttributeError:
            logging.error("Invalid filter field")
            raise self._http_400_exception(
                f'Invalid filter field provided for {self.model.__name__}'
            )
        except:
            logging.exception(f"Error in get_by_filters for {self.model.__name__}")
            raise self._http_500_exception()

    def get_by_pattern(
            self, *,
            db: Session,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[List[str]] = None,
            **patterns: Any
    ) -> Sequence[ModelType]:
        query = db.query(self.model)
        try:
            for field, pattern in patterns.items():
                if not pattern: continue

                field_attr = getattr(self.model, field)
                if isinstance(pattern, list):

                    valid_patterns = [p.strip() for p in pattern if p]
                    if not valid_patterns: continue

                    query = query.filter(or_(*[field_attr.ilike(f"%{p}%") for p in valid_patterns]))

                else:
                    query = query.filter(field_attr.ilike(f"%{pattern}%"))

            query = self._get_ordering(query=query, order_by=order_by)
            query = query.offset(skip).limit(limit)
            result = db.execute(query)
            return result.scalars().all()

        except HTTPException:
            raise
        except AttributeError as e:
            logging.error("Invalid pattern matching field", exc_info=True)
            raise self._http_400_exception(
                f'Invalid field for pattern matching: {str(e)}'
            )
        except:
            logging.exception(f"Error in get_by_pattern for {self.model.__name__}")
            raise self._http_500_exception()

    def get_or_create(
            self, *,
            db: Session,
            data: CreateSchemaType,
            unique_field: str,
    ) -> ModelType:
        try:
            db_obj = (
                db.query(self.model)
                .filter(getattr(self.model, unique_field) == getattr(data, unique_field))
                .first()
            )
            if db_obj: return db_obj
            return self.create(db=db, data=data)
        except HTTPException:
            db.rollback()
            raise
        except:
            logging.exception(f"Error in get_or_create for {self.model.__name__}")
            db.rollback()
            raise self._http_500_exception()

    def create(self, db: Session, *, data: CreateSchemaType, unique_fields: list = None) -> ModelType:
        if unique_fields is None: unique_fields = []
        if not data: raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="No data provided for creation"
        )

        try:
            model_data = data.model_dump(exclude_none=True, exclude_defaults=False)
            self._validate_unique_fields(db=db, model_data=model_data, unique_fields=unique_fields)

            db_obj = self.model(**model_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return self.get_by_id(db=db, id=db_obj.id)

        except HTTPException:
            db.rollback()
            raise
        except IntegrityError as e:
            db.rollback()
            logging.error(f"Integrity error creating {self.model.__name__}", exc_info=True)
            raise self._http_409_exception(self._format_integrity_error(e))
        except:
            logging.exception(f"Failed to create {self.model.__name__}")
            db.rollback()
            raise self._http_500_exception()

    def update(
            self, *,
            db: Session,
            data: Union[UpdateSchemaType, Dict[str, Any]],
            db_obj: Optional[ModelType] = None,
            id: Optional[UUID4] = None,
            unique_fields: Optional[List] = None
    ) -> ModelType:
        if unique_fields is None: unique_fields = []
        if not db_obj and not id: raise self._http_400_exception(
            "Either 'db_obj' or 'id' must be provided for update"
        )
        if not db_obj: db_obj = self.get_by_id(db=db, id=id, silent=False)
        try:
            update_data = data.model_dump(exclude_none=True) if isinstance(data, BaseModel) else data
            self._validate_unique_fields(db=db, model_data=update_data, unique_fields=unique_fields, id=id)

            for field, value in update_data.items():
                setattr(db_obj, field, value)

            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)

            return db_obj
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logging.exception(f"Error updating {self.model.__name__}: {str(e)}")
        raise self._http_500_exception()

    def delete(self, db: Session, *, id: UUID4, soft: bool = False) -> None:
        """
        Delete a record by ID.

        Args:
            db: Database session
            id: Record ID to delete
            soft: argument to either soft delete the record or not

        Raises:
            HTTPException: 404 if not found, 409 if deletion violates constraints
        """
        # Check existence
        existing_obj = self.get_by_id(db=db, id=id)
        try:
            if soft:
                existing_obj.is_deleted = True
                existing_obj.is_active = False
                existing_obj.deleted_at = datetime.utcnow()

                # Mark the object as changed
                db.add(existing_obj)
                db.commit()
            else:
                # Perform hard deletion
                db.execute(
                    delete(self.model)
                    .where(self.model.id == id)
                    .execution_options(synchronize_session=False)
                )
                db.commit()

        except HTTPException:
            db.rollback()
            raise
        except IntegrityError as e:
            db.rollback()
            logging.error(f"Integrity error deleting {self.model.__name__}", exc_info=True)
            raise self._http_409_exception(self._format_integrity_error(e))
        except:
            db.rollback()
            logging.exception(f"Error deleting {self.model.__name__}")
            raise self._http_500_exception()

    def bulk_hard_delete(self, db: Session, *, ids: List[UUID4]) -> None:
        """
        Delete multiple records by ID.

        Args:
            db: Database session
            ids: List of record IDs to delete

        Raises:
            HTTPException: 404 if not found, 409 if deletion violates constraints
        """
        if not ids: return
        try:
            result = db.execute(delete(self.model).where(self.model.id.in_(ids)))
            db.commit()

            # Check if all rows were deleted
            if result.rowcount != len(ids): logging.warning(
                f"Requested to delete {len(ids)} records, but only {result.rowcount} were deleted"
            )

        except HTTPException:
            db.rollback()
            logging.exception("failed to delete")
            raise
        except IntegrityError:
            db.rollback()
            logging.error(f"Integrity error during bulk delete of {self.model.__name__}", exc_info=True)
            raise self._http_409_exception(
                f"Cannot delete some {self.model.__name__} records due to constraints"
            )
        except Exception:
            db.rollback()
            logging.exception(f"Error during bulk delete of {self.model.__name__}")
            raise self._http_500_exception()

    def _validate_unique_fields(self, db: Session, *, model_data: dict, unique_fields: List, id: UUID = None):
        for field in unique_fields:
            if field in model_data and model_data[field]:
                query = select(self.model).where(getattr(self.model, field) == model_data[field])

                if id:
                    if not isinstance(id, UUID): raise self._http_400_exception(
                        "Invalid UUID format for ID"
                    )
                    query = query.where(self.model.id != id)

                result = db.execute(query)
                if result.scalars().first(): raise self._http_400_exception(
                    f"'{field}' for {model_data[field]} already exists"
                )

    def _get_ordering(self, query, order_by: List[str]):
        if not order_by: return query.order_by(desc(self.model.created_at))

        _ordering_fields = []
        try:
            for field in order_by:
                desc_order = False
                if field.startswith('-'):
                    field = field[1:]
                    desc_order = True

                order_column = getattr(self.model, field)
                ordering = desc(order_column) if desc_order else order_column
                _ordering_fields.append(ordering)

            return query.order_by(*_ordering_fields)
        except AttributeError:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f'Invalid key given to order_by: {order_by}'
            )

    @staticmethod
    def _format_integrity_error(e: IntegrityError) -> str:
        """Prettifies SQLAlchemy IntegrityError messages."""
        error_message = str(e.orig)

        if isinstance(e.orig, Exception):
            if "ForeignKeyViolationError" in error_message:
                start = error_message.find("Key (")
                if start != -1:
                    detail = error_message[start:].replace("DETAIL: ", "").strip()
                    return f"Foreign key constraint violated: {detail}"
                return "Foreign key constraint violated."
            elif "UniqueViolationError" in error_message:
                return "Unique constraint violated. A similar record already exists."

        return str(e.orig)

    @staticmethod
    def _http_500_exception() -> Exception:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong! Kindly try again or contact support.",
        )

    @staticmethod
    def _http_400_exception(message: str) -> Exception:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    @staticmethod
    def _http_409_exception(message: str) -> Exception:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        )
