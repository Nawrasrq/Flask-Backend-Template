"""
Initialize database and seed sample data.

This script:
1. Creates the database if it doesn't exist (PostgreSQL/MySQL)
2. Applies migrations to create/update schema
3. Seeds sample data (idempotent - safe to run multiple times)

Run with: python scripts/init_db.py
"""

from flask_migrate import upgrade
from sqlalchemy_utils import create_database, database_exists

from app import create_app, db
from app.models.item import Item, ItemStatus
from app.models.user import User


def create_database_if_not_exists():
    """
    Create database if it doesn't exist.

    Works with PostgreSQL, MySQL, and SQLite.
    SQLite auto-creates the file, but this is safe to run.
    """
    database_url = db.engine.url

    if not database_exists(database_url):
        print(f"Creating database: {database_url.database}")
        create_database(database_url)
        print("[OK] Database created")
    else:
        print(f"[OK] Database already exists: {database_url.database}")


def seed_items():
    """Seed sample items."""
    # Check if items already exist
    existing_count = Item.query.count()
    if existing_count > 0:
        print(f"[OK] Items already exist ({existing_count} items). Skipping seed.")
        return

    items = [
        Item(
            name="Sample Item 1",
            description="This is a draft sample item for testing",
            status=ItemStatus.DRAFT,
            priority=1,
        ),
        Item(
            name="Sample Item 2",
            description="This is an active sample item for testing",
            status=ItemStatus.ACTIVE,
            priority=3,
        ),
        Item(
            name="Sample Item 3",
            description="This is an archived sample item for testing",
            status=ItemStatus.ARCHIVED,
            priority=2,
        ),
    ]

    db.session.add_all(items)
    db.session.commit()
    print(f"[OK] Created {len(items)} sample items")


def seed_users():
    """
    Seed test users for development.

    Creates two test users:
    - admin@example.com (admin role)
    - user@example.com (user role)

    Both have password: TestPassword123!
    """
    # Check if users already exist
    existing_count = User.query.count()
    if existing_count > 0:
        print(f"[OK] Users already exist ({existing_count} users). Skipping seed.")
        return

    users = [
        User(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            role="admin",
            is_active=True,
            is_verified=True,
        ),
        User(
            email="user@example.com",
            first_name="Test",
            last_name="User",
            role="user",
            is_active=True,
            is_verified=True,
        ),
    ]

    # Set passwords (uses Argon2 hashing)
    for user in users:
        user.set_password("TestPassword123!")

    db.session.add_all(users)
    db.session.commit()
    print(f"[OK] Created {len(users)} test users")
    print("    - admin@example.com (admin)")
    print("    - user@example.com (user)")
    print("    - Password for both: TestPassword123!")


def main():
    """Initialize database and seed data."""
    app = create_app()
    with app.app_context():
        print("=" * 50)
        print("Database Initialization")
        print("=" * 50)

        # Step 1: Create database
        print("\n1. Checking/creating database...")
        create_database_if_not_exists()

        # Step 2: Apply migrations
        print("\n2. Applying migrations...")
        upgrade()
        print("[OK] Migrations applied")

        # Step 3: Seed data
        print("\n3. Seeding sample data...")
        seed_users()
        seed_items()

        print("\n" + "=" * 50)
        print("[OK] Database initialization complete!")
        print("=" * 50)


if __name__ == "__main__":
    main()
