"""Backward-compatible import for the Admin feature service."""
import sys
from app.admin import service as _implementation

sys.modules[__name__] = _implementation
