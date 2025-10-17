"""
User service for profile management operations.

This module provides the service layer for user profile operations,
implementing business logic between controllers and repositories.
"""

import logging

from app.core.exceptions import NotFoundError, UnauthorizedError, ValidationError
from app.core.security.password import password_service
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user_schemas import UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    """
    Business logic for user profile management.

    Implements service layer pattern with strategic transaction control.
    Services call commit() after successful operations.

    Parameters
    ----------
    user_repo : UserRepository | None
        User repository instance (optional, creates default if not provided)
    """

    def __init__(self, user_repo: UserRepository | None = None):
        """
        Initialize UserService with repository.

        Parameters
        ----------
        user_repo : UserRepository | None
            Repository instance for dependency injection (useful for testing)
        """
        self.user_repo = user_repo or UserRepository()

    # MARK: Read
    def get_user_by_public_id(self, public_id: str) -> User:
        """
        Get user by public UUID.

        Parameters
        ----------
        public_id : str
            Public UUID of the user

        Returns
        -------
        User
            User instance

        Raises
        ------
        NotFoundError
            If user not found or is deleted/inactive
        """
        user = self.user_repo.get_by_public_id(public_id)

        if not user:
            logger.warning(f"User not found: {public_id}")
            raise NotFoundError(message="User not found")

        if user.is_deleted:
            logger.warning(f"Attempted to access deleted user: {public_id}")
            raise NotFoundError(message="User not found")

        logger.debug(f"Retrieved user: {public_id}")
        return user

    def get_user_by_id(self, user_id: int) -> User:
        """
        Get user by internal ID.

        For internal service use only. External APIs should use public_id.

        Parameters
        ----------
        user_id : int
            Internal user ID

        Returns
        -------
        User
            User instance

        Raises
        ------
        NotFoundError
            If user not found or is deleted
        """
        user = self.user_repo.get_by_id(user_id)

        if not user:
            logger.warning(f"User not found by ID: {user_id}")
            raise NotFoundError(message="User not found")

        if user.is_deleted:
            logger.warning(f"Attempted to access deleted user ID: {user_id}")
            raise NotFoundError(message="User not found")

        return user

    # MARK: Update
    def update_profile_by_id(self, user_id: int, data: UserUpdate) -> User | None:
        """
        Update user profile by internal ID.

        Use this method when you already have the user_id (e.g., from JWT claims)
        to avoid an extra database query.

        Parameters
        ----------
        user_id : int
            Internal user ID
        data : UserUpdate
            Update data from request schema

        Returns
        -------
        User
            Updated user instance

        Raises
        ------
        NotFoundError
            If user not found or is deleted
        SQLAlchemyError
            If database operation fails
        """
        # Get existing user (validates existence)
        user = self.get_user_by_id(user_id)

        # Extract only provided fields (exclude None values)
        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            logger.debug(f"No changes for user ID: {user_id}")
            return user

        # Update via repository using internal ID
        updated_user = self.user_repo.update(user_id, **update_data)

        # Commit transaction
        self.user_repo.commit()

        logger.info(f"Updated user profile for user ID: {user_id}")
        return updated_user

    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> bool:
        """
        Change user password.

        Parameters
        ----------
        user_id : int
            Internal user ID
        old_password : str
            Current password for verification
        new_password : str
            New password to set

        Returns
        -------
        bool
            True if password changed successfully

        Raises
        ------
        NotFoundError
            If user not found
        UnauthorizedError
            If old password is incorrect
        ValidationError
            If new password doesn't meet strength requirements
        """
        # Get user
        user = self.get_user_by_id(user_id)

        # Verify old password
        if not user.check_password(old_password):
            logger.warning(f"Incorrect old password for user ID: {user_id}")
            raise UnauthorizedError(message="Current password is incorrect")

        # Validate new password strength
        is_valid, violations = password_service.validate_password_strength(new_password)
        if not is_valid:
            logger.warning(f"Weak password attempt for user ID: {user_id}")
            raise ValidationError(message="; ".join(violations))

        # Check if new password is same as old
        if user.check_password(new_password):
            logger.warning(f"New password same as old for user ID: {user_id}")
            raise ValidationError(
                message="New password must be different from current password"
            )

        # Update password via repository
        result = self.user_repo.update_password(user_id, new_password)

        # Commit transaction
        self.user_repo.commit()

        logger.info(f"Password changed for user ID: {user_id}")
        return result

    def deactivate_account(self, user_id: int) -> bool:
        """
        Deactivate user account.

        Parameters
        ----------
        user_id : int
            Internal user ID

        Returns
        -------
        bool
            True if account deactivated successfully

        Raises
        ------
        NotFoundError
            If user not found
        """
        # Verify user exists
        self.get_user_by_id(user_id)

        # Deactivate via repository
        result = self.user_repo.deactivate_user(user_id)

        # Commit transaction
        self.user_repo.commit()

        logger.info(f"Deactivated user account: {user_id}")
        return result
