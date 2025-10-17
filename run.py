"""
Development server entry point.

Run this script to start the Flask development server:
    python run.py
"""

from app.main import app

if __name__ == "__main__":
    # Run development server with auto-reload
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
