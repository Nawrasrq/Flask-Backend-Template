"""
Tests for controller layer (API endpoints).

Tests HTTP endpoints including:
- Health check
- Authentication endpoints
- User profile endpoints
- Item CRUD endpoints
"""

import pytest

from sqlalchemy import select

from app import db
from app.models.item import Item
from app.models.refresh_token import RefreshToken
from app.models.user import User


class TestHealthController:
    """Tests for health check endpoint."""

    @pytest.mark.unit
    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        assert "timestamp" in data["data"]


class TestAuthController:
    """Tests for authentication endpoints."""

    @pytest.mark.integration
    def test_register_success(self, client, app):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "SecurePassword123!",
                "first_name": "New",
                "last_name": "User",
            },
            content_type="application/json",
        )

        assert response.status_code == 201

        data = response.get_json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "Bearer"

        # Cleanup
        with app.app_context():
            user = db.session.execute(
                select(User).where(User.email == "newuser@test.com")
            ).scalar_one_or_none()
            if user:
                db.session.execute(
                    RefreshToken.__table__.delete().where(
                        RefreshToken.user_id == user.id
                    )
                )
                db.session.delete(user)
                db.session.commit()

    @pytest.mark.unit
    def test_register_duplicate_email(self, client, test_user):
        """Test registration fails with duplicate email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePassword123!",
                "first_name": "Duplicate",
                "last_name": "User",
            },
            content_type="application/json",
        )

        assert response.status_code == 409

        data = response.get_json()
        assert data["success"] is False

    @pytest.mark.unit
    def test_register_invalid_email(self, client):
        """Test registration fails with invalid email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePassword123!",
                "first_name": "Invalid",
                "last_name": "Email",
            },
            content_type="application/json",
        )

        assert response.status_code == 400

    @pytest.mark.unit
    def test_register_weak_password(self, client):
        """Test registration fails with weak password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@test.com",
                "password": "weak",
                "first_name": "Weak",
                "last_name": "Password",
            },
            content_type="application/json",
        )

        assert response.status_code == 400

    @pytest.mark.integration
    def test_login_success(self, client, test_user, app):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
            },
            content_type="application/json",
        )

        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

        # Cleanup
        with app.app_context():
            db.session.execute(
                RefreshToken.__table__.delete().where(
                    RefreshToken.user_id == test_user.id
                )
            )
            db.session.commit()

    @pytest.mark.unit
    def test_login_wrong_password(self, client, test_user):
        """Test login fails with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123!",
            },
            content_type="application/json",
        )

        assert response.status_code == 401

    @pytest.mark.unit
    def test_login_nonexistent_user(self, client):
        """Test login fails with nonexistent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "SomePassword123!",
            },
            content_type="application/json",
        )

        assert response.status_code == 401

    @pytest.mark.integration
    def test_refresh_tokens(self, client, test_user, app):
        """Test token refresh."""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
            },
            content_type="application/json",
        )

        refresh_token = login_response.get_json()["data"]["refresh_token"]

        # Refresh
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
            content_type="application/json",
        )

        assert response.status_code == 200

        data = response.get_json()
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

        # Cleanup
        with app.app_context():
            db.session.execute(
                RefreshToken.__table__.delete().where(
                    RefreshToken.user_id == test_user.id
                )
            )
            db.session.commit()

    @pytest.mark.integration
    def test_logout(self, client, test_user, app):
        """Test logout."""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
            },
            content_type="application/json",
        )

        refresh_token = login_response.get_json()["data"]["refresh_token"]

        # Logout
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            content_type="application/json",
        )

        assert response.status_code == 200

        # Cleanup
        with app.app_context():
            db.session.execute(
                RefreshToken.__table__.delete().where(
                    RefreshToken.user_id == test_user.id
                )
            )
            db.session.commit()

    @pytest.mark.integration
    def test_logout_all(self, client, test_user, auth_headers, app):
        """Test logout from all devices."""
        # Login a few times to create multiple tokens
        for _ in range(3):
            client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "TestPassword123!",
                },
                content_type="application/json",
            )

        # Logout all
        response = client.post(
            "/api/v1/auth/logout-all",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.get_json()
        assert data["data"]["tokens_revoked"] >= 3

        # Cleanup
        with app.app_context():
            db.session.execute(
                RefreshToken.__table__.delete().where(
                    RefreshToken.user_id == test_user.id
                )
            )
            db.session.commit()


class TestUserController:
    """Tests for user profile endpoints."""

    @pytest.mark.unit
    def test_get_profile(self, client, auth_headers, test_user):
        """Test getting current user profile."""
        response = client.get(
            "/api/v1/users/me",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["email"] == "test@example.com"
        assert "password" not in data["data"]
        assert "password_hash" not in data["data"]

    @pytest.mark.unit
    def test_get_profile_unauthorized(self, client):
        """Test getting profile without auth returns 401."""
        response = client.get("/api/v1/users/me")

        assert response.status_code == 401

    @pytest.mark.unit
    def test_update_profile(self, client, auth_headers, test_user):
        """Test updating user profile."""
        response = client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={
                "first_name": "Updated",
                "last_name": "Name",
            },
            content_type="application/json",
        )

        assert response.status_code == 200

        data = response.get_json()
        assert data["data"]["first_name"] == "Updated"
        assert data["data"]["last_name"] == "Name"

    @pytest.mark.integration
    def test_change_password(self, client, app):
        """Test changing password."""
        with app.app_context():
            # Create test user
            user = User(
                email="pwchange@test.com",
                first_name="Password",
                last_name="Change",
            )
            user.set_password("OldPassword123!")
            db.session.add(user)
            db.session.commit()

            # Get auth headers
            from app.core.security.jwt import token_service

            access_token, _ = token_service.create_access_token(
                user_id=user.id,
                email=user.email,
                role=user.role,
            )
            headers = {"Authorization": f"Bearer {access_token}"}

        response = client.post(
            "/api/v1/users/me/password",
            headers=headers,
            json={
                "old_password": "OldPassword123!",
                "new_password": "NewPassword456!",
            },
            content_type="application/json",
        )

        assert response.status_code == 200

        # Verify new password works
        with app.app_context():
            user = db.session.execute(
                select(User).where(User.email == "pwchange@test.com")
            ).scalar_one_or_none()
            assert user.check_password("NewPassword456!")

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    @pytest.mark.unit
    def test_change_password_wrong_old(self, client, auth_headers):
        """Test change password fails with wrong old password."""
        response = client.post(
            "/api/v1/users/me/password",
            headers=auth_headers,
            json={
                "old_password": "WrongOldPassword!",
                "new_password": "NewPassword456!",
            },
            content_type="application/json",
        )

        assert response.status_code == 401


class TestItemController:
    """Tests for item CRUD endpoints."""

    @pytest.mark.unit
    def test_list_items(self, client, sample_items):
        """Test listing items."""
        response = client.get("/api/v1/items")

        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "pagination" in data["data"]
        assert len(data["data"]["items"]) > 0

    @pytest.mark.unit
    def test_list_items_pagination(self, client, sample_items):
        """Test item list pagination."""
        response = client.get("/api/v1/items?page=1&per_page=3")

        assert response.status_code == 200

        data = response.get_json()
        assert len(data["data"]["items"]) == 3
        assert data["data"]["pagination"]["page"] == 1
        assert data["data"]["pagination"]["per_page"] == 3

    @pytest.mark.unit
    def test_list_items_filter_status(self, client, sample_items):
        """Test filtering items by status."""
        response = client.get("/api/v1/items?status=active")

        assert response.status_code == 200

        data = response.get_json()
        for item in data["data"]["items"]:
            assert item["status"] == "active"

    @pytest.mark.unit
    def test_get_item(self, client, sample_item, app):
        """Test getting single item."""
        with app.app_context():
            item = db.session.get(Item, sample_item.id)
            public_id = item.public_id

        response = client.get(f"/api/v1/items/{public_id}")

        assert response.status_code == 200

        data = response.get_json()
        assert data["data"]["public_id"] == public_id

    @pytest.mark.unit
    def test_get_item_not_found(self, client):
        """Test getting non-existent item returns 404."""
        response = client.get("/api/v1/items/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404

    @pytest.mark.unit
    def test_search_items(self, client, sample_items):
        """Test searching items."""
        response = client.get("/api/v1/items/search?q=Item")

        assert response.status_code == 200

        data = response.get_json()
        assert "items" in data["data"]
        assert "count" in data["data"]
        assert data["data"]["count"] > 0

    @pytest.mark.unit
    def test_search_items_no_query(self, client):
        """Test search without query returns error."""
        response = client.get("/api/v1/items/search")

        assert response.status_code == 400

    @pytest.mark.integration
    def test_create_item(self, client, auth_headers, app):
        """Test creating an item."""
        response = client.post(
            "/api/v1/items",
            headers=auth_headers,
            json={
                "name": "New Test Item",
                "description": "Created via API",
                "status": "active",
                "priority": 3,
            },
            content_type="application/json",
        )

        assert response.status_code == 201

        data = response.get_json()
        assert data["data"]["name"] == "New Test Item"
        assert data["data"]["status"] == "active"

        # Cleanup
        with app.app_context():
            item = db.session.execute(
                select(Item).where(Item.name == "New Test Item")
            ).scalar_one_or_none()
            if item:
                db.session.delete(item)
                db.session.commit()

    @pytest.mark.unit
    def test_create_item_unauthorized(self, client):
        """Test creating item without auth returns 401."""
        response = client.post(
            "/api/v1/items",
            json={"name": "Unauthorized Item"},
            content_type="application/json",
        )

        assert response.status_code == 401

    @pytest.mark.unit
    def test_create_item_invalid_data(self, client, auth_headers):
        """Test creating item with invalid data returns 400."""
        response = client.post(
            "/api/v1/items",
            headers=auth_headers,
            json={},  # Missing required name
            content_type="application/json",
        )

        assert response.status_code == 400

    @pytest.mark.integration
    def test_update_item(self, client, auth_headers, sample_item, app):
        """Test updating an item."""
        with app.app_context():
            item = db.session.get(Item, sample_item.id)
            public_id = item.public_id

        response = client.patch(
            f"/api/v1/items/{public_id}",
            headers=auth_headers,
            json={"name": "Updated Item Name"},
            content_type="application/json",
        )

        assert response.status_code == 200

        data = response.get_json()
        assert data["data"]["name"] == "Updated Item Name"

    @pytest.mark.unit
    def test_update_item_not_found(self, client, auth_headers):
        """Test updating non-existent item returns 404."""
        response = client.patch(
            "/api/v1/items/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
            json={"name": "Updated"},
            content_type="application/json",
        )

        assert response.status_code == 404

    @pytest.mark.integration
    def test_delete_item(self, client, auth_headers, app):
        """Test deleting an item."""
        # Create item to delete
        with app.app_context():
            item = Item(name="To Delete")
            db.session.add(item)
            db.session.commit()
            public_id = item.public_id
            item_id = item.id

        response = client.delete(
            f"/api/v1/items/{public_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200

        # Verify soft deleted
        with app.app_context():
            item = db.session.get(Item, item_id)
            assert item.is_deleted is True

            # Cleanup
            db.session.delete(item)
            db.session.commit()

    @pytest.mark.unit
    def test_delete_item_unauthorized(self, client, sample_item, app):
        """Test deleting item without auth returns 401."""
        with app.app_context():
            item = db.session.get(Item, sample_item.id)
            public_id = item.public_id

        response = client.delete(f"/api/v1/items/{public_id}")

        assert response.status_code == 401


class TestDocsController:
    """Tests for API documentation endpoints."""

    @pytest.mark.unit
    def test_openapi_spec(self, client):
        """Test OpenAPI spec endpoint."""
        response = client.get("/api/docs/openapi.json")

        assert response.status_code == 200

        data = response.get_json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    @pytest.mark.unit
    def test_swagger_ui(self, client):
        """Test Swagger UI endpoint."""
        response = client.get("/api/docs/swagger")

        assert response.status_code == 200
        assert b"swagger-ui" in response.data
