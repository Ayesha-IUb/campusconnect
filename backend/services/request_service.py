import sys
from app.requests import service as _implementation

sys.modules[__name__] = _implementation
