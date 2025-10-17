"""
Pytest configuration and fixtures.

This module provides test fixtures for the Flask application including:
- Application factory with test configuration
- Database session with automatic cleanup
- Test client for API requests
- Authentication helpers
"""

import os

# Set test environment variables BEFORE importing app
# This ensures pydantic-settings uses these values
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FLASK_ENV"] = "testing"

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app, db
from app.core.security.jwt import token_service
from app.models.item import Item, ItemStatus
from app.models.user import User


@pytest.fixture(scope="session")
def app() -> Flask:
    """
    Create test application with test configuration.

    Uses an in-memory SQLite database for fast tests.
    Scope is session to reuse app across all tests.

    Returns
    -------
    Flask
        Configured Flask application for testing
    """
    app = create_app()
    app.config["TESTING"] = True

    # Create tables
    with app.app_context():
        db.create_all()

    yield app

    # Cleanup
    with app.app_context():
        db.drop_all()


@pytest.fixture(scope="function")
def db_session(app: Flask):
    """
    Database session with automatic rollback after each test.

    Creates a nested transaction that rolls back after each test,
    ensuring test isolation without recreating tables.

    Parameters
    ----------
    app : Flask
        Test application fixture

    Yields
    ------
    SQLAlchemy session
        Database session for the test
    """
    with app.app_context():
        # Start a transaction
        connection = db.engine.connect()
        transaction = connection.begin()

        # Bind session to connection
        db.session.bind = connection

        yield db.session

        # Rollback transaction after test
        db.session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(app: Flask) -> FlaskClient:
    """
    Test client for making HTTP requests.

    Parameters
    ----------
    app : Flask
        Test application fixture

    Returns
    -------
    FlaskClient
        Flask test client
    """
    return app.test_client()


@pytest.fixture(scope="function")
def test_user(app: Flask) -> User:
    """
    Create a test user for authentication tests.

    Parameters
    ----------
    app : Flask
        Test application fixture

    Returns
    -------
    User
        Test user instance with known credentials
    """
    with app.app_context():
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role="user",
            is_active=True,
            is_verified=True,
        )
        user.set_password("TestPassword123!")

        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

        yield user

        # Cleanup
        db.session.delete(user)
        db.session.commit()


@pytest.fixture(scope="function")
def admin_user(app: Flask) -> User:
    """
    Create an admin user for authorization tests.

    Parameters
    ----------
    app : Flask
        Test application fixture

    Returns
    -------
    User
        Admin user instance
    """
    with app.app_context():
        user = User(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            role="admin",
            is_active=True,
            is_verified=True,
        )
        user.set_password("AdminPassword123!")

        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

        yield user

        # Cleanup
        db.session.delete(user)
        db.session.commit()


@pytest.fixture(scope="function")
def auth_headers(test_user: User, app: Flask) -> dict:
    """
    Generate authorization headers with valid JWT token.

    Parameters
    ----------
    test_user : User
        Test user fixture
    app : Flask
        Test application fixture

    Returns
    -------
    dict
        Headers dict with Authorization bearer token
    """
    with app.app_context():
        access_token, _ = token_service.create_access_token(
            user_id=test_user.id,
            email=test_user.email,
            role=test_user.role,
        )

        return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(admin_user: User, app: Flask) -> dict:
    """
    Generate authorization headers for admin user.

    Parameters
    ----------
    admin_user : User
        Admin user fixture
    app : Flask
        Test application fixture

    Returns
    -------
    dict
        Headers dict with Authorization bearer token
    """
    with app.app_context():
        access_token, _ = token_service.create_access_token(
            user_id=admin_user.id,
            email=admin_user.email,
            role=admin_user.role,
        )

        return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def sample_item(app: Flask) -> Item:
    """
    Create a sample item for testing.

    Parameters
    ----------
    app : Flask
        Test application fixture

    Returns
    -------
    Item
        Sample item instance
    """
    with app.app_context():
        item = Item(
            name="Test Item",
            description="A test item for testing",
            status=ItemStatus.ACTIVE,
            priority=2,
        )

        db.session.add(item)
        db.session.commit()
        db.session.refresh(item)

        yield item

        # Cleanup - check if item still exists
        existing = db.session.get(Item, item.id)
        if existing:
            db.session.delete(existing)
            db.session.commit()


@pytest.fixture(scope="function")
def sample_items(app: Flask) -> list[Item]:
    """
    Create multiple sample items for list/pagination tests.

    Parameters
    ----------
    app : Flask
        Test application fixture

    Returns
    -------
    list[Item]
        List of sample items
    """
    with app.app_context():
        items = [
            Item(
                name=f"Item {i}",
                description=f"Description for item {i}",
                status=ItemStatus.ACTIVE if i % 2 == 0 else ItemStatus.DRAFT,
                priority=(i % 5) + 1,
            )
            for i in range(1, 11)
        ]

        db.session.add_all(items)
        db.session.commit()

        # Refresh all items to get IDs
        for item in items:
            db.session.refresh(item)

        yield items

        # Cleanup
        for item in items:
            existing = db.session.get(Item, item.id)
            if existing:
                db.session.delete(existing)
        db.session.commit()
