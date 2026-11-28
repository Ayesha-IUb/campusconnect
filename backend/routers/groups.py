import sys
from app.groups import router as _implementation
sys.modules[__name__] = _implementation
