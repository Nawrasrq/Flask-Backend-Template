"""
Tests for service layer.

Tests business logic including:
- ItemService CRUD operations
- UserService profile management
- AuthService authentication flow
"""

import pytest

from app import db
from sqlalchemy import select

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.models.item import Item, ItemStatus
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth_schemas import LoginRequest
from app.schemas.item_schemas import ItemCreate, ItemUpdate
from app.schemas.user_schemas import UserRegister, UserUpdate
from app.services.auth_service import AuthService
from app.services.item_service import ItemService
from app.services.user_service import UserService


class TestItemService:
    """Tests for ItemService."""

    @pytest.mark.unit
    def test_create_item(self, app):
        """Test creating an item via service."""
        with app.app_context():
            service = ItemService()

            data = ItemCreate(
                name="Service Test Item",
                description="Created via service",
                status=ItemStatus.ACTIVE,
                priority=3,
            )

            item = service.create_item(data)

            assert item.id is not None
            assert item.name == "Service Test Item"
            assert item.status == ItemStatus.ACTIVE

            # Cleanup
            db.session.delete(item)
            db.session.commit()

    @pytest.mark.unit
    def test_get_item_by_public_id(self, sample_item, app):
        """Test getting item by public ID."""
        with app.app_context():
            service = ItemService()

            item = db.session.get(Item, sample_item.id)
            public_id = item.public_id

            found = service.get_item_by_public_id(public_id)

            assert found is not None
            assert found.id == sample_item.id
            assert found.name == sample_item.name

    @pytest.mark.unit
    def test_get_item_not_found(self, app):
        """Test NotFoundError when item doesn't exist."""
        with app.app_context():
            service = ItemService()

            with pytest.raises(NotFoundError) as exc_info:
                service.get_item_by_public_id("00000000-0000-0000-0000-000000000000")

            assert "not found" in str(exc_info.value.message).lower()

    @pytest.mark.unit
    def test_get_deleted_item_raises_not_found(self, app):
        """Test that getting a soft-deleted item raises NotFoundError."""
        with app.app_context():
            service = ItemService()

            # Create and soft delete an item
            data = ItemCreate(name="To Delete")
            item = service.create_item(data)
            public_id = item.public_id

            service.delete_item(public_id)

            # Should raise NotFoundError
            with pytest.raises(NotFoundError):
                service.get_item_by_public_id(public_id)

            # Cleanup
            db.session.delete(item)
            db.session.commit()

    @pytest.mark.unit
    def test_list_items_with_pagination(self, sample_items, app):
        """Test listing items with pagination."""
        with app.app_context():
            service = ItemService()

            items, pagination = service.list_items(page=1, per_page=5)

            assert len(items) == 5
            assert pagination.page == 1
            assert pagination.per_page == 5
            assert pagination.total >= 10
            assert pagination.has_next is True

    @pytest.mark.unit
    def test_list_items_filter_by_status(self, sample_items, app):
        """Test listing items filtered by status."""
        with app.app_context():
            service = ItemService()

            items, pagination = service.list_items(
                page=1, per_page=20, status=ItemStatus.ACTIVE
            )

            assert all(item.status == ItemStatus.ACTIVE for item in items)

    @pytest.mark.unit
    def test_search_items(self, sample_items, app):
        """Test searching items by name."""
        with app.app_context():
            service = ItemService()

            results = service.search_items("Item")

            assert len(results) > 0

    @pytest.mark.unit
    def test_update_item(self, sample_item, app):
        """Test updating an item."""
        with app.app_context():
            service = ItemService()

            item = db.session.get(Item, sample_item.id)
            public_id = item.public_id

            data = ItemUpdate(name="Updated Name", priority=5)
            updated = service.update_item(public_id, data)

            assert updated.name == "Updated Name"
            assert updated.priority == 5

    @pytest.mark.unit
    def test_update_item_partial(self, sample_item, app):
        """Test partial update only changes specified fields."""
        with app.app_context():
            service = ItemService()

            item = db.session.get(Item, sample_item.id)
            public_id = item.public_id
            original_description = item.description

            data = ItemUpdate(name="Only Name Changed")
            updated = service.update_item(public_id, data)

            assert updated.name == "Only Name Changed"
            assert updated.description == original_description

    @pytest.mark.unit
    def test_delete_item(self, app):
        """Test soft deleting an item."""
        with app.app_context():
            service = ItemService()

            # Create item to delete
            data = ItemCreate(name="Delete Test")
            item = service.create_item(data)
            public_id = item.public_id

            # Delete
            result = service.delete_item(public_id)

            assert result is True

            # Verify soft deleted
            db_item = db.session.get(Item, item.id)
            assert db_item.is_deleted is True

            # Cleanup
            db.session.delete(db_item)
            db.session.commit()


class TestUserService:
    """Tests for UserService."""

    @pytest.mark.unit
    def test_get_user_by_public_id(self, test_user, app):
        """Test getting user by public ID."""
        with app.app_context():
            service = UserService()

            user = db.session.get(User, test_user.id)
            public_id = user.public_id

            found = service.get_user_by_public_id(public_id)

            assert found is not None
            assert found.email == test_user.email

    @pytest.mark.unit
    def test_get_user_by_id(self, test_user, app):
        """Test getting user by internal ID."""
        with app.app_context():
            service = UserService()

            found = service.get_user_by_id(test_user.id)

            assert found is not None
            assert found.email == test_user.email

    @pytest.mark.unit
    def test_get_user_not_found(self, app):
        """Test NotFoundError when user doesn't exist."""
        with app.app_context():
            service = UserService()

            with pytest.raises(NotFoundError):
                service.get_user_by_public_id("00000000-0000-0000-0000-000000000000")

    @pytest.mark.unit
    def test_update_profile(self, test_user, app):
        """Test updating user profile."""
        with app.app_context():
            service = UserService()

            data = UserUpdate(first_name="Updated", last_name="Name")
            updated = service.update_profile_by_id(test_user.id, data)

            assert updated.first_name == "Updated"
            assert updated.last_name == "Name"

    @pytest.mark.unit
    def test_change_password_success(self, app):
        """Test successful password change."""
        with app.app_context():
            # Create user with known password
            user = User(
                email="pwchange@example.com",
                first_name="Password",
                last_name="Change",
            )
            user.set_password("OldPassword123!")
            db.session.add(user)
            db.session.commit()

            service = UserService()
            result = service.change_password(
                user_id=user.id,
                old_password="OldPassword123!",
                new_password="NewPassword456!",
            )

            assert result is True

            # Verify new password works
            db.session.refresh(user)
            assert user.check_password("NewPassword456!")

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    @pytest.mark.unit
    def test_change_password_wrong_old_password(self, test_user, app):
        """Test password change fails with wrong old password."""
        with app.app_context():
            service = UserService()

            with pytest.raises(UnauthorizedError) as exc_info:
                service.change_password(
                    user_id=test_user.id,
                    old_password="WrongOldPassword!",
                    new_password="NewPassword456!",
                )

            assert "incorrect" in str(exc_info.value.message).lower()

    @pytest.mark.unit
    def test_change_password_weak_new_password(self, app):
        """Test password change fails with weak new password."""
        with app.app_context():
            user = User(
                email="weakpw@example.com",
                first_name="Weak",
                last_name="Password",
            )
            user.set_password("StrongPassword123!")
            db.session.add(user)
            db.session.commit()

            service = UserService()

            with pytest.raises(ValidationError):
                service.change_password(
                    user_id=user.id,
                    old_password="StrongPassword123!",
                    new_password="weak",  # Too weak
                )

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    @pytest.mark.unit
    def test_change_password_same_as_old(self, app):
        """Test password change fails when new equals old."""
        with app.app_context():
            user = User(
                email="samepw@example.com",
                first_name="Same",
                last_name="Password",
            )
            user.set_password("SamePassword123!")
            db.session.add(user)
            db.session.commit()

            service = UserService()

            with pytest.raises(ValidationError) as exc_info:
                service.change_password(
                    user_id=user.id,
                    old_password="SamePassword123!",
                    new_password="SamePassword123!",
                )

            assert "different" in str(exc_info.value.message).lower()

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    @pytest.mark.unit
    def test_deactivate_account(self, app):
        """Test account deactivation."""
        with app.app_context():
            user = User(
                email="deactivate@example.com",
                first_name="Deactivate",
                last_name="Test",
            )
            user.set_password("Password123!")
            db.session.add(user)
            db.session.commit()

            service = UserService()
            result = service.deactivate_account(user.id)

            assert result is True

            db.session.refresh(user)
            assert user.is_active is False

            # Cleanup
            db.session.delete(user)
            db.session.commit()


class TestAuthService:
    """Tests for AuthService."""

    @pytest.mark.unit
    def test_register_success(self, app):
        """Test successful user registration."""
        with app.app_context():
            service = AuthService()

            data = UserRegister(
                email="newuser@example.com",
                password="SecurePassword123!",
                first_name="New",
                last_name="User",
            )

            response = service.register(data)

            assert response.access_token is not None
            assert response.refresh_token is not None
            assert response.token_type == "Bearer"
            assert response.expires_in > 0

            # Cleanup - find and delete user
            user = db.session.execute(
                select(User).where(User.email == "newuser@example.com")
            ).scalar_one_or_none()
            if user:
                # Delete refresh tokens first
                db.session.execute(
                    RefreshToken.__table__.delete().where(
                        RefreshToken.user_id == user.id
                    )
                )
                db.session.delete(user)
                db.session.commit()

    @pytest.mark.unit
    def test_register_duplicate_email(self, test_user, app):
        """Test registration fails with duplicate email."""
        with app.app_context():
            service = AuthService()

            data = UserRegister(
                email="test@example.com",  # Same as test_user
                password="SecurePassword123!",
                first_name="Duplicate",
                last_name="User",
            )

            with pytest.raises(ConflictError) as exc_info:
                service.register(data)

            assert "already" in str(exc_info.value.message).lower()

    @pytest.mark.unit
    def test_register_weak_password(self, app):
        """Test registration fails with weak password."""
        from pydantic import ValidationError as PydanticValidationError

        with app.app_context():
            # Pydantic validates password length at schema level
            with pytest.raises(PydanticValidationError):
                UserRegister(
                    email="weakpw@example.com",
                    password="weak",  # Too weak - min 8 chars
                    first_name="Weak",
                    last_name="Password",
                )

    @pytest.mark.unit
    def test_login_success(self, test_user, app):
        """Test successful login."""
        with app.app_context():
            service = AuthService()

            data = LoginRequest(
                email="test@example.com",
                password="TestPassword123!",
            )

            response = service.login(data)

            assert response.access_token is not None
            assert response.refresh_token is not None
            assert response.token_type == "Bearer"

            # Cleanup refresh token
            from app.models.refresh_token import RefreshToken

            db.session.execute(
                RefreshToken.__table__.delete().where(
                    RefreshToken.user_id == test_user.id
                )
            )
            db.session.commit()

    @pytest.mark.unit
    def test_login_wrong_password(self, test_user, app):
        """Test login fails with wrong password."""
        with app.app_context():
            service = AuthService()

            data = LoginRequest(
                email="test@example.com",
                password="WrongPassword123!",
            )

            with pytest.raises(UnauthorizedError):
                service.login(data)

    @pytest.mark.unit
    def test_login_nonexistent_user(self, app):
        """Test login fails with nonexistent user."""
        with app.app_context():
            service = AuthService()

            data = LoginRequest(
                email="nonexistent@example.com",
                password="SomePassword123!",
            )

            with pytest.raises(UnauthorizedError):
                service.login(data)

    @pytest.mark.unit
    def test_login_inactive_user(self, app):
        """Test login fails for inactive user."""
        with app.app_context():
            # Create inactive user
            user = User(
                email="inactive@example.com",
                first_name="Inactive",
                last_name="User",
                is_active=False,
            )
            user.set_password("Password123!")
            db.session.add(user)
            db.session.commit()

            service = AuthService()

            data = LoginRequest(
                email="inactive@example.com",
                password="Password123!",
            )

            with pytest.raises(UnauthorizedError):
                service.login(data)

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    @pytest.mark.integration
    def test_refresh_tokens(self, test_user, app):
        """Test token refresh flow."""
        with app.app_context():
            service = AuthService()

            # First login to get tokens
            login_data = LoginRequest(
                email="test@example.com",
                password="TestPassword123!",
            )
            initial_response = service.login(login_data)

            # Refresh tokens
            new_response = service.refresh_tokens(initial_response.refresh_token)

            assert new_response.access_token is not None
            assert new_response.refresh_token is not None
            # New tokens should be different
            assert new_response.access_token != initial_response.access_token
            assert new_response.refresh_token != initial_response.refresh_token

            # Cleanup
            from app.models.refresh_token import RefreshToken

            db.session.execute(
                RefreshToken.__table__.delete().where(
                    RefreshToken.user_id == test_user.id
                )
            )
            db.session.commit()

    @pytest.mark.unit
    def test_logout(self, test_user, app):
        """Test logout revokes refresh token."""
        with app.app_context():
            service = AuthService()

            # Login first
            login_data = LoginRequest(
                email="test@example.com",
                password="TestPassword123!",
            )
            response = service.login(login_data)

            # Logout
            service.logout(response.refresh_token)

            # Token should now be invalid
            with pytest.raises(UnauthorizedError):
                service.refresh_tokens(response.refresh_token)

            # Cleanup
            from app.models.refresh_token import RefreshToken

            db.session.execute(
                RefreshToken.__table__.delete().where(
                    RefreshToken.user_id == test_user.id
                )
            )
            db.session.commit()

    @pytest.mark.unit
    def test_logout_all(self, test_user, app):
        """Test logout all revokes all tokens."""
        with app.app_context():
            service = AuthService()

            # Login multiple times
            login_data = LoginRequest(
                email="test@example.com",
                password="TestPassword123!",
            )
            service.login(login_data)
            service.login(login_data)
            service.login(login_data)

            # Logout all
            count = service.logout_all(test_user.id)

            assert count >= 3

            # Cleanup
            from app.models.refresh_token import RefreshToken

            db.session.execute(
                RefreshToken.__table__.delete().where(
                    RefreshToken.user_id == test_user.id
                )
            )
            db.session.commit()
