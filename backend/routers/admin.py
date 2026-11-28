import sys
from app.admin import router as _implementation

sys.modules[__name__] = _implementation
