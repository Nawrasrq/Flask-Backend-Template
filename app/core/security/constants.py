"""
Application constants.

This module defines constants used throughout the application.
Centralize magic numbers and strings here for maintainability.
"""


# MARK: Pagination
class Pagination:
    """Pagination constants."""

    DEFAULT_PAGE = 1
    DEFAULT_PER_PAGE = 20
    MAX_PER_PAGE = 100


# MARK: Permissions
class Permission:
    """
    Permission string constants for role-based access control.

    Example usage with @require_permission decorator:
        @require_auth
        @require_permission(Permission.ITEMS_WRITE)
        def create_item():
            ...
    """

    # Item permissions
    ITEMS_READ = "items:read"
    ITEMS_WRITE = "items:write"
    ITEMS_DELETE = "items:delete"

    # User management
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"

    # Admin permissions
    ADMIN_ACCESS = "admin:access"
    ADMIN_MANAGE = "admin:manage"


# MARK: Roles
class Role:
    """
    Role name constants.
    Used for assigning roles to users and checking permissions.
    """

    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


# MARK: Token
class Token:
    """Token-related constants."""

    BEARER_TYPE = "Bearer"
    HEADER_NAME = "Authorization"
