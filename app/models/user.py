"""
User model for authentication and user management.

This module defines the User model which handles user data,
authentication, and relationships with other models.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.security.password import password_service
from app.models.base import Base, PublicIdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.refresh_token import RefreshToken


class User(Base, TimestampMixin, PublicIdMixin):
    """
    User model representing application users.

    Attributes
    ----------
    id : int
        Primary key
    email : str
        Unique email address
    hashed_password : str
        Hashed password using Argon2id
    first_name : str
        User's first name
    last_name : str
        User's last name
    role : str
        User role (e.g., 'user', 'admin')
    is_active : bool
        Whether user account is active
    is_verified : bool
        Whether user email is verified
    refresh_tokens : List[RefreshToken]
        User's refresh tokens for session management
    """

    __tablename__ = "users"

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Argon2id hashed password"
    )

    # User Information
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="user", server_default="user"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        server_default="true",
        index=True,
        comment="Whether the user account is active",
    )
    is_verified: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether the user has verified their email address",
    )

    # Session & Security
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_ip: Mapped[str | None] = mapped_column(
        String(45), nullable=True, comment="IP address of last login (IPv6 support)"
    )
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Account Lockout (for security)
    failed_login_attempts: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of consecutive failed login attempts",
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Account locked until this time (null if not locked)",
    )

    # Relationships
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked due to failed login attempts.

        Returns:
            True if account is locked, False otherwise.
        """
        if not self.locked_until:
            return False
        # Check if lockout period has expired
        return datetime.now(timezone.utc) < self.locked_until

    @property
    def full_name(self) -> str:
        """
        Get user's full name.

        Returns
        -------
        str
            Full name (first_name + last_name)
        """
        return f"{self.first_name} {self.last_name}"

    def set_password(self, password: str) -> None:
        """
        Hash and store password using Argon2id.

        Parameters
        ----------
        password : str
            Plain text password to hash

        Returns
        -------
        None
        """
        self.hashed_password = password_service.hash_password(password)

    def check_password(self, password: str) -> bool:
        """
        Verify password against stored hash.

        Parameters
        ----------
        password : str
            Plain text password to verify

        Returns
        -------
        bool
            True if password matches hash
        """
        return password_service.verify_password(password, self.hashed_password)

    def __repr__(self) -> str:
        """
        String representation of User.

        Returns
        -------
        str
            User representation
        """
        return f"<User {self.email}>"
