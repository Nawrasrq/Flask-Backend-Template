"""
Flask application factory.

This module creates and configures the Flask application using the
factory pattern, enabling flexible configuration and testing.
"""

import logging

from flask import Flask
from flask_caching import Cache
from flask_cors import CORS
from flask_migrate import Migrate

from app.core.config import settings
from app.core.exceptions import APIException
from app.core.responses import error_response
from app.db import db

# Initialize extensions
migrate = Migrate()
cache = Cache()


def create_app() -> Flask:
    """
    Create and configure Flask application.

    Returns
    -------
    Flask
        Configured Flask application instance
    """
    # Initialize Flask app
    app = Flask(__name__)

    # Load configuration from settings
    app.config["SECRET_KEY"] = settings.SECRET_KEY.get_secret_value()
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"] = settings.DEBUG

    # Caching configuration
    app.config["CACHE_TYPE"] = settings.CACHE_TYPE
    app.config["CACHE_DEFAULT_TIMEOUT"] = settings.CACHE_DEFAULT_TIMEOUT

    # Testing configuration
    app.config["TESTING"] = settings.TESTING

    # Configure logging (basicConfig is sufficient, called once at startup)
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {settings.APP_NAME} in {settings.FLASK_ENV} mode")

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)

    # Configure CORS
    cors_origins = settings.get_cors_origins()
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})
    logger.info(f"CORS configured for origins: {cors_origins}")

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Add security headers
    add_security_headers(app)

    # Register CLI commands
    register_cli_commands(app)

    logger.info(f"{settings.APP_NAME} initialized successfully")

    return app


def register_cli_commands(app: Flask) -> None:
    """
    Register Flask CLI commands.

    Parameters
    ----------
    app : Flask
        Flask application instance
    """
    from app.cli import register_commands

    register_commands(app)


def register_blueprints(app: Flask) -> None:
    """
    Register all Flask blueprints.

    Parameters
    ----------
    app : Flask
        Flask application instance

    Returns
    -------
    None
    """
    # Import blueprints here to avoid circular imports
    from app.controllers.auth_controller import auth_bp
    from app.controllers.docs_controller import docs_bp
    from app.controllers.health_controller import health_bp
    from app.controllers.item_controller import items_bp
    from app.controllers.user_controller import users_bp

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(docs_bp)

    logger = logging.getLogger(__name__)
    logger.info("Blueprints registered successfully")


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers for common HTTP errors and custom exceptions.

    Parameters
    ----------
    app : Flask
        Flask application instance

    Returns
    -------
    None
    """

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return error_response("Resource not found", status=404)

    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error."""
        logger = logging.getLogger(__name__)
        logger.error(f"Internal server error: {error}")
        return error_response("An unexpected error occurred", status=500)

    @app.errorhandler(APIException)
    def handle_api_exception(error: APIException):
        """Handle custom API exceptions."""
        return error_response(
            message=error.message,
            status=error.status_code,
            errors=error.payload if error.payload else None,
        )

    logger = logging.getLogger(__name__)
    logger.info("Error handlers registered successfully")


def add_security_headers(app: Flask) -> None:
    """
    Add security headers to all responses.

    Parameters
    ----------
    app : Flask
        Flask application instance

    Returns
    -------
    None
    """

    @app.after_request
    def set_security_headers(response):
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        return response

    logger = logging.getLogger(__name__)
    logger.info("Security headers configured")
