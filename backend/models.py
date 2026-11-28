"""Backward-compatible import for shared application models."""
import sys
from app.core import models as _implementation

sys.modules[__name__] = _implementation
