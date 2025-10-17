"""
User controller for profile management operations.

This module provides API endpoints for user profile operations
including viewing and updating profile, and changing password.
"""

import logging

from flask import Blueprint, request
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import ValidationError
from app.core.middleware import get_current_user_id, require_auth
from app.core.responses import success_response
from app.schemas.auth_schemas import PasswordChangeRequest
from app.schemas.user_schemas import UserResponse, UserUpdate
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

# Create users blueprint with URL prefix
users_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")

# Service instance
user_service = UserService()


# MARK: Profile Endpoints
@users_bp.route("/me", methods=["GET"])
@require_auth
def get_current_user():
    """
    Get current user's profile.

    Requires authentication.

    Returns
    -------
    tuple
        Success response with user profile data

    Raises
    ------
    NotFoundError
        If user not found (should not happen for valid token)
    """
    user_id = get_current_user_id()

    # Get user by internal ID (from token)
    user = user_service.get_user_by_id(user_id)
    user_data = UserResponse.model_validate(user).model_dump()

    return success_response(user_data)


@users_bp.route("/me", methods=["PATCH"])
@require_auth
def update_current_user():
    """
    Update current user's profile.

    Requires authentication.

    Request Body
    ------------
    first_name : str, optional
        New first name
    last_name : str, optional
        New last name

    Returns
    -------
    tuple
        Success response with updated profile

    Raises
    ------
    ValidationError
        If request body is invalid
    """
    user_id = get_current_user_id()

    # Parse and validate request body
    try:
        data = UserUpdate.model_validate(request.get_json())
    except PydanticValidationError as e:
        raise ValidationError(message=str(e))

    # Update profile directly by ID (avoids extra query)
    updated_user = user_service.update_profile_by_id(user_id, data)
    user_data = UserResponse.model_validate(updated_user).model_dump()

    logger.info(f"User profile updated: {user_id}")

    return success_response(user_data)


# MARK: Password Management
@users_bp.route("/me/password", methods=["POST"])
@require_auth
def change_password():
    """
    Change current user's password.

    Requires authentication.

    Request Body
    ------------
    old_password : str
        Current password (required)
    new_password : str
        New password meeting strength requirements (required)

    Returns
    -------
    tuple
        Success response with confirmation

    Raises
    ------
    ValidationError
        If request body is invalid or new password too weak
    UnauthorizedError
        If old password is incorrect
    """
    user_id = get_current_user_id()

    # Parse and validate request body
    try:
        data = PasswordChangeRequest.model_validate(request.get_json())
    except PydanticValidationError as e:
        raise ValidationError(message=str(e))

    # Change password
    user_service.change_password(
        user_id=user_id,
        old_password=data.old_password,
        new_password=data.new_password,
    )

    logger.info(f"Password changed for user: {user_id}")

    return success_response({"message": "Password changed successfully"})


# MARK: Account Management
@users_bp.route("/me/deactivate", methods=["POST"])
@require_auth
def deactivate_account():
    """
    Deactivate current user's account.

    Requires authentication. This action can be reversed by an admin.

    Returns
    -------
    tuple
        Success response with confirmation
    """
    user_id = get_current_user_id()

    user_service.deactivate_account(user_id)

    logger.info(f"Account deactivated for user: {user_id}")

    return success_response({"message": "Account deactivated successfully"})
