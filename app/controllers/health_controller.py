"""
Health check controller for monitoring application status.

This module provides a simple health check endpoint for monitoring
and load balancer health checks.
"""

from datetime import datetime, timezone

from flask import Blueprint

from app.core.responses import success_response

# Create health blueprint
health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.

    Returns application health status and timestamp.

    Returns
    -------
    tuple
        Success response with health status
    """
    data = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return success_response(data)
