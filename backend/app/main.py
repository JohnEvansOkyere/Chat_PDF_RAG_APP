"""
Compatibility ASGI entrypoint.

This allows starting the backend with either:
- `uvicorn main:app --reload`
- `uvicorn app.main:app --reload`
"""

from main import app

__all__ = ["app"]
