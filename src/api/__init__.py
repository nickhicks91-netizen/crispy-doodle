"""
API Layer (v4.2.1)
-------------------
FastAPI-based REST API for EchoZero.

Fixes from v4.2.0:
- Rate limiting (Issue #15 resolved)
- Input validation (Issue #12 resolved)
- Proper error handling
- WebSocket support
"""

from .server import app

__all__ = ['app']
