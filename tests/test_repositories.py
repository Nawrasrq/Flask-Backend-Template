"""
Tests for repository layer.

Tests CRUD operations and custom queries including:
- BaseRepository generic methods
- UserRepository custom methods
- ItemRepository custom methods
"""

import pytest

from app import db
from app.models.item import Item, ItemStatus
from app.models.user import User
from app.repositories.item_repository import ItemRepository
from app.repositories.user_repository import UserRepository


class TestUserRepository:
    """Tests for UserRepository."""

    @pytest.mark.unit
    def test_create_user(self, app):
        """Test creating a user via repository."""
        with app.app_context():
            repo = UserRepository()

            user = repo.create_user(
                email="repo_test@example.com",
                password="SecurePassword123!",
                first_name="Repo",
                last_name="Test",
            )
            repo.commit()

            assert user.id is not None
            assert user.email == "repo_test@example.com"
            assert user.first_name == "Repo"
            assert user.check_password("SecurePassword123!")

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    @pytest.mark.unit
    def test_find_by_email(self, test_user, app):
        """Test finding user by email."""
        with app.app_context():
            repo = UserRepository()

            # Find existing user
            user = repo.find_by_email("test@example.com")
            assert user is not None
            assert user.email == "test@example.com"

            # Find non-existent user
            not_found = repo.find_by_email("nonexistent@example.com")
            assert not_found is None

    @pytest.mark.unit
    def test_get_by_public_id(self, test_user, app):
        """Test getting user by public UUID."""
        with app.app_context():
            repo = UserRepository()

            # Refresh to get public_id
            user = db.session.get(User, test_user.id)
            public_id = user.public_id

            # Find by public_id
            found = repo.get_by_public_id(public_id)
            assert found is not None
            assert found.id == test_user.id

            # Non-existent public_id
            not_found = repo.get_by_public_id("00000000-0000-0000-0000-000000000000")
            assert not_found is None

    @pytest.mark.unit
    def test_update_password(self, test_user, app):
        """Test updating user password."""
        with app.app_context():
            repo = UserRepository()

            # Update password
            result = repo.update_password(test_user.id, "NewPassword456!")
            repo.commit()

            assert result is True

            # Verify new password works
            user = db.session.get(User, test_user.id)
            assert user.check_password("NewPassword456!")
            assert not user.check_password("TestPassword123!")

    @pytest.mark.unit
    def test_deactivate_user(self, app):
        """Test deactivating a user."""
        with app.app_context():
            repo = UserRepository()

            # Create user to deactivate
            user = repo.create_user(
                email="deactivate@example.com",
                password="Password123!",
                first_name="Deactivate",
                last_name="Test",
            )
            repo.commit()

            assert user.is_active is True

            # Deactivate
            result = repo.deactivate_user(user.id)
            repo.commit()

            assert result is True

            # Verify deactivated
            updated_user = db.session.get(User, user.id)
            assert updated_user.is_active is False

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    @pytest.mark.unit
    def test_find_by_email_exists(self, test_user, app):
        """Test checking if email exists via find_by_email."""
        with app.app_context():
            repo = UserRepository()

            # Email exists
            user = repo.find_by_email("test@example.com")
            assert user is not None

            # Email doesn't exist
            user = repo.find_by_email("nonexistent@example.com")
            assert user is None


class TestItemRepository:
    """Tests for ItemRepository."""

    @pytest.mark.unit
    def test_create_item(self, app):
        """Test creating an item via repository."""
        with app.app_context():
            repo = ItemRepository()

            item = repo.create(
                name="Repo Test Item",
                description="Created via repository",
                status=ItemStatus.ACTIVE,
                priority=3,
            )
            repo.commit()

            assert item.id is not None
            assert item.name == "Repo Test Item"
            assert item.status == ItemStatus.ACTIVE

            # Cleanup
            db.session.delete(item)
            db.session.commit()

    @pytest.mark.unit
    def test_get_by_public_id(self, sample_item, app):
        """Test getting item by public UUID."""
        with app.app_context():
            repo = ItemRepository()

            item = db.session.get(Item, sample_item.id)
            public_id = item.public_id

            found = repo.get_by_public_id(public_id)
            assert found is not None
            assert found.id == sample_item.id

    @pytest.mark.unit
    def test_get_by_status_paginated(self, sample_items, app):
        """Test getting items by status with pagination."""
        with app.app_context():
            repo = ItemRepository()

            # Get active items (even numbered items in fixture)
            items, total = repo.get_by_status_paginated(
                ItemStatus.ACTIVE, skip=0, limit=10
            )

            assert len(items) > 0
            assert all(item.status == ItemStatus.ACTIVE for item in items)
            assert total >= len(items)

    @pytest.mark.unit
    def test_get_active_items_paginated(self, sample_items, app):
        """Test getting active (non-deleted) items with pagination."""
        with app.app_context():
            repo = ItemRepository()

            items, total = repo.get_active_items_paginated(skip=0, limit=5)

            assert len(items) <= 5
            assert all(not item.is_deleted for item in items)
            assert total >= len(items)

    @pytest.mark.unit
    def test_search_by_name(self, sample_items, app):
        """Test searching items by name."""
        with app.app_context():
            repo = ItemRepository()

            # Search for "Item" which all sample items contain
            results = repo.search_by_name("Item")
            assert len(results) > 0

            # Search for specific item
            results = repo.search_by_name("Item 1")
            assert len(results) >= 1

            # Search for non-existent
            results = repo.search_by_name("XYZNONEXISTENT")
            assert len(results) == 0

    @pytest.mark.unit
    def test_update_item(self, sample_item, app):
        """Test updating an item."""
        with app.app_context():
            repo = ItemRepository()

            updated = repo.update(
                sample_item.id,
                name="Updated Name",
                priority=5,
            )
            repo.commit()

            assert updated is not None
            assert updated.name == "Updated Name"
            assert updated.priority == 5

    @pytest.mark.unit
    def test_soft_delete_item(self, app):
        """Test soft deleting an item."""
        with app.app_context():
            repo = ItemRepository()

            # Create item to delete
            item = repo.create(name="To Delete")
            repo.commit()

            assert item.is_deleted is False

            # Soft delete
            result = repo.soft_delete(item.id)
            repo.commit()

            assert result is True

            # Verify deleted flag
            deleted_item = db.session.get(Item, item.id)
            assert deleted_item.is_deleted is True

            # Cleanup
            db.session.delete(deleted_item)
            db.session.commit()


class TestBaseRepositoryMethods:
    """Tests for BaseRepository generic methods."""

    @pytest.mark.unit
    def test_get_by_id(self, sample_item, app):
        """Test getting record by ID."""
        with app.app_context():
            repo = ItemRepository()

            item = repo.get_by_id(sample_item.id)
            assert item is not None
            assert item.id == sample_item.id

            # Non-existent ID
            not_found = repo.get_by_id(99999)
            assert not_found is None

    @pytest.mark.unit
    def test_get_all_with_pagination(self, sample_items, app):
        """Test getting all records with pagination."""
        with app.app_context():
            repo = ItemRepository()

            # First page
            items = repo.get_all(skip=0, limit=3)
            assert len(items) == 3

            # Second page
            items_page2 = repo.get_all(skip=3, limit=3)
            assert len(items_page2) == 3

            # Verify different items
            page1_ids = {i.id for i in items}
            page2_ids = {i.id for i in items_page2}
            assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.unit
    def test_count(self, sample_items, app):
        """Test counting records."""
        with app.app_context():
            repo = ItemRepository()

            count = repo.count()
            assert count >= 10  # At least our sample items

            # Count with filter
            active_count = repo.count(status=ItemStatus.ACTIVE)
            assert active_count > 0
            assert active_count < count

    @pytest.mark.unit
    def test_exists(self, sample_item, app):
        """Test checking record existence."""
        with app.app_context():
            repo = ItemRepository()

            item = db.session.get(Item, sample_item.id)

            # Exists by name
            assert repo.exists(name=item.name) is True

            # Does not exist
            assert repo.exists(name="NONEXISTENT_NAME_12345") is False

    @pytest.mark.unit
    def test_delete_hard(self, app):
        """Test hard delete (permanent removal)."""
        with app.app_context():
            repo = ItemRepository()

            # Create item to delete
            item = repo.create(name="Hard Delete Test")
            repo.commit()
            item_id = item.id

            # Hard delete
            result = repo.delete(item_id)
            repo.commit()

            assert result is True

            # Verify gone
            deleted = repo.get_by_id(item_id)
            assert deleted is None

    @pytest.mark.unit
    def test_rollback(self, app):
        """Test transaction rollback."""
        with app.app_context():
            repo = ItemRepository()

            # Create but don't commit
            item = repo.create(name="Rollback Test")
            repo.flush()

            # Should have an ID after flush
            assert item.id is not None
            item_id = item.id

            # Rollback
            repo.rollback()

            # Should not exist in DB
            not_found = repo.get_by_id(item_id)
            assert not_found is None
