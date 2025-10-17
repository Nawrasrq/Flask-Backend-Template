"""
Application entry point.

This module creates the Flask application instance for production
deployment with gunicorn or development server.
"""

from app import create_app

# Create Flask application instance
app = create_app()

if __name__ == "__main__":
    # Run development server
    app.run(debug=True)
