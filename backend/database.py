import sys
from app.core import database as _implementation
sys.modules[__name__] = _implementation
