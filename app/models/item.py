"""
Item model - generic resource demonstrating the MSCR pattern.
"""

from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, PublicIdMixin, TimestampMixin


class ItemStatus(str, PyEnum):
    """Item status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Item(Base, TimestampMixin, PublicIdMixin):
    """
    Item model representing a generic resource.

    Attributes:
        id: Primary key
        name: Item name (required)
        description: Item description (optional)
        status: Item status (draft/active/archived)
        priority: Priority level (1-5)
    """

    __tablename__ = "items"

    # Item Information
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ItemStatus] = mapped_column(
        SQLEnum(ItemStatus),
        nullable=False,
        default=ItemStatus.DRAFT,
        server_default=ItemStatus.DRAFT.value,
    )
    priority: Mapped[int] = mapped_column(
        nullable=False, default=1, server_default="1", comment="Priority level (1-5)"
    )

    def __repr__(self) -> str:
        """
        String representation of Item.

        Returns
        -------
        str
            Item representation
        """
        return f"<Item(id={self.id}, name={self.name}, status={self.status}, priority={self.priority})>"
