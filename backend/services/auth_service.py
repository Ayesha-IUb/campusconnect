import sys
from app.auth import service as _implementation
sys.modules[__name__] = _implementation
