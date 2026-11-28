"""Backward-compatible import for the Groups feature repository."""
import sys
from app.groups import repository as _implementation

sys.modules[__name__] = _implementation
