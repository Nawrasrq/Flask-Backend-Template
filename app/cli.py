"""
Flask CLI commands for administrative tasks.

Usage:
    flask seed         # Seed database with test data
    flask create-user  # Create a new user interactively
    flask routes       # List all registered routes (built-in)
"""

import click
from flask import Flask
from flask.cli import with_appcontext

from app import db
from app.models.item import Item, ItemStatus
from app.models.user import User


def register_commands(app: Flask) -> None:
    """
    Register CLI commands with Flask application.

    Parameters
    ----------
    app : Flask
        Flask application instance
    """

    @app.cli.command("seed")
    @with_appcontext
    def seed_database():
        """Seed database with sample data."""
        click.echo("Seeding database...")

        # Seed users
        if User.query.first() is None:
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

            for user in users:
                user.set_password("TestPassword123!")

            db.session.add_all(users)
            db.session.commit()
            click.echo(f"  Created {len(users)} users")
        else:
            click.echo("  Users already exist, skipping")

        # Seed items
        if Item.query.first() is None:
            items = [
                Item(
                    name="Sample Item 1",
                    description="This is a draft sample item",
                    status=ItemStatus.DRAFT,
                    priority=1,
                ),
                Item(
                    name="Sample Item 2",
                    description="This is an active sample item",
                    status=ItemStatus.ACTIVE,
                    priority=3,
                ),
                Item(
                    name="Sample Item 3",
                    description="This is an archived sample item",
                    status=ItemStatus.ARCHIVED,
                    priority=2,
                ),
            ]

            db.session.add_all(items)
            db.session.commit()
            click.echo(f"  Created {len(items)} items")
        else:
            click.echo("  Items already exist, skipping")

        click.echo("Database seeding complete!")

    @app.cli.command("create-user")
    @click.option("--email", prompt=True, help="User email address")
    @click.option(
        "--password",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="User password",
    )
    @click.option("--first-name", prompt=True, help="First name")
    @click.option("--last-name", prompt=True, help="Last name")
    @click.option(
        "--role",
        default="user",
        type=click.Choice(["user", "admin", "moderator"]),
        help="User role",
    )
    @click.option("--verified/--no-verified", default=False, help="Mark as verified")
    @with_appcontext
    def create_user(email, password, first_name, last_name, role, verified):
        """Create a new user interactively."""
        # Check if email exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            click.echo(f"Error: User with email {email} already exists", err=True)
            return

        # Validate password length
        if len(password) < 8:
            click.echo("Error: Password must be at least 8 characters", err=True)
            return

        # Create user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True,
            is_verified=verified,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        click.echo(f"Created user: {email} (role: {role}, verified: {verified})")

    @app.cli.command("list-users")
    @click.option("--role", help="Filter by role")
    @click.option("--active/--inactive", default=None, help="Filter by active status")
    @with_appcontext
    def list_users(role, active):
        """List all users."""
        query = User.query.filter(User.is_deleted.is_(False))

        if role:
            query = query.filter(User.role == role)
        if active is not None:
            query = query.filter(User.is_active == active)

        users = query.all()

        if not users:
            click.echo("No users found")
            return

        click.echo(f"{'ID':<5} {'Email':<30} {'Name':<25} {'Role':<10} {'Active':<8}")
        click.echo("-" * 78)

        for user in users:
            name = f"{user.first_name} {user.last_name}"
            active_str = "Yes" if user.is_active else "No"
            click.echo(
                f"{user.id:<5} {user.email:<30} {name:<25} {user.role:<10} {active_str:<8}"
            )

        click.echo(f"\nTotal: {len(users)} users")

    @app.cli.command("deactivate-user")
    @click.argument("email")
    @click.confirmation_option(prompt="Are you sure you want to deactivate this user?")
    @with_appcontext
    def deactivate_user(email):
        """Deactivate a user by email."""
        user = User.query.filter_by(email=email, is_deleted=False).first()

        if not user:
            click.echo(f"Error: User with email {email} not found", err=True)
            return

        if not user.is_active:
            click.echo(f"User {email} is already deactivated")
            return

        user.is_active = False
        db.session.commit()

        click.echo(f"Deactivated user: {email}")

    @app.cli.command("reset-password")
    @click.argument("email")
    @click.option(
        "--password",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="New password",
    )
    @with_appcontext
    def reset_password(email, password):
        """Reset a user's password."""
        user = User.query.filter_by(email=email, is_deleted=False).first()

        if not user:
            click.echo(f"Error: User with email {email} not found", err=True)
            return

        if len(password) < 8:
            click.echo("Error: Password must be at least 8 characters", err=True)
            return

        user.set_password(password)
        db.session.commit()

        click.echo(f"Password reset for user: {email}")

    @app.cli.command("db-stats")
    @with_appcontext
    def db_stats():
        """Show database statistics."""
        user_count = User.query.filter(User.is_deleted.is_(False)).count()
        active_users = User.query.filter(
            User.is_deleted.is_(False), User.is_active.is_(True)
        ).count()
        item_count = Item.query.filter(Item.is_deleted.is_(False)).count()

        click.echo("Database Statistics")
        click.echo("=" * 30)
        click.echo(f"Total Users:  {user_count}")
        click.echo(f"Active Users: {active_users}")
        click.echo(f"Total Items:  {item_count}")
