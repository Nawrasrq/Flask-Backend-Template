# Flask Backend Template

A production-ready Flask backend template following the MSCR (Model-Service-Controller-Repository) architecture pattern. Built with modern Python practices and comprehensive tooling.

## Features

- **MSCR Architecture** - Clean separation of concerns with Models, Services, Controllers, and Repositories
- **JWT Authentication** - Access and refresh token authentication with token rotation
- **Argon2 Password Hashing** - Industry-standard secure password hashing
- **Pydantic Validation** - Type-safe request/response validation with Pydantic v2
- **SQLAlchemy 2.0** - Modern async-ready ORM with type hints
- **Flask-Migrate** - Database migrations with Alembic
- **OpenAPI Documentation** - Auto-generated Swagger UI at `/api/docs/swagger`
- **Comprehensive Testing** - Pytest with 90%+ coverage target
- **Docker Ready** - Dockerfile and docker-compose for containerized deployment

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL (optional, SQLite works for development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Flask-Backend-Template
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize database**
   ```bash
   flask db upgrade
   python -m app.db.init_db
   ```

6. **Run the development server**
   ```bash
   python run.py
   ```

The API will be available at `http://localhost:5000`

## Project Structure

```
Flask-Backend-Template/
├── app/
│   ├── __init__.py          # App factory
│   ├── core/                 # Core utilities
│   │   ├── config.py         # Pydantic settings
│   │   ├── exceptions.py     # Custom exceptions
│   │   ├── middleware.py     # Auth middleware
│   │   ├── responses.py      # Response helpers
│   │   └── security/         # Security modules
│   │       ├── jwt.py        # JWT token service
│   │       ├── password.py   # Argon2 hashing
│   │       └── encryption.py # Fernet encryption
│   ├── controllers/          # API endpoints (Blueprints)
│   │   ├── auth_controller.py
│   │   ├── user_controller.py
│   │   ├── item_controller.py
│   │   └── health_controller.py
│   ├── services/             # Business logic
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   └── item_service.py
│   ├── repositories/         # Data access layer
│   │   ├── base.py           # Generic CRUD repository
│   │   ├── user_repository.py
│   │   └── item_repository.py
│   ├── models/               # SQLAlchemy models
│   │   ├── base.py           # Base model with mixins
│   │   ├── user.py
│   │   ├── item.py
│   │   └── refresh_token.py
│   ├── schemas/              # Pydantic schemas
│   │   ├── auth_schemas.py
│   │   ├── user_schemas.py
│   │   ├── item_schemas.py
│   │   └── common_schemas.py
│   └── db/
│       ├── session.py        # Database session
│       └── init_db.py        # Database seeding
├── migrations/               # Alembic migrations
├── tests/                    # Test suite
│   ├── conftest.py           # Pytest fixtures
│   ├── test_models.py
│   ├── test_repositories.py
│   ├── test_services.py
│   └── test_controllers.py
├── .env.example              # Environment template
├── requirements.txt          # Dependencies
├── pyproject.toml           # Tool configuration
├── Dockerfile               # Container build
└── docker-compose.yml       # Container orchestration
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Revoke refresh token |
| POST | `/api/v1/auth/logout-all` | Revoke all user tokens |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | Get current user profile |
| PATCH | `/api/v1/users/me` | Update profile |
| POST | `/api/v1/users/me/password` | Change password |
| POST | `/api/v1/users/me/deactivate` | Deactivate account |

### Items (Example Resource)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/items` | List items (paginated) |
| POST | `/api/v1/items` | Create item |
| GET | `/api/v1/items/<id>` | Get item |
| PATCH | `/api/v1/items/<id>` | Update item |
| DELETE | `/api/v1/items/<id>` | Delete item (soft) |
| GET | `/api/v1/items/search?q=` | Search items |

### Documentation
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/docs/swagger` | Swagger UI |
| GET | `/api/docs/openapi.json` | OpenAPI spec |
| GET | `/health` | Health check |

## Configuration

All configuration is done via environment variables. See `.env.example` for all options.

### Key Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | Required |
| `JWT_SECRET_KEY` | JWT signing key | Required |
| `DATABASE_URL` | Database connection URL | `sqlite:///app.db` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `15` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `30` |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services.py

# Run with verbose output
pytest -v

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

## Database Migrations

```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade
```

## Docker

```bash
# Build and run with docker-compose
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

## Architecture Patterns

### MSCR Pattern

1. **Models** - SQLAlchemy ORM models representing database tables
2. **Schemas** - Pydantic models for request/response validation
3. **Controllers** - Flask Blueprints handling HTTP requests
4. **Repositories** - Data access layer with CRUD operations
5. **Services** - Business logic layer between controllers and repositories

### Transaction Control

The repository pattern follows a **separation of concerns** where repositories handle database access, but services control transaction boundaries.

| Layer | Responsibility | Database Access |
|-------|----------------|-----------------|
| **Repository** | CRUD operations, provide transaction control API | Direct `db.session` access |
| **Service** | Business logic, control transaction boundaries | Only via repository methods |
| **Controller** | HTTP handling, validation | Only via service methods |

**Key Pattern:**
- **Repositories** call `flush()` to stage changes (tactical control)
- **Services** call `commit()` after successful operations (strategic control)
- This allows services to coordinate multiple repository operations in a single transaction

```python
# Service controls the transaction boundary
def register_user(self, user_data: dict, profile_data: dict) -> User:
    try:
        user = self.user_repo.create(**user_data)       # flush (gets ID)
        profile = self.profile_repo.create(**profile_data)  # flush
        self.user_repo.commit()  # Service decides when to commit
        return user
    except Exception:
        self.user_repo.rollback()  # Service handles failures
        raise
```

### Dual-ID Architecture (Integer PK + UUID)

This template uses **integer primary keys + indexed UUID column** for optimal performance and security.

| Aspect | Internal (Integer PK) | External (UUID) |
|--------|----------------------|-----------------|
| **Used for** | Foreign keys, JOINs | API endpoints, URLs |
| **Storage** | 4 bytes | 16 bytes |
| **Performance** | Faster (sequential, cache-friendly) | Indexed lookup ~1ms |
| **Security** | Never exposed externally | Safe to expose (no enumeration) |

```python
# External API uses UUIDs (security)
GET /api/v1/items/f47ac10b-58cc-4372-a567-0e02b2c3d479

# Internal database uses integers (performance)
SELECT * FROM items WHERE user_id = 42;  # 4 bytes, fast
```

### Model Mixins (DRY Principle)

Mixins provide reusable fields without being models themselves:

| Mixin | Fields | Purpose |
|-------|--------|---------|
| `PublicIdMixin` | `public_id` (UUID) | API security (prevents ID enumeration) |
| `TimestampMixin` | `created_at`, `updated_at` | Automatic timestamp tracking |
| `SoftDeleteMixin` | `is_deleted`, `deleted_at` | Soft delete pattern |

```python
# Compose mixins into models:
class User(TimestampMixin, SoftDeleteMixin, PublicIdMixin, db.Model):
    # Automatically has created_at, updated_at, is_deleted, deleted_at, public_id
    pass
```

### Soft Delete

All models inherit `SoftDeleteMixin` providing:
- `is_deleted` boolean flag
- `deleted_at` timestamp
- `soft_delete()` and `restore()` methods

### Enum Best Practices

Use `str, PyEnum` (multiple inheritance) for better API serialization:

```python
class ItemStatus(str, PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"

# Benefits:
status = ItemStatus.ACTIVE
print(status)        # "active" (string, not ItemStatus.ACTIVE)
json.dumps(status)   # Works automatically
status == "active"   # True (string comparison works)
```

### Race Condition Prevention

Use **defense in depth** for uniqueness constraints:

1. **Application check** (fast path - catches 99% of duplicates)
2. **Database constraint** (safety net - guarantees correctness)
3. **IntegrityError handler** (clean error messages)

```python
def create_user(self, email: str) -> User:
    try:
        if self.find_by_email(email):  # 1. Optimistic check
            raise ConflictError("Email exists")

        user = User(email=email)
        self.session.add(user)
        self.flush()  # 2. Constraint violation if race occurred
        return user

    except IntegrityError:  # 3. Catch race condition
        self.rollback()
        raise ConflictError("Email exists")
```

## SQLAlchemy Best Practices

### Flask-SQLAlchemy Session Management

Flask-SQLAlchemy **automatically manages database sessions** tied to the request lifecycle:

- Session created per HTTP request
- Automatic commit on successful request
- Automatic rollback on exceptions
- Session closed when request ends

### Boolean Comparisons

Avoid direct equality comparisons (`== True`, `== False`) in queries:

```python
# ❌ BAD - Triggers linter warnings
stmt = select(Item).where(Item.is_deleted == False)

# ✅ GOOD - Use .is_(False) for False checks
stmt = select(Item).where(Item.is_deleted.is_(False))

# ✅ GOOD - Direct reference for True checks
stmt = select(Item).where(Item.is_active)
```

### `default` vs `server_default`

Use both for production templates:

```python
is_active: Mapped[bool] = mapped_column(
    default=True,           # Python-level (ORM creates)
    server_default="true",  # Database-level (SQL, migrations)
)
```

### DateTime Best Practices

Always use `datetime.now(timezone.utc)` for Python 3.8+ compatibility:

```python
from datetime import datetime, timezone

# ✅ GOOD - Works in Python 3.8+
now = datetime.now(timezone.utc)

# ❌ BAD - Only Python 3.11+
now = datetime.now(UTC)
```

## Type Hints

This template uses **Python 3.9+ compatible** type hints:

```python
# Built-in generics (Python 3.9+)
def get_items() -> list[Item]:
    ...

# Union types (Python 3.10+)
def find_user(id: int) -> User | None:
    ...
```

### Bound TypeVars for Repositories

Use bound TypeVars for type-safe generic repositories:

```python
from typing import TypeVar, Generic
from sqlalchemy.orm import DeclarativeBase

# Bound to DeclarativeBase for type safety
ModelType = TypeVar("ModelType", bound=DeclarativeBase)

class BaseRepository(Generic[ModelType]):
    def get_by_id(self, id: int) -> ModelType | None:
        # Type checker knows ModelType has model attributes
        ...
```

## Security Features

- **Argon2id** password hashing (memory-hard, resistant to GPU attacks)
- **JWT** with refresh token rotation
- **Token families** to detect refresh token reuse attacks
- **Fernet** symmetric encryption for sensitive data
- **CORS** configuration
- **Input validation** via Pydantic

## Test Users (Development)

After running `init_db.py`:

| Email | Password | Role |
|-------|----------|------|
| `admin@example.com` | `TestPassword123!` | admin |
| `user@example.com` | `TestPassword123!` | user |

## License

MIT License
