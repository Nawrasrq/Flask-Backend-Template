"""Password hashing using Argon2id (OWASP recommended)."""

import re
import secrets

from argon2 import PasswordHasher, Type
from argon2.exceptions import (
    HashingError,
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

from app.core.config import settings


class PasswordService:
    """
    FAANG-grade password hashing using Argon2id.

    Why Argon2id over bcrypt:
    - Winner of Password Hashing Competition (2015)
    - Memory-hard: resists GPU/ASIC attacks
    - Argon2id: hybrid of Argon2i (side-channel resistant) and Argon2d (GPU-resistant)
    - Recommended by OWASP for 2024+
    """

    def __init__(self):
        self._hasher = PasswordHasher(
            time_cost=settings.ARGON2_TIME_COST,
            memory_cost=settings.ARGON2_MEMORY_COST,
            parallelism=settings.ARGON2_PARALLELISM,
            hash_len=32,
            salt_len=16,
            type=Type.ID,
        )

    def hash_password(self, password: str) -> str:
        """
        Hash a password using Argon2id.

        Returns the full hash string including algorithm parameters,
        salt, and hash - allowing future parameter upgrades.
        """
        try:
            return self._hasher.hash(password)
        except HashingError as e:
            raise ValueError(f"Password hashing failed: {e}")

    def verify_password(self, password: str, hash: str) -> bool:
        """
        Verify a password against a hash.

        Uses constant-time comparison to prevent timing attacks.
        """
        try:
            self._hasher.verify(hash, password)
            return True
        except VerifyMismatchError:
            return False
        except (InvalidHashError, VerificationError):
            return False

    def needs_rehash(self, hash: str) -> bool:
        """
        Check if hash uses outdated parameters.

        Call this after successful verification to upgrade hashes
        when security parameters are increased.
        """
        try:
            return self._hasher.check_needs_rehash(hash)
        except InvalidHashError:
            return True

    @staticmethod
    def generate_temp_password(length: int = 16) -> str:
        """Generate a cryptographically secure temporary password."""
        alphabet = (
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        )
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, list[str]]:
        """
        Validate password meets security requirements.

        Returns (is_valid, list_of_violations)
        """
        violations = []

        if len(password) < settings.PASSWORD_MIN_LENGTH:
            violations.append(
                f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
            )

        if not re.search(r"[A-Z]", password):
            violations.append("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            violations.append("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            violations.append("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            violations.append("Password must contain at least one special character")

        # Check against common passwords
        common_passwords = {"password", "123456", "password123", "admin", "qwerty"}
        if password.lower() in common_passwords:
            violations.append("Password is too common")

        return len(violations) == 0, violations


# Singleton instance
password_service = PasswordService()
