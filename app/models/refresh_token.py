"""
RefreshToken model for JWT token rotation and management.

This module defines the RefreshToken model which tracks refresh tokens
for secure token rotation and revocation.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(Base, TimestampMixin):
    """
    RefreshToken model for tracking JWT refresh tokens.

    This model supports refresh token rotation with family tracking
    for enhanced security against token theft attacks.

    Attributes
    ----------
    id : int
        Primary key
    user_id : int
        Foreign key to User
    token_hash : str
        SHA256 hash of refresh token (never store raw tokens)
    token_family : str
        Family ID for token rotation tracking
    expires_at : datetime
        Token expiration timestamp
    is_revoked : bool
        Whether token has been revoked
    user : User
        Relationship to User model
    """

    __tablename__ = "refresh_tokens"

    # Foreign Key
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Token Information
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="SHA256 hash of the refresh token",
    )
    token_family: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="Token family UUID for rotation detection",
    )

    # Expiration & Status
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When the refresh token expires",
    )
    is_revoked: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default="false",
        index=True,
        comment="Whether the token has been revoked",
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When the token was revoked"
    )
    revoked_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Reason for token revocation (e.g., 'logout', 'expired')",
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    @property
    def is_expired(self) -> bool:
        """
        Check if token has expired.

        Returns
        -------
        bool
            True if token is expired
        """
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """
        Check if token is valid (not revoked and not expired).

        Returns
        -------
        bool
            True if token is valid
        """
        return not self.is_revoked and not self.is_expired

    def __repr__(self) -> str:
        """
        String representation of RefreshToken.

        Returns
        -------
        str
            RefreshToken representation
        """
        return f"<RefreshToken {self.id} (user_id={self.user_id})>"
