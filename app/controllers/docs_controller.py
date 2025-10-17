"""
API documentation controller serving OpenAPI spec and Swagger UI.

This module provides endpoints for API documentation including:
- OpenAPI 3.0 JSON specification
- Swagger UI for interactive API exploration
"""

import logging

from flask import Blueprint, jsonify, render_template_string

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create docs blueprint
docs_bp = Blueprint("docs", __name__, url_prefix="/api/docs")


# MARK: OpenAPI Specification
def get_openapi_spec() -> dict:
    """
    Generate OpenAPI 3.0 specification for the API.

    Returns
    -------
    dict
        OpenAPI specification dictionary
    """
    return {
        "openapi": settings.OPENAPI_VERSION,
        "info": {
            "title": settings.API_TITLE,
            "version": settings.API_VERSION,
            "description": "A production-ready Flask backend template with MSCR architecture.",
            "contact": {"name": "API Support"},
        },
        "servers": [
            {"url": "/", "description": "Current server"},
        ],
        "tags": [
            {"name": "Health", "description": "Health check endpoints"},
            {"name": "Auth", "description": "Authentication and authorization"},
            {"name": "Users", "description": "User profile management"},
            {"name": "Items", "description": "Item CRUD operations"},
        ],
        "paths": {
            "/health": {
                "get": {
                    "tags": ["Health"],
                    "summary": "Health check",
                    "description": "Returns application health status",
                    "responses": {
                        "200": {
                            "description": "Application is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HealthResponse"
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/api/v1/auth/register": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Register new user",
                    "description": "Create a new user account and return authentication tokens",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserRegister"}
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "User registered successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/TokenResponse"
                                    }
                                }
                            },
                        },
                        "400": {
                            "description": "Validation error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "409": {
                            "description": "Email already exists",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                }
            },
            "/api/v1/auth/login": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "User login",
                    "description": "Authenticate user and return tokens",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/LoginRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Login successful",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/TokenResponse"
                                    }
                                }
                            },
                        },
                        "401": {
                            "description": "Invalid credentials",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                }
            },
            "/api/v1/auth/refresh": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Refresh tokens",
                    "description": "Get new access token using refresh token",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/RefreshRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Tokens refreshed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/TokenResponse"
                                    }
                                }
                            },
                        },
                        "401": {
                            "description": "Invalid or expired refresh token",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                }
            },
            "/api/v1/auth/logout": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Logout",
                    "description": "Revoke refresh token",
                    "requestBody": {
                        "required": False,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/RefreshRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Logged out successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/MessageResponse"
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/api/v1/auth/logout-all": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Logout from all devices",
                    "description": "Revoke all refresh tokens for current user",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Logged out from all devices",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/LogoutAllResponse"
                                    }
                                }
                            },
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                }
            },
            "/api/v1/users/me": {
                "get": {
                    "tags": ["Users"],
                    "summary": "Get current user profile",
                    "description": "Returns the authenticated user's profile",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "User profile",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/UserResponse"}
                                }
                            },
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                },
                "patch": {
                    "tags": ["Users"],
                    "summary": "Update current user profile",
                    "description": "Update the authenticated user's profile",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserUpdate"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Profile updated",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/UserResponse"}
                                }
                            },
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                },
            },
            "/api/v1/users/me/password": {
                "post": {
                    "tags": ["Users"],
                    "summary": "Change password",
                    "description": "Change the authenticated user's password",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/PasswordChangeRequest"
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Password changed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/MessageResponse"
                                    }
                                }
                            },
                        },
                        "400": {
                            "description": "Validation error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "401": {
                            "description": "Unauthorized or incorrect current password",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                }
            },
            "/api/v1/users/me/deactivate": {
                "post": {
                    "tags": ["Users"],
                    "summary": "Deactivate account",
                    "description": "Deactivate the authenticated user's account",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Account deactivated",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/MessageResponse"
                                    }
                                }
                            },
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                }
            },
            "/api/v1/items": {
                "get": {
                    "tags": ["Items"],
                    "summary": "List items",
                    "description": "Get paginated list of items with optional filtering",
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "schema": {"type": "integer", "default": 1},
                            "description": "Page number",
                        },
                        {
                            "name": "per_page",
                            "in": "query",
                            "schema": {"type": "integer", "default": 20, "maximum": 100},
                            "description": "Items per page",
                        },
                        {
                            "name": "status",
                            "in": "query",
                            "schema": {
                                "type": "string",
                                "enum": ["draft", "active", "archived"],
                            },
                            "description": "Filter by status",
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "List of items",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ItemListResponse"
                                    }
                                }
                            },
                        }
                    },
                },
                "post": {
                    "tags": ["Items"],
                    "summary": "Create item",
                    "description": "Create a new item",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ItemCreate"}
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "Item created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ItemResponse"}
                                }
                            },
                        },
                        "400": {
                            "description": "Validation error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                },
            },
            "/api/v1/items/{public_id}": {
                "get": {
                    "tags": ["Items"],
                    "summary": "Get item",
                    "description": "Get a single item by public ID",
                    "parameters": [
                        {
                            "name": "public_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "format": "uuid"},
                            "description": "Item's public UUID",
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Item details",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ItemResponse"}
                                }
                            },
                        },
                        "404": {
                            "description": "Item not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                },
                "patch": {
                    "tags": ["Items"],
                    "summary": "Update item",
                    "description": "Update an existing item",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {
                            "name": "public_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "format": "uuid"},
                            "description": "Item's public UUID",
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ItemUpdate"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Item updated",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ItemResponse"}
                                }
                            },
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "404": {
                            "description": "Item not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                },
                "delete": {
                    "tags": ["Items"],
                    "summary": "Delete item",
                    "description": "Soft delete an item",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {
                            "name": "public_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "format": "uuid"},
                            "description": "Item's public UUID",
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Item deleted",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/MessageResponse"
                                    }
                                }
                            },
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "404": {
                            "description": "Item not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                },
            },
            "/api/v1/items/search": {
                "get": {
                    "tags": ["Items"],
                    "summary": "Search items",
                    "description": "Search items by name",
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Search query",
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Search results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ItemSearchResponse"
                                    }
                                }
                            },
                        },
                        "400": {
                            "description": "Missing search query",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                }
            },
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT access token",
                }
            },
            "schemas": {
                "HealthResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "data": {
                            "type": "object",
                            "properties": {
                                "status": {"type": "string", "example": "healthy"},
                                "timestamp": {
                                    "type": "string",
                                    "format": "date-time",
                                    "example": "2024-01-01T00:00:00Z",
                                },
                            },
                        },
                    },
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "example": "Error message",
                                },
                                "errors": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "nullable": True,
                                },
                            },
                        },
                    },
                },
                "MessageResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "data": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "example": "Operation successful",
                                }
                            },
                        },
                    },
                },
                "UserRegister": {
                    "type": "object",
                    "required": ["email", "password", "first_name", "last_name"],
                    "properties": {
                        "email": {
                            "type": "string",
                            "format": "email",
                            "example": "user@example.com",
                        },
                        "password": {
                            "type": "string",
                            "format": "password",
                            "minLength": 8,
                            "example": "SecurePass123!",
                        },
                        "first_name": {"type": "string", "example": "John"},
                        "last_name": {"type": "string", "example": "Doe"},
                    },
                },
                "LoginRequest": {
                    "type": "object",
                    "required": ["email", "password"],
                    "properties": {
                        "email": {
                            "type": "string",
                            "format": "email",
                            "example": "user@example.com",
                        },
                        "password": {
                            "type": "string",
                            "format": "password",
                            "example": "SecurePass123!",
                        },
                    },
                },
                "RefreshRequest": {
                    "type": "object",
                    "required": ["refresh_token"],
                    "properties": {
                        "refresh_token": {"type": "string", "example": "eyJ..."}
                    },
                },
                "TokenResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "data": {
                            "type": "object",
                            "properties": {
                                "access_token": {"type": "string", "example": "eyJ..."},
                                "refresh_token": {"type": "string", "example": "eyJ..."},
                                "token_type": {"type": "string", "example": "Bearer"},
                                "expires_in": {"type": "integer", "example": 900},
                            },
                        },
                    },
                },
                "LogoutAllResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "data": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "example": "Logged out from all devices",
                                },
                                "tokens_revoked": {"type": "integer", "example": 3},
                            },
                        },
                    },
                },
                "UserResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "data": {
                            "type": "object",
                            "properties": {
                                "public_id": {
                                    "type": "string",
                                    "format": "uuid",
                                    "example": "550e8400-e29b-41d4-a716-446655440000",
                                },
                                "email": {
                                    "type": "string",
                                    "format": "email",
                                    "example": "user@example.com",
                                },
                                "first_name": {"type": "string", "example": "John"},
                                "last_name": {"type": "string", "example": "Doe"},
                                "role": {"type": "string", "example": "user"},
                                "is_active": {"type": "boolean", "example": True},
                                "is_verified": {"type": "boolean", "example": True},
                                "created_at": {
                                    "type": "string",
                                    "format": "date-time",
                                },
                                "updated_at": {
                                    "type": "string",
                                    "format": "date-time",
                                },
                            },
                        },
                    },
                },
                "UserUpdate": {
                    "type": "object",
                    "properties": {
                        "first_name": {"type": "string", "example": "Jane"},
                        "last_name": {"type": "string", "example": "Smith"},
                    },
                },
                "PasswordChangeRequest": {
                    "type": "object",
                    "required": ["old_password", "new_password"],
                    "properties": {
                        "old_password": {
                            "type": "string",
                            "format": "password",
                            "example": "OldPass123!",
                        },
                        "new_password": {
                            "type": "string",
                            "format": "password",
                            "minLength": 8,
                            "example": "NewSecurePass456!",
                        },
                    },
                },
                "ItemCreate": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string", "maxLength": 100, "example": "My Item"},
                        "description": {
                            "type": "string",
                            "nullable": True,
                            "example": "Item description",
                        },
                        "status": {
                            "type": "string",
                            "enum": ["draft", "active", "archived"],
                            "default": "draft",
                        },
                        "priority": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 5,
                            "default": 1,
                        },
                    },
                },
                "ItemUpdate": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "maxLength": 100},
                        "description": {"type": "string", "nullable": True},
                        "status": {
                            "type": "string",
                            "enum": ["draft", "active", "archived"],
                        },
                        "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                    },
                },
                "ItemResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "data": {
                            "type": "object",
                            "properties": {
                                "public_id": {"type": "string", "format": "uuid"},
                                "name": {"type": "string"},
                                "description": {"type": "string", "nullable": True},
                                "status": {
                                    "type": "string",
                                    "enum": ["draft", "active", "archived"],
                                },
                                "priority": {"type": "integer"},
                                "created_at": {"type": "string", "format": "date-time"},
                                "updated_at": {"type": "string", "format": "date-time"},
                            },
                        },
                    },
                },
                "ItemListResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "data": {
                            "type": "object",
                            "properties": {
                                "items": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/ItemData"},
                                },
                                "pagination": {
                                    "$ref": "#/components/schemas/Pagination"
                                },
                            },
                        },
                    },
                },
                "ItemSearchResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "data": {
                            "type": "object",
                            "properties": {
                                "items": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/ItemData"},
                                },
                                "count": {"type": "integer", "example": 5},
                            },
                        },
                    },
                },
                "ItemData": {
                    "type": "object",
                    "properties": {
                        "public_id": {"type": "string", "format": "uuid"},
                        "name": {"type": "string"},
                        "description": {"type": "string", "nullable": True},
                        "status": {
                            "type": "string",
                            "enum": ["draft", "active", "archived"],
                        },
                        "priority": {"type": "integer"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                    },
                },
                "Pagination": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "example": 1},
                        "per_page": {"type": "integer", "example": 20},
                        "total": {"type": "integer", "example": 100},
                        "pages": {"type": "integer", "example": 5},
                        "has_next": {"type": "boolean", "example": True},
                        "has_prev": {"type": "boolean", "example": False},
                    },
                },
            },
        },
    }


@docs_bp.route("/openapi.json")
def openapi_spec():
    """
    Serve OpenAPI specification as JSON.

    Returns
    -------
    Response
        JSON response with OpenAPI specification
    """
    return jsonify(get_openapi_spec())


# Swagger UI HTML template
SWAGGER_UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - API Documentation</title>
    <link rel="stylesheet" type="text/css" href="{{ swagger_ui_url }}swagger-ui.css">
    <style>
        html { box-sizing: border-box; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin: 0; background: #fafafa; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="{{ swagger_ui_url }}swagger-ui-bundle.js"></script>
    <script src="{{ swagger_ui_url }}swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "{{ spec_url }}",
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                layout: "StandaloneLayout",
                deepLinking: true,
                showExtensions: true,
                showCommonExtensions: true
            });
            window.ui = ui;
        };
    </script>
</body>
</html>
"""


@docs_bp.route("/swagger")
def swagger_ui():
    """
    Serve Swagger UI for interactive API documentation.

    Returns
    -------
    str
        Rendered Swagger UI HTML page
    """
    return render_template_string(
        SWAGGER_UI_TEMPLATE,
        title=settings.API_TITLE,
        swagger_ui_url=settings.OPENAPI_SWAGGER_UI_URL,
        spec_url="/api/docs/openapi.json",
    )


@docs_bp.route("")
def docs_index():
    """
    Redirect to Swagger UI.

    Returns
    -------
    str
        Redirect response to Swagger UI
    """
    return swagger_ui()
