"""
Base repository with generic CRUD operations.

This module provides a generic repository pattern implementation with
type safety using Python generics and SQLAlchemy 2.0.
"""

import logging
from typing import Generic, List, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.db import db
from app.models.base import Base

# Type variable bound to SQLAlchemy DeclarativeBase
ModelType = TypeVar("ModelType", bound=Base)

logger = logging.getLogger(__name__)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository with type-safe CRUD operations.

    This repository provides common database operations for any SQLAlchemy model,
    with full type safety through Python generics.

    Parameters
    ----------
    model : Type[ModelType]
        The SQLAlchemy model this repository manages
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize repository with model class.

        Parameters
        ----------
        model : Type[ModelType]
            SQLAlchemy model class from models
        """
        self.model = model
        self.session = db.session

    # MARK: Transaction
    def rollback(self) -> None:
        """
        Rollback current transaction.

        Raises
        ------
        SQLAlchemyError
            If database operation fails
        """
        try:
            self.session.rollback()
            logger.debug("Transaction rolled back")
        except SQLAlchemyError as e:
            logger.error(f"Failed to rollback transaction: {e}")
            raise

    def flush(self) -> None:
        """
        Flush pending changes without committing.

        Raises
        ------
        SQLAlchemyError
            If flush fails
        """
        try:
            self.session.flush()
            logger.debug("Session flushed")
        except SQLAlchemyError as e:
            logger.error(f"Failed to flush session: {e}")
            raise

    def commit(self) -> None:
        """
        Commit current transaction.

        Raises
        ------
        SQLAlchemyError
            If commit fails
        """
        try:
            self.session.commit()
            logger.debug("Transaction committed")
        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Failed to commit transaction: {e}")
            raise

    # MARK: Get
    def count(self, **filters) -> int:
        """
        Count records matching filters.

        Parameters
        ----------
        **filters
            Field filters (e.g., status="active")

        Returns
        -------
        int
            Number of matching records
        """
        try:
            stmt = select(self.model)

            # Apply filters
            for key, value in filters.items():
                if hasattr(self.model, key):
                    stmt = stmt.where(getattr(self.model, key) == value)

            count = self.session.execute(stmt).scalars().all()
            count_value = len(count)

            logger.debug(
                f"Counted {count_value} {self.model.__name__} records matching filters"
            )
            return count_value

        except SQLAlchemyError as e:
            logger.error(f"Failed to count {self.model.__name__}: {e}")
            raise

    def exists(self, **filters) -> bool:
        """
        Check if record exists matching filters.

        Parameters
        ----------
        **filters
            Field filters (e.g., email="test@example.com")

        Returns
        -------
        bool
            True if record exists
        """
        return self.count(**filters) > 0

    # MARK: Read
    def get_by_id(self, id: int) -> ModelType | None:
        """
        Get record by ID.

        Parameters
        ----------
        id : int
            Record ID primary key

        Returns
        -------
        ModelType | None
            Model instance if found, None otherwise

        Raises
        ------
        SQLAlchemyError
            If database operation fails
        """
        try:
            stmt = select(self.model).where(self.model.id == id)
            result = self.session.execute(stmt).scalar_one_or_none()

            if result:
                logger.debug(f"Found {self.model.__name__} with ID {id}")
            else:
                logger.debug(f"{self.model.__name__} with ID {id} not found")

            return result

        except SQLAlchemyError as e:
            logger.error(f"Failed to get {self.model.__name__} by ID {id}: {e}")
            raise

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get all records with pagination.

        Parameters
        ----------
        skip : int, optional
            Number of records to skip (default: 0)
        limit : int, optional
            Maximum number of records to return (default: 100)

        Returns
        -------
        List[ModelType]
            List of model instances

        Raises
        ------
        SQLAlchemyError
            If database operation fails
        """
        try:
            stmt = select(self.model).offset(skip).limit(limit)
            results = list(self.session.execute(stmt).scalars().all())

            logger.debug(f"Retrieved {len(results)} {self.model.__name__} records")
            return results

        except SQLAlchemyError as e:
            logger.error(f"Failed to get all {self.model.__name__}: {e}")
            raise

    # MARK: Create
    def create(self, **kwargs) -> ModelType:
        """
        Create a new record.

        Parameters
        ----------
        **kwargs
            Field values for the new record

        Returns
        -------
        ModelType
            Created model instance

        Raises
        ------
        SQLAlchemyError
            If database operation fails
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            self.flush()
            self.session.refresh(instance)

            logger.info(f"Created {self.model.__name__} with ID {instance.id}")
            return instance

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Failed to create {self.model.__name__}: {e}")
            raise

    # MARK: Update
    def update(self, id: int, **kwargs) -> ModelType | None:
        """
        Update record by ID.

        Parameters
        ----------
        id : int
            Record ID
        **kwargs
            Fields to update with new values

        Returns
        -------
        ModelType | None
            Updated model instance if found, None otherwise

        Raises
        ------
        SQLAlchemyError
            If database operation fails
        """
        try:
            instance = self.get_by_id(id)
            if not instance:
                logger.warning(
                    f"{self.model.__name__} with ID {id} not found for update"
                )
                return None

            # Update fields
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            self.flush()
            self.session.refresh(instance)

            logger.info(f"Updated {self.model.__name__} with ID {id}")
            return instance

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Failed to update {self.model.__name__} with ID {id}: {e}")
            raise

    # MARK: Delete
    def delete(self, id: int) -> bool:
        """
        Permanently delete record by ID.

        Parameters
        ----------
        id : int
            Record ID

        Returns
        -------
        bool
            True if deleted, False if not found

        Raises
        ------
        SQLAlchemyError
            If database operation fails
        """
        try:
            instance = self.get_by_id(id)
            if not instance:
                logger.warning(
                    f"{self.model.__name__} with ID {id} not found for deletion"
                )
                return False

            self.session.delete(instance)
            self.flush()

            logger.info(f"Deleted {self.model.__name__} with ID {id}")
            return True

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Failed to delete {self.model.__name__} with ID {id}: {e}")
            raise

    def soft_delete(self, id: int) -> bool:
        """
        Soft delete record by ID (set is_deleted=True).

        Only works if model has is_deleted field.

        Parameters
        ----------
        id : int
            Record ID

        Returns
        -------
        bool
            True if soft deleted, False if not found

        Raises
        ------
        AttributeError
            If model doesn't have is_deleted field
        SQLAlchemyError
            If database operation fails
        """
        try:
            instance = self.get_by_id(id)
            if not instance:
                logger.warning(
                    f"{self.model.__name__} with ID {id} not found for soft deletion"
                )
                return False

            if not hasattr(instance, "soft_delete"):
                raise AttributeError(
                    f"{self.model.__name__} does not support soft delete"
                )
            instance.soft_delete()
            self.flush()

            logger.info(f"Soft deleted {self.model.__name__} with ID {id}")
            return True

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(
                f"Failed to soft delete {self.model.__name__} with ID {id}: {e}"
            )
            raise
