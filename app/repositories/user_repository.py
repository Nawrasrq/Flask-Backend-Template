"""
User repository for database operations.

This module provides data access methods specific to the User model.
"""

import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import ConflictError
from app.models.user import User
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """
    Repository for User model with authentication-specific methods.

    Extends BaseRepository to provide User-specific database operations
    including user creation with password hashing and email lookup.
    """

    def __init__(self):
        """Initialize UserRepository with User model class."""
        super().__init__(User)

    # MARK: Get
    def get_by_public_id(self, public_id: str) -> User | None:
        """
        Get record by public ID.

        Parameters
        ----------
        public_id : str
            Record public ID primary key

        Returns
        -------
        User | None
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

    def find_by_email(self, email: str) -> User | None:
        """
        Find user by email address.

        Parameters
        ----------
        email : str
            Email address to search for

        Returns
        -------
        User | None
            User instance if found, None otherwise
        """
        try:
            stmt = select(User).where(User.email == email, User.is_deleted.is_(False))
            result = self.session.execute(stmt).scalar_one_or_none()

            if result:
                logger.debug(f"Found user with email {email}")
            else:
                logger.debug(f"User with email {email} not found")

            return result

        except SQLAlchemyError as e:
            logger.error(f"Failed to find user by email {email}: {e}")
            raise

    def get_active_users(self) -> List[User]:
        """
        Get all active (non-deleted, is_active=True) users.

        Returns
        -------
        List[User]
            List of active users
        """
        try:
            stmt = select(User).where(User.is_active, User.is_deleted.is_(False))
            results = list(self.session.execute(stmt).scalars().all())

            logger.debug(f"Retrieved {len(results)} active users")
            return results

        except SQLAlchemyError as e:
            logger.error(f"Failed to get active users: {e}")
            raise

    def get_verified_users(self) -> List[User]:
        """
        Get all verified users.

        Returns
        -------
        List[User]
            List of verified users
        """
        try:
            stmt = select(User).where(User.is_verified, User.is_deleted.is_(False))
            results = list(self.session.execute(stmt).scalars().all())

            logger.debug(f"Retrieved {len(results)} verified users")
            return results

        except SQLAlchemyError as e:
            logger.error(f"Failed to get verified users: {e}")
            raise

    def verify_email(self, user_id: int) -> bool:
        """
        Mark user email as verified.

        Parameters
        ----------
        user_id : int
            User ID

        Returns
        -------
        bool
            True if verified, False if user not found

        Raises
        ------
        SQLAlchemyError
            If database operation fails
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                logger.warning(
                    f"User with ID {user_id} not found for email verification"
                )
                return False

            user.is_verified = True
            self.flush()

            logger.info(f"Verified email for user ID {user_id}")
            return True

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Failed to verify email for user ID {user_id}: {e}")
            raise

    # MARK: Create
    def create_user(
        self, email: str, password: str, first_name: str, last_name: str
    ) -> User:
        """
        Create a new user with hashed password.

        Parameters
        ----------
        email : str
            User email address (must be unique)
        password : str
            Plain text password (will be hashed)
        first_name : str
            User's first name
        last_name : str
            User's last name

        Returns
        -------
        User
            Created user instance

        Raises
        ------
        ConflictError
            If email already exists
        SQLAlchemyError
            If database operation fails
        """
        try:
            # Check if email already exists
            if self.find_by_email(email):
                logger.warning(
                    f"Attempted to create user with duplicate email: {email}"
                )
                raise ConflictError(
                    message=f"User with email {email} already exists", field="email"
                )

            # Create user with hashed password
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            user.set_password(password)

            self.session.add(user)
            self.flush()
            self.session.refresh(user)

            logger.info(f"Created user with email {email} (ID: {user.id})")
            return user

        except IntegrityError as e:
            self.rollback()
            logger.error(f"Integrity error creating user with email {email}: {e}")
            raise ConflictError(
                message=f"User with email {email} already exists", field="email"
            )
        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Failed to create user with email {email}: {e}")
            raise

    # MARK: Update
    def update_password(self, user_id: int, new_password: str) -> bool:
        """
        Update user's password.

        Parameters
        ----------
        user_id : int
            User ID
        new_password : str
            New plain text password (will be hashed)

        Returns
        -------
        bool
            True if password updated, False if user not found

        Raises
        ------
        SQLAlchemyError
            If database operation fails
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                logger.warning(f"User with ID {user_id} not found for password update")
                return False

            # Hash and update password
            user.set_password(new_password)
            self.flush()

            logger.info(f"Updated password for user ID {user_id}")
            return True

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Failed to update password for user ID {user_id}: {e}")
            raise

    def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate user account.

        Parameters
        ----------
        user_id : int
            User ID

        Returns
        -------
        bool
            True if deactivated, False if user not found

        Raises
        ------
        SQLAlchemyError
            If database operation fails
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                logger.warning(f"User with ID {user_id} not found for deactivation")
                return False

            user.is_active = False
            self.flush()

            logger.info(f"Deactivated user ID {user_id}")
            return True

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Failed to deactivate user ID {user_id}: {e}")
            raise
