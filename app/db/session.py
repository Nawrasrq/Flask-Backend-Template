"""
Database session management using Flask-SQLAlchemy.

This module initializes the SQLAlchemy database instance that is used
throughout the application for all database operations.
"""

from flask_sqlalchemy import SQLAlchemy

from app.models.base import Base

# Initialize SQLAlchemy instance
# This will be configured in the Flask app factory
db = SQLAlchemy(model_class=Base)
