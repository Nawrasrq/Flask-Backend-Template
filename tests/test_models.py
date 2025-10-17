"""
Tests for database models.

Tests model creation, relationships, and methods including:
- User model with password hashing
- Item model with status enum
- Soft delete functionality
- Timestamp mixins
"""

import pytest
from datetime import datetime, timezone

from app import db
from app.models.item import Item, ItemStatus
from app.models.user import User


class TestUserModel:
    """Tests for User model."""

    @pytest.mark.unit
    def test_create_user(self, app):
        """Test user creation with required fields."""
        with app.app_context():
            user = User(
                email="newuser@example.com",
                first_name="New",
                last_name="User",
            )
            user.set_password("SecurePass123!")

            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.public_id is not None
            assert user.email == "newuser@example.com"
            assert user.first_name == "New"
            assert user.last_name == "User"
            assert user.role == "user"  # Default role
            assert user.is_active is True
            assert user.is_deleted is False

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    @pytest.mark.unit
    def test_password_hashing(self, app):
        """Test password is hashed and can be verified."""
        with app.app_context():
            user = User(
                email="hashtest@example.com",
                first_name="Hash",
                last_name="Test",
            )
            user.set_password("MySecurePassword123!")

            # Password should be hashed, not stored in plain text
            assert user.hashed_password is not None
            assert user.hashed_password != "MySecurePassword123!"
            assert "$argon2" in user.hashed_password  # Argon2 hash format

            # Verify correct password
            assert user.check_password("MySecurePassword123!") is True

            # Verify incorrect password
            assert user.check_password("WrongPassword") is False
            assert user.check_password("") is False

    @pytest.mark.unit
    def test_user_public_id_is_uuid(self, test_user, app):
        """Test that public_id is a valid UUID string."""
        with app.app_context():
            # Refresh to get latest state
            user = db.session.get(User, test_user.id)
            assert user.public_id is not None
            assert len(user.public_id) == 36  # UUID format
            assert user.public_id.count("-") == 4

    @pytest.mark.unit
    def test_user_soft_delete(self, app):
        """Test user soft delete sets is_deleted flag."""
        with app.app_context():
            user = User(
                email="softdelete@example.com",
                first_name="Soft",
                last_name="Delete",
            )
            user.set_password("Password123!")

            db.session.add(user)
            db.session.commit()

            assert user.is_deleted is False

            # Soft delete
            user.soft_delete()
            db.session.commit()

            assert user.is_deleted is True
            assert user.deleted_at is not None

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    @pytest.mark.unit
    def test_user_timestamps(self, app):
        """Test created_at and updated_at timestamps."""
        with app.app_context():
            before_create = datetime.now(timezone.utc)

            user = User(
                email="timestamps@example.com",
                first_name="Time",
                last_name="Stamp",
            )
            user.set_password("Password123!")

            db.session.add(user)
            db.session.commit()

            after_create = datetime.now(timezone.utc)

            # Check created_at is set and reasonable
            assert user.created_at is not None

            # Update user
            user.first_name = "Updated"
            db.session.commit()

            # updated_at should be set after update
            assert user.updated_at is not None

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    @pytest.mark.unit
    def test_user_repr(self, test_user, app):
        """Test user string representation."""
        with app.app_context():
            user = db.session.get(User, test_user.id)
            repr_str = repr(user)
            assert "User" in repr_str
            assert user.email in repr_str


class TestItemModel:
    """Tests for Item model."""

    @pytest.mark.unit
    def test_create_item(self, app):
        """Test item creation with required fields."""
        with app.app_context():
            item = Item(
                name="Test Item",
                description="Test description",
                status=ItemStatus.DRAFT,
                priority=3,
            )

            db.session.add(item)
            db.session.commit()

            assert item.id is not None
            assert item.public_id is not None
            assert item.name == "Test Item"
            assert item.description == "Test description"
            assert item.status == ItemStatus.DRAFT
            assert item.priority == 3
            assert item.is_deleted is False

            # Cleanup
            db.session.delete(item)
            db.session.commit()

    @pytest.mark.unit
    def test_item_default_values(self, app):
        """Test item default values are applied."""
        with app.app_context():
            item = Item(name="Minimal Item")

            db.session.add(item)
            db.session.commit()

            assert item.description is None
            assert item.status == ItemStatus.DRAFT  # Default status
            assert item.priority == 1  # Default priority
            assert item.is_deleted is False

            # Cleanup
            db.session.delete(item)
            db.session.commit()

    @pytest.mark.unit
    def test_item_status_enum(self, app):
        """Test item status enum values."""
        with app.app_context():
            # Test all status values
            for status in ItemStatus:
                item = Item(
                    name=f"Item with {status.value} status",
                    status=status,
                )

                db.session.add(item)
                db.session.commit()

                assert item.status == status
                assert item.status.value in ["draft", "active", "archived"]

                db.session.delete(item)
                db.session.commit()

    @pytest.mark.unit
    def test_item_soft_delete(self, sample_item, app):
        """Test item soft delete sets is_deleted flag."""
        with app.app_context():
            item = db.session.get(Item, sample_item.id)
            assert item.is_deleted is False

            # Soft delete
            item.soft_delete()
            db.session.commit()

            assert item.is_deleted is True
            assert item.deleted_at is not None

    @pytest.mark.unit
    def test_item_priority_values(self, app):
        """Test item priority accepts valid values."""
        with app.app_context():
            for priority in range(1, 6):
                item = Item(
                    name=f"Priority {priority} item",
                    priority=priority,
                )

                db.session.add(item)
                db.session.commit()

                assert item.priority == priority

                db.session.delete(item)
                db.session.commit()

    @pytest.mark.unit
    def test_item_repr(self, sample_item, app):
        """Test item string representation."""
        with app.app_context():
            item = db.session.get(Item, sample_item.id)
            repr_str = repr(item)
            assert "Item" in repr_str
            assert item.name in repr_str


class TestModelRelationships:
    """Tests for model relationships."""

    @pytest.mark.unit
    def test_user_refresh_tokens_relationship(self, test_user, app):
        """Test User has refresh_tokens relationship."""
        with app.app_context():
            user = db.session.get(User, test_user.id)
            # Should have refresh_tokens attribute (even if empty)
            assert hasattr(user, "refresh_tokens")
            assert isinstance(user.refresh_tokens, list)
