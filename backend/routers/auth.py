import sys
from app.auth import router as _implementation
sys.modules[__name__] = _implementation
