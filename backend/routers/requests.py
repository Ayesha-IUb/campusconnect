import sys
from app.requests import router as _implementation

sys.modules[__name__] = _implementation
