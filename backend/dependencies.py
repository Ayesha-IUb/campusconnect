import sys
from app.core import dependencies as _implementation
sys.modules[__name__] = _implementation
