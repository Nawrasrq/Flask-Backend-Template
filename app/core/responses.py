"""
Standardized API response helpers.

This module provides functions for creating consistent JSON responses
across all API endpoints.
"""

from datetime import datetime, timezone
from typing import Any

from flask import jsonify


def success_response(data: Any = None, status: int = 200) -> tuple:
    """
    Create standardized success response.

    Parameters
    ----------
    data : Any, optional
        Response data to return
    status : int, optional
        HTTP status code (default: 200)

    Returns
    -------
    tuple
        Flask response tuple (response, status_code)
    """
    response = {
        "success": True,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return jsonify(response), status


def error_response(
    message: str, status: int = 400, errors: dict | None = None
) -> tuple:
    """
    Create standardized error response.

    Parameters
    ----------
    message : str
        Error message
    status : int, optional
        HTTP status code (default: 400)
    errors : dict | None, optional
        Additional error details (field-level errors, etc.)

    Returns
    -------
    tuple
        Flask response tuple (response, status_code)
    """
    response = {
        "success": False,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if errors:
        response["errors"] = errors
    return jsonify(response), status
