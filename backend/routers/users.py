import sys
from app.users import router as _implementation
sys.modules[__name__] = _implementation
