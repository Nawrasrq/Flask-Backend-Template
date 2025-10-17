"""
Authentication controller for user registration, login, and token management.

This module provides API endpoints for authentication operations
including registration, login, token refresh, and logout.
"""

import logging

from flask import Blueprint, request
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import ValidationError
from app.core.middleware import get_current_user_id, require_auth
from app.core.responses import success_response
from app.schemas.auth_schemas import LoginRequest, RefreshRequest
from app.schemas.user_schemas import UserRegister
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

# Create auth blueprint with URL prefix
auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

# Service instance
auth_service = AuthService()


# MARK: Registration
@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user.

    Creates a new user account and returns authentication tokens.

    Request Body
    ------------
    email : str
        Valid email address (required)
    password : str
        Password meeting strength requirements (required)
    first_name : str
        First name (required)
    last_name : str
        Last name (required)

    Returns
    -------
    tuple
        Success response with tokens (201 status)

    Raises
    ------
    ValidationError
        If request body is invalid or password too weak
    ConflictError
        If email already exists
    """
    # Parse and validate request body
    try:
        data = UserRegister.model_validate(request.get_json())
    except PydanticValidationError as e:
        raise ValidationError(message=str(e))

    # Register user and get tokens
    token_response = auth_service.register(data)

    logger.info(f"User registered: {data.email}")

    return success_response(token_response.model_dump(), status=201)


# MARK: Login
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate user and return tokens.

    Request Body
    ------------
    email : str
        User's email address (required)
    password : str
        User's password (required)

    Returns
    -------
    tuple
        Success response with tokens

    Raises
    ------
    ValidationError
        If request body is invalid
    UnauthorizedError
        If credentials are invalid
    """
    # Parse and validate request body
    try:
        data = LoginRequest.model_validate(request.get_json())
    except PydanticValidationError as e:
        raise ValidationError(message=str(e))

    # Authenticate and get tokens
    token_response = auth_service.login(data)

    logger.info(f"User logged in: {data.email}")

    return success_response(token_response.model_dump())


# MARK: Token Refresh
@auth_bp.route("/refresh", methods=["POST"])
def refresh_tokens():
    """
    Refresh access token using refresh token.

    Implements token rotation - the old refresh token is revoked
    and a new refresh token is issued.

    Request Body
    ------------
    refresh_token : str
        Current refresh token (required)

    Returns
    -------
    tuple
        Success response with new tokens

    Raises
    ------
    ValidationError
        If request body is invalid
    UnauthorizedError
        If refresh token is invalid, expired, or revoked
    """
    # Parse and validate request body
    try:
        data = RefreshRequest.model_validate(request.get_json())
    except PydanticValidationError as e:
        raise ValidationError(message=str(e))

    # Rotate tokens
    token_response = auth_service.refresh_tokens(data.refresh_token)

    logger.debug("Tokens refreshed")

    return success_response(token_response.model_dump())


# MARK: Logout
@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    Logout user by revoking refresh token.

    Request Body
    ------------
    refresh_token : str
        Refresh token to revoke (required)

    Returns
    -------
    tuple
        Success response with confirmation
    """
    # Parse request body
    body = request.get_json() or {}
    refresh_token = body.get("refresh_token")

    if refresh_token:
        auth_service.logout(refresh_token)
        logger.info("User logged out")

    return success_response({"message": "Logged out successfully"})


@auth_bp.route("/logout-all", methods=["POST"])
@require_auth
def logout_all():
    """
    Logout user from all devices.

    Revokes all refresh tokens for the current user.
    Requires authentication.

    Returns
    -------
    tuple
        Success response with count of revoked tokens
    """
    user_id = get_current_user_id()
    count = auth_service.logout_all(user_id)

    logger.info(f"User {user_id} logged out from all devices")

    return success_response(
        {
            "message": "Logged out from all devices",
            "tokens_revoked": count,
        }
    )
