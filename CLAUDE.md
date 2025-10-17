# CLAUDE.md - AI Context for Flask Backend Template

This file provides context for AI assistants (Claude, GPT, etc.) when working with this Flask backend template. It describes the architecture, patterns, and conventions used throughout the codebase.

## Project Overview

This is a **production-ready Flask backend template** following the MSCR (Model-Service-Controller-Repository) architecture pattern. It's designed to be extended into specific backend applications.

### Tech Stack

- **Framework:** Flask 3.x with Flask-SQLAlchemy 3.x
- **ORM:** SQLAlchemy 2.0 with type hints (`Mapped[]`, `mapped_column()`)
- **Validation:** Pydantic v2 for request/response schemas
- **Authentication:** JWT with refresh token rotation
- **Password Hashing:** Argon2id
- **Database:** PostgreSQL (SQLite for development/testing)
- **Testing:** pytest with pytest-flask

## Architecture: MSCR Pattern

```
Controllers (HTTP) → Services (Business Logic) → Repositories (Data Access) → Models (ORM)
     ↑                      ↑                           ↑                         ↑
  Schemas              Schemas                    db.session                  Database
```

### Layer Responsibilities

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Models** | `app/models/` | SQLAlchemy ORM models, database schema |
| **Schemas** | `app/schemas/` | Pydantic models for validation |
| **Controllers** | `app/controllers/` | Flask blueprints, HTTP handling |
| **Repositories** | `app/repositories/` | Database CRUD operations |
| **Services** | `app/services/` | Business logic, transaction control |

### Transaction Control Pattern

**Critical:** Services control transaction boundaries, repositories handle database operations.

```python
# Repository: flush() only (tactical)
def create(self, **kwargs) -> ModelType:
    instance = self.model(**kwargs)
    self.session.add(instance)
    self.flush()  # Stage changes, get ID
    return instance

# Service: commit() after business logic (strategic)
def register_user(self, data: UserRegister) -> User:
    try:
        user = self.user_repo.create(**data.model_dump())
        self.user_repo.commit()  # Service decides when to commit
        return user
    except Exception:
        self.user_repo.rollback()
        raise
```

## Key Patterns & Conventions

### 1. Dual-ID Architecture

All models use integer primary keys internally + UUID for external API exposure:

```python
# Internal: Integer PK (4 bytes, fast JOINs)
id: Mapped[int] = mapped_column(primary_key=True)

# External: UUID (prevents enumeration attacks)
public_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
```

**API Pattern:**
- External endpoints use `public_id` (UUID)
- Internal operations use `id` (integer)
- Never expose integer IDs in API responses

### 2. Model Mixins

Located in `app/models/base.py`:

| Mixin | Fields | Usage |
|-------|--------|-------|
| `PublicIdMixin` | `public_id` | Add to models exposed via API |
| `TimestampMixin` | `created_at`, `updated_at` | Add to all models |
| `SoftDeleteMixin` | `is_deleted`, `deleted_at` | Add to models needing soft delete |

```python
class User(db.Model, TimestampMixin, SoftDeleteMixin, PublicIdMixin):
    # Inherits: id, public_id, created_at, updated_at, is_deleted, deleted_at
    email: Mapped[str] = mapped_column(String(255), unique=True)
```

### 3. Custom Declarative Base

Flask-SQLAlchemy is initialized with a custom base class for type safety:

```python
# app/models/base.py
class Base(DeclarativeBase, SoftDeleteMixin):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

# app/db/session.py
db = SQLAlchemy(model_class=Base)
```

This enables:
- Type-safe repositories with `ModelType = TypeVar("ModelType", bound=Base)`
- IDE autocomplete for model attributes
- Shared `id` field across all models

### 4. Enum Pattern

Use `str, PyEnum` for API-friendly enums:

```python
from enum import Enum as PyEnum

class ItemStatus(str, PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
```

Benefits: JSON serializable, string comparisons work, clean API responses.

### 5. Boolean Queries

```python
# ❌ Avoid
query.where(Model.is_deleted == False)

# ✅ Use
query.where(Model.is_deleted.is_(False))  # For False
query.where(Model.is_active)              # For True
```

### 6. Race Condition Prevention

For unique constraints, use check-then-catch pattern:

```python
def create_user(self, email: str) -> User:
    try:
        # 1. Optimistic check (fast path)
        if self.find_by_email(email):
            raise ConflictError("Email exists")

        # 2. Create with database constraint
        user = User(email=email)
        self.session.add(user)
        self.flush()
        return user

    except IntegrityError:
        # 3. Safety net for race conditions
        self.rollback()
        raise ConflictError("Email exists")
```

## File Structure

```
app/
├── __init__.py          # App factory (create_app)
├── cli.py               # Flask CLI commands
├── core/
│   ├── config.py        # Pydantic Settings (env vars)
│   ├── exceptions.py    # Custom API exceptions
│   ├── middleware.py    # Auth decorators (@require_auth)
│   ├── responses.py     # Response helpers
│   └── security/
│       ├── jwt.py       # JWT token service
│       ├── password.py  # Argon2 password service
│       └── encryption.py # Fernet encryption
├── controllers/         # Flask blueprints
│   ├── auth_controller.py
│   ├── user_controller.py
│   ├── item_controller.py
│   └── health_controller.py
├── services/            # Business logic
│   ├── auth_service.py
│   ├── user_service.py
│   └── item_service.py
├── repositories/        # Data access
│   ├── base.py          # Generic BaseRepository[T]
│   ├── user_repository.py
│   └── item_repository.py
├── models/              # SQLAlchemy models
│   ├── base.py          # Mixins + custom Base
│   ├── user.py
│   ├── item.py
│   └── refresh_token.py
├── schemas/             # Pydantic schemas
│   ├── base.py
│   ├── auth_schemas.py
│   ├── user_schemas.py
│   └── item_schemas.py
└── db/
    ├── session.py       # SQLAlchemy db instance
    └── init_db.py       # Database seeding
```

## Adding New Features

### Adding a New Model

1. Create model in `app/models/new_model.py`:
```python
from app.db import db
from app.models.base import TimestampMixin, SoftDeleteMixin, PublicIdMixin

class NewModel(db.Model, TimestampMixin, SoftDeleteMixin, PublicIdMixin):
    __tablename__ = "new_models"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Add fields...
```

2. Export in `app/models/__init__.py`

3. Create migration: `flask db migrate -m "Add new_model table"`

4. Apply migration: `flask db upgrade`

### Adding a New Repository

1. Create `app/repositories/new_model_repository.py`:
```python
from app.repositories.base import BaseRepository
from app.models.new_model import NewModel

class NewModelRepository(BaseRepository[NewModel]):
    def __init__(self):
        super().__init__(NewModel)

    # Add custom queries...
```

### Adding a New Service

1. Create `app/services/new_model_service.py`:
```python
from app.repositories.new_model_repository import NewModelRepository
from app.schemas.new_model_schemas import NewModelCreate

class NewModelService:
    def __init__(self, repo: NewModelRepository | None = None):
        self.repo = repo or NewModelRepository()

    def create(self, data: NewModelCreate) -> NewModel:
        instance = self.repo.create(**data.model_dump())
        self.repo.commit()
        return instance
```

### Adding a New Controller

1. Create `app/controllers/new_model_controller.py`:
```python
from flask import Blueprint, request
from app.core.middleware import require_auth
from app.core.responses import success_response
from app.services.new_model_service import NewModelService
from app.schemas.new_model_schemas import NewModelCreate, NewModelResponse

new_model_bp = Blueprint("new_models", __name__, url_prefix="/api/v1/new-models")
service = NewModelService()

@new_model_bp.route("", methods=["POST"])
@require_auth
def create():
    data = NewModelCreate(**request.get_json())
    instance = service.create(data)
    return success_response(NewModelResponse.model_validate(instance).model_dump(), status=201)
```

2. Register blueprint in `app/__init__.py` → `register_blueprints()`

## Common Operations

### Authentication Flow

```python
# Login: POST /api/v1/auth/login
# Returns: { access_token, refresh_token, token_type, expires_in }

# Use access token in header:
Authorization: Bearer <access_token>

# Refresh: POST /api/v1/auth/refresh
# Body: { refresh_token }
# Returns: New token pair (old refresh token is revoked)
```

### Database Commands

```bash
# Create migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade

# Seed database
flask seed

# Create user interactively
flask create-user

# List users
flask list-users
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services.py -v
```

## Security Considerations

1. **Never expose integer IDs** - Use `public_id` (UUID) in API responses
2. **Password requirements** - Minimum 8 characters (configurable via `PASSWORD_MIN_LENGTH`)
3. **JWT tokens** - Short-lived access tokens (15 min), long-lived refresh tokens (30 days)
4. **Refresh token rotation** - Old tokens are revoked on refresh
5. **Token families** - Detect refresh token reuse attacks
6. **Database constraints** - Always add `unique=True` for uniqueness requirements

## Environment Variables

Key variables in `.env`:

```bash
# Required
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Optional (have defaults)
FLASK_ENV=development
DEBUG=True
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
```

## Extending This Template

When building a specific application from this template:

1. **Keep the MSCR pattern** - Add new models/services/controllers following existing patterns
2. **Use mixins** - Compose models from existing mixins for consistency
3. **Add domain-specific services** - Business logic goes in services, not controllers
4. **Extend schemas** - Add validation rules in Pydantic schemas
5. **Add tests** - Follow the test patterns in `tests/` directory
6. **Update OpenAPI docs** - Controllers automatically generate Swagger documentation

## Type Hints Reference

```python
# SQLAlchemy 2.0 style
from sqlalchemy.orm import Mapped, mapped_column

# Mapped column
name: Mapped[str] = mapped_column(String(100))

# Optional column
description: Mapped[str | None] = mapped_column(String(500), nullable=True)

# Foreign key
user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

# Relationship
user: Mapped["User"] = relationship(back_populates="items")
items: Mapped[list["Item"]] = relationship(back_populates="user")
```

## Troubleshooting

### Common Issues

1. **Import errors with `db.Model`**: Ensure models import `db` from `app.db`, not `app`
2. **Type checker errors on `model.id`**: The custom `Base` class defines `id` - ensure models inherit from `db.Model`
3. **Test isolation issues**: Tests use function-scoped fixtures that rollback transactions
4. **Migration conflicts**: Delete migration files and recreate if schema is significantly changed during development
