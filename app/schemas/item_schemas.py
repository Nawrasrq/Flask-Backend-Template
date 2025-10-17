"""
Pydantic schemas for Item model.

This module defines request and response schemas for Item CRUD operations.
"""

from pydantic import Field

from app.models.item import ItemStatus
from app.schemas.base import BaseResponseSchema, BaseSchema


class ItemCreate(BaseSchema):
    """
    Schema for creating a new item.

    Parameters
    ----------
    name : str
        Item name (max 100 characters)
    description : str | None
        Optional item description
    status : ItemStatus
        Item status (default: DRAFT)
    priority : int
        Priority level 1-5 (default: 1)
    """

    name: str = Field(min_length=1, max_length=100, description="Item name (required)")
    description: str | None = Field(default=None, description="Item description")
    status: ItemStatus = Field(default=ItemStatus.DRAFT, description="Item status")
    priority: int = Field(default=1, ge=1, le=5, description="Priority level (1-5)")


class ItemUpdate(BaseSchema):
    """
    Schema for updating an existing item.

    All fields are optional - only provided fields will be updated.

    Parameters
    ----------
    name : str | None
        Item name (max 100 characters)
    description : str | None
        Item description
    status : ItemStatus | None
        Item status
    priority : int | None
        Priority level 1-5
    """

    name: str | None = Field(
        default=None, min_length=1, max_length=100, description="Item name"
    )
    description: str | None = Field(default=None, description="Item description")
    status: ItemStatus | None = Field(default=None, description="Item status")
    priority: int | None = Field(default=None, ge=1, le=5, description="Priority level")


class ItemResponse(BaseResponseSchema):
    """
    Schema for item response with all fields.

    Attributes
    ----------
    name : str
        Item name
    description : str | None
        Item description
    status : ItemStatus
        Item status
    priority : int
        Priority level
    """

    name: str = Field(description="Item name")
    description: str | None = Field(description="Item description")
    status: ItemStatus = Field(description="Item status")
    priority: int = Field(description="Priority level")
