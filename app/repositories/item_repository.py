"""
Item repository for database operations.

This module provides data access methods specific to the Item model.
"""

import logging
from typing import List

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.models.item import Item, ItemStatus
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ItemRepository(BaseRepository[Item]):
    """
    Repository for Item model with custom query methods.

    Extends BaseRepository to provide Item-specific database operations.
    """

    def __init__(self):
        """Initialize ItemRepository with Item model class."""
        super().__init__(Item)

    # MARK: Get
    def get_by_public_id(self, public_id: str) -> Item | None:
        """
        Get record by public ID.

        Parameters
        ----------
        public_id : str
            Record public ID primary key

        Returns
        -------
        Item | None
            Model instance if found, None otherwise

        Raises
        ------
        SQLAlchemyError
            If database operation fails
        """
        try:
            stmt = select(self.model).where(self.model.public_id == public_id)
            result = self.session.execute(stmt).scalar_one_or_none()

            if result:
                logger.debug(f"Found {self.model.__name__} with public ID {public_id}")
            else:
                logger.debug(
                    f"{self.model.__name__} with public ID {public_id} not found"
                )

            return result

        except SQLAlchemyError as e:
            logger.error(
                f"Failed to get {self.model.__name__} by public ID {public_id}: {e}"
            )
            raise

    def get_by_status(self, status: ItemStatus) -> List[Item]:
        """
        Get all items with specific status.

        Parameters
        ----------
        status : ItemStatus
            Item status to filter by

        Returns
        -------
        List[Item]
            List of items with matching status
        """
        try:
            stmt = select(Item).where(Item.status == status, Item.is_deleted.is_(False))
            results = list(self.session.execute(stmt).scalars().all())

            logger.debug(f"Retrieved {len(results)} items with status {status.value}")
            return results

        except SQLAlchemyError as e:
            logger.error(f"Failed to get items by status {status.value}: {e}")
            raise

    def search_by_name(self, query: str) -> List[Item]:
        """
        Search items by name (case-insensitive partial match).

        Parameters
        ----------
        query : str
            Search query for item name

        Returns
        -------
        List[Item]
            List of items matching search query
        """
        try:
            stmt = select(Item).where(
                Item.name.ilike(f"%{query}%"), Item.is_deleted.is_(False)
            )
            results = list(self.session.execute(stmt).scalars().all())

            logger.debug(f"Found {len(results)} items matching query '{query}'")
            return results

        except SQLAlchemyError as e:
            logger.error(f"Failed to search items by name '{query}': {e}")
            raise

    def get_active_items(self) -> List[Item]:
        """
        Get all non-deleted items.

        Returns
        -------
        List[Item]
            List of active (non-deleted) items
        """
        try:
            stmt = select(Item).where(Item.is_deleted.is_(False))
            results = list(self.session.execute(stmt).scalars().all())

            logger.debug(f"Retrieved {len(results)} active items")
            return results

        except SQLAlchemyError as e:
            logger.error(f"Failed to get active items: {e}")
            raise

    def get_by_priority(self, min_priority: int = 1) -> List[Item]:
        """
        Get items with priority >= minimum.

        Parameters
        ----------
        min_priority : int, optional
            Minimum priority level (default: 1)

        Returns
        -------
        List[Item]
            List of items with priority >= min_priority
        """
        try:
            stmt = select(Item).where(
                Item.priority >= min_priority, Item.is_deleted.is_(False)
            )
            results = list(self.session.execute(stmt).scalars().all())

            logger.debug(
                f"Retrieved {len(results)} items with priority >= {min_priority}"
            )
            return results

        except SQLAlchemyError as e:
            logger.error(f"Failed to get items by priority >= {min_priority}: {e}")
            raise

    # MARK: Paginated Queries
    def get_active_items_paginated(
        self, skip: int = 0, limit: int = 20
    ) -> tuple[List[Item], int]:
        """
        Get non-deleted items with database-level pagination.

        Parameters
        ----------
        skip : int, optional
            Number of records to skip (default: 0)
        limit : int, optional
            Maximum records to return (default: 20)

        Returns
        -------
        tuple[List[Item], int]
            Tuple of (items list, total count)

        Raises
        ------
        SQLAlchemyError
            If database operation fails
        """
        try:
            # Get total count
            count_stmt = select(func.count()).select_from(Item).where(
                Item.is_deleted.is_(False)
            )
            total = self.session.execute(count_stmt).scalar() or 0

            # Get paginated results
            stmt = (
                select(Item)
                .where(Item.is_deleted.is_(False))
                .order_by(Item.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            items = list(self.session.execute(stmt).scalars().all())

            logger.debug(f"Retrieved {len(items)} of {total} active items (skip={skip})")
            return items, total

        except SQLAlchemyError as e:
            logger.error(f"Failed to get paginated active items: {e}")
            raise

    def get_by_status_paginated(
        self, status: ItemStatus, skip: int = 0, limit: int = 20
    ) -> tuple[List[Item], int]:
        """
        Get items by status with database-level pagination.

        Parameters
        ----------
        status : ItemStatus
            Item status to filter by
        skip : int, optional
            Number of records to skip (default: 0)
        limit : int, optional
            Maximum records to return (default: 20)

        Returns
        -------
        tuple[List[Item], int]
            Tuple of (items list, total count)

        Raises
        ------
        SQLAlchemyError
            If database operation fails
        """
        try:
            # Get total count
            count_stmt = select(func.count()).select_from(Item).where(
                Item.status == status, Item.is_deleted.is_(False)
            )
            total = self.session.execute(count_stmt).scalar() or 0

            # Get paginated results
            stmt = (
                select(Item)
                .where(Item.status == status, Item.is_deleted.is_(False))
                .order_by(Item.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            items = list(self.session.execute(stmt).scalars().all())

            logger.debug(
                f"Retrieved {len(items)} of {total} items with status {status.value}"
            )
            return items, total

        except SQLAlchemyError as e:
            logger.error(f"Failed to get paginated items by status: {e}")
            raise
