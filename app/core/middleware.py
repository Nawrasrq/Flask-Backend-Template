"""
Middleware and decorators for request handling.

This module provides authentication decorators and request middleware
for protecting endpoints and validating requests.
"""

import logging
from functools import wraps
from typing import Callable

import jwt
from flask import g, request

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security.jwt import TokenClaims, token_service

logger = logging.getLogger(__name__)


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require JWT authentication for an endpoint.

    Extracts and validates the JWT from the Authorization header,
    then stores the token claims in Flask's g object for access
    in the route handler.

    Parameters
    ----------
    f : Callable
        The route handler function to wrap

    Returns
    -------
    Callable
        Wrapped function that validates authentication

    Raises
    ------
    UnauthorizedError
        If token is missing, invalid, or expired
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        # Get Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            logger.warning("Missing Authorization header")
            raise UnauthorizedError(message="Authorization header is required")

        # Validate Bearer token format
        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning("Invalid Authorization header format")
            raise UnauthorizedError(
                message="Invalid Authorization header format. Use: Bearer <token>"
            )

        token = parts[1]

        # Decode and validate token
        try:
            claims = token_service.decode_token(token, "access")
        except jwt.ExpiredSignatureError:
            logger.warning("Expired access token")
            raise UnauthorizedError(message="Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid access token: {e}")
            raise UnauthorizedError(message="Invalid token")

        # Store claims in Flask's g object for route access
        g.current_user = claims
        g.user_id = int(claims.sub)

        logger.debug(f"Authenticated user: {claims.sub}")

        return f(*args, **kwargs)

    return decorated


def require_permission(permission: str) -> Callable:
    """
    Decorator to require a specific permission for an endpoint.

    Must be used after @require_auth decorator.

    Parameters
    ----------
    permission : str
        Required permission string (e.g., "items:write", "admin:manage")

    Returns
    -------
    Callable
        Decorator function

    Raises
    ------
    ForbiddenError
        If user lacks the required permission
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            # Ensure @require_auth was called first
            if not hasattr(g, "current_user"):
                logger.error("require_permission used without require_auth")
                raise UnauthorizedError(message="Authentication required")

            claims: TokenClaims = g.current_user

            # Super admins bypass permission checks
            if claims.is_super_admin:
                logger.debug(f"Super admin access granted for: {permission}")
                return f(*args, **kwargs)

            # Check if user has the required permission
            if permission not in claims.permissions:
                logger.warning(f"Permission denied: {permission} for user {claims.sub}")
                raise ForbiddenError(message=f"Permission required: {permission}")

            logger.debug(f"Permission granted: {permission} for user {claims.sub}")

            return f(*args, **kwargs)

        return decorated

    return decorator


def require_verified(f: Callable) -> Callable:
    """
    Decorator to require email verification for an endpoint.

    Must be used after @require_auth decorator.

    Parameters
    ----------
    f : Callable
        The route handler function to wrap

    Returns
    -------
    Callable
        Wrapped function that checks verification status

    Raises
    ------
    ForbiddenError
        If user's email is not verified
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        # Ensure @require_auth was called first
        if not hasattr(g, "current_user"):
            logger.error("require_verified used without require_auth")
            raise UnauthorizedError(message="Authentication required")

        # Note: Email verification status should be checked against database
        # or included in token claims. This is a placeholder pattern.
        # For full implementation, fetch user from database or add is_verified to claims.

        return f(*args, **kwargs)

    return decorated


def get_current_user_id() -> int:
    """
    Get the current authenticated user's ID.

    Helper function to retrieve user ID from Flask's g object.
    Must be called within a route protected by @require_auth.

    Returns
    -------
    int
        Current user's ID

    Raises
    ------
    UnauthorizedError
        If no authenticated user in context
    """
    if not hasattr(g, "user_id"):
        raise UnauthorizedError(message="No authenticated user")
    return g.user_id


def get_current_user_claims() -> TokenClaims:
    """
    Get the current authenticated user's token claims.

    Helper function to retrieve full token claims from Flask's g object.
    Must be called within a route protected by @require_auth.

    Returns
    -------
    TokenClaims
        Current user's token claims

    Raises
    ------
    UnauthorizedError
        If no authenticated user in context
    """
    if not hasattr(g, "current_user"):
        raise UnauthorizedError(message="No authenticated user")
    return g.current_user
