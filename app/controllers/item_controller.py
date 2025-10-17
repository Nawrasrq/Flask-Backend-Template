"""
Item controller for RESTful item operations.

This module provides API endpoints for Item CRUD operations
with proper authentication and validation.

Caching Example
---------------
Flask-Caching is initialized in the app factory. To cache an endpoint:

    from app import cache

    @items_bp.route("/expensive", methods=["GET"])
    @cache.cached(timeout=300, key_prefix="expensive_items")
    def expensive_query():
        # This response will be cached for 5 minutes
        return success_response({"data": "cached"})

To invalidate cache when data changes:

    @items_bp.route("", methods=["POST"])
    @require_auth
    def create_item():
        item = item_service.create_item(data)
        cache.delete("expensive_items")  # Invalidate related cache
        return success_response(item_data, status=201)
"""

import logging

from flask import Blueprint, request
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import ValidationError
from app.core.middleware import require_auth
from app.core.responses import success_response
from app.models.item import ItemStatus
from app.schemas.item_schemas import ItemCreate, ItemResponse, ItemUpdate
from app.services.item_service import ItemService

logger = logging.getLogger(__name__)

# Create items blueprint with URL prefix
items_bp = Blueprint("items", __name__, url_prefix="/api/v1/items")

# Service instance (in production, consider dependency injection)
item_service = ItemService()


# MARK: Read Endpoints
@items_bp.route("", methods=["GET"])
def list_items():
    """
    List items with pagination and optional filtering.

    Query Parameters
    ----------------
    page : int, optional
        Page number (default: 1)
    per_page : int, optional
        Items per page (default: 20, max: 100)
    status : str, optional
        Filter by status (draft, active, archived)

    Returns
    -------
    tuple
        Success response with paginated items list
    """
    # Parse query parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status_str = request.args.get("status")

    # Parse status if provided
    status = None
    if status_str:
        try:
            status = ItemStatus(status_str)
        except ValueError:
            raise ValidationError(
                message=f"Invalid status: {status_str}. Valid values: {[s.value for s in ItemStatus]}"
            )

    # Get paginated items from service (pagination metadata included)
    items, pagination = item_service.list_items(
        page=page, per_page=per_page, status=status
    )

    # Convert items to response schemas
    items_data = [ItemResponse.model_validate(item).model_dump() for item in items]

    return success_response(
        {"items": items_data, "pagination": pagination.model_dump()}
    )


@items_bp.route("/<public_id>", methods=["GET"])
def get_item(public_id: str):
    """
    Get a single item by public ID.

    Parameters
    ----------
    public_id : str
        Item's public UUID

    Returns
    -------
    tuple
        Success response with item data

    Raises
    ------
    NotFoundError
        If item not found
    """
    item = item_service.get_item_by_public_id(public_id)
    item_data = ItemResponse.model_validate(item).model_dump()

    return success_response(item_data)


@items_bp.route("/search", methods=["GET"])
def search_items():
    """
    Search items by name.

    Query Parameters
    ----------------
    q : str
        Search query

    Returns
    -------
    tuple
        Success response with matching items
    """
    query = request.args.get("q", "")

    if not query:
        raise ValidationError(message="Search query 'q' is required")

    items = item_service.search_items(query)
    items_data = [ItemResponse.model_validate(item).model_dump() for item in items]

    return success_response({"items": items_data, "count": len(items_data)})


# MARK: Create Endpoints
@items_bp.route("", methods=["POST"])
@require_auth
def create_item():
    """
    Create a new item.

    Requires authentication.

    Request Body
    ------------
    name : str
        Item name (required)
    description : str, optional
        Item description
    status : str, optional
        Item status (default: draft)
    priority : int, optional
        Priority 1-5 (default: 1)

    Returns
    -------
    tuple
        Success response with created item (201 status)

    Raises
    ------
    ValidationError
        If request body is invalid
    """
    # Parse and validate request body
    try:
        data = ItemCreate.model_validate(request.get_json())
    except PydanticValidationError as e:
        raise ValidationError(message=str(e))

    # Create item
    item = item_service.create_item(data)
    item_data = ItemResponse.model_validate(item).model_dump()

    logger.info(f"Item created: {item.public_id}")

    return success_response(item_data, status=201)


# MARK: Update Endpoints
@items_bp.route("/<public_id>", methods=["PATCH"])
@require_auth
def update_item(public_id: str):
    """
    Update an existing item.

    Requires authentication.

    Parameters
    ----------
    public_id : str
        Item's public UUID

    Request Body
    ------------
    name : str, optional
        New item name
    description : str, optional
        New description
    status : str, optional
        New status
    priority : int, optional
        New priority

    Returns
    -------
    tuple
        Success response with updated item

    Raises
    ------
    NotFoundError
        If item not found
    ValidationError
        If request body is invalid
    """
    # Parse and validate request body
    try:
        data = ItemUpdate.model_validate(request.get_json())
    except PydanticValidationError as e:
        raise ValidationError(message=str(e))

    # Update item
    item = item_service.update_item(public_id, data)
    item_data = ItemResponse.model_validate(item).model_dump()

    logger.info(f"Item updated: {public_id}")

    return success_response(item_data)


# MARK: Delete Endpoints
@items_bp.route("/<public_id>", methods=["DELETE"])
@require_auth
def delete_item(public_id: str):
    """
    Soft delete an item.

    Requires authentication.

    Parameters
    ----------
    public_id : str
        Item's public UUID

    Returns
    -------
    tuple
        Success response with confirmation

    Raises
    ------
    NotFoundError
        If item not found
    """
    item_service.delete_item(public_id)

    logger.info(f"Item deleted: {public_id}")

    return success_response({"message": "Item deleted successfully"})
