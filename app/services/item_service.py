"""
Item service for business logic operations.

This module provides the service layer for Item CRUD operations,
implementing business logic between controllers and repositories.
"""

import logging
from typing import List

from app.core.exceptions import NotFoundError
from app.models.item import Item, ItemStatus
from app.repositories.item_repository import ItemRepository
from app.schemas.common_schemas import PaginationMeta
from app.schemas.item_schemas import ItemCreate, ItemUpdate

logger = logging.getLogger(__name__)


class ItemService:
    """
    Business logic for Item operations.

    Implements service layer pattern with strategic transaction control.
    Services call commit() after successful operations.

    Parameters
    ----------
    item_repo : ItemRepository | None
        Item repository instance (optional, creates default if not provided)
    """

    def __init__(self, item_repo: ItemRepository | None = None):
        """
        Initialize ItemService with repository.

        Parameters
        ----------
        item_repo : ItemRepository | None
            Repository instance for dependency injection (useful for testing)
        """
        self.item_repo = item_repo or ItemRepository()

    # MARK: Read
    def get_item_by_public_id(self, public_id: str) -> Item:
        """
        Get item by public UUID.

        Parameters
        ----------
        public_id : str
            Public UUID of the item

        Returns
        -------
        Item
            Item instance

        Raises
        ------
        NotFoundError
            If item not found or is deleted
        """
        item = self.item_repo.get_by_public_id(public_id)

        if not item:
            logger.warning(f"Item not found: {public_id}")
            raise NotFoundError(message="Item not found")

        if item.is_deleted:
            logger.warning(f"Attempted to access deleted item: {public_id}")
            raise NotFoundError(message="Item not found")

        logger.debug(f"Retrieved item: {public_id}")
        return item

    def list_items(
        self,
        page: int = 1,
        per_page: int = 20,
        status: ItemStatus | None = None,
    ) -> tuple[List[Item], PaginationMeta]:
        """
        List items with pagination and optional status filter.

        Uses database-level pagination (LIMIT/OFFSET) for efficiency.

        Parameters
        ----------
        page : int, optional
            Page number (1-indexed, default: 1)
        per_page : int, optional
            Items per page (default: 20, capped at 100)
        status : ItemStatus | None, optional
            Filter by item status

        Returns
        -------
        tuple[List[Item], PaginationMeta]
            Tuple of (items list, pagination metadata)
        """
        # Cap per_page at 100
        per_page = min(per_page, 100)
        skip = (page - 1) * per_page

        if status:
            # Filter by status with database-level pagination
            items, total = self.item_repo.get_by_status_paginated(
                status, skip=skip, limit=per_page
            )
        else:
            # Get active items with database-level pagination
            items, total = self.item_repo.get_active_items_paginated(
                skip=skip, limit=per_page
            )

        # Build pagination metadata
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        pagination = PaginationMeta(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

        logger.debug(f"Listed {len(items)} items (page {page}, total {total})")
        return items, pagination

    def search_items(self, query: str) -> List[Item]:
        """
        Search items by name.

        Parameters
        ----------
        query : str
            Search query for item name

        Returns
        -------
        List[Item]
            List of items matching search query
        """
        items = self.item_repo.search_by_name(query)
        logger.debug(f"Search '{query}' returned {len(items)} items")
        return items

    # MARK: Create
    def create_item(self, data: ItemCreate) -> Item:
        """
        Create a new item.

        Parameters
        ----------
        data : ItemCreate
            Item creation data from request schema

        Returns
        -------
        Item
            Created item instance

        Raises
        ------
        SQLAlchemyError
            If database operation fails
        """
        # Extract validated data from schema
        item_data = data.model_dump()

        # Create item via repository
        item = self.item_repo.create(**item_data)

        # Commit transaction (strategic control)
        self.item_repo.commit()

        logger.info(f"Created item: {item.public_id} (name: {item.name})")
        return item

    # MARK: Update
    def update_item(self, public_id: str, data: ItemUpdate) -> Item | None:
        """
        Update an existing item.

        Parameters
        ----------
        public_id : str
            Public UUID of the item to update
        data : ItemUpdate
            Update data from request schema

        Returns
        -------
        Item
            Updated item instance

        Raises
        ------
        NotFoundError
            If item not found or is deleted
        SQLAlchemyError
            If database operation fails
        """
        # Get existing item (validates existence)
        item = self.get_item_by_public_id(public_id)

        # Extract only provided fields (exclude None values)
        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            logger.debug(f"No changes for item: {public_id}")
            return item

        # Update via repository using internal ID
        updated_item = self.item_repo.update(item.id, **update_data)

        # Commit transaction
        self.item_repo.commit()

        logger.info(f"Updated item: {public_id}")
        return updated_item

    # MARK: Delete
    def delete_item(self, public_id: str) -> bool:
        """
        Soft delete an item.

        Parameters
        ----------
        public_id : str
            Public UUID of the item to delete

        Returns
        -------
        bool
            True if deleted successfully

        Raises
        ------
        NotFoundError
            If item not found or already deleted
        SQLAlchemyError
            If database operation fails
        """
        # Get existing item (validates existence)
        item = self.get_item_by_public_id(public_id)

        # Soft delete via repository using internal ID
        result = self.item_repo.soft_delete(item.id)

        # Commit transaction
        self.item_repo.commit()

        logger.info(f"Soft deleted item: {public_id}")
        return result
