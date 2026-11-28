import sys
from app.requests import repository as _implementation

sys.modules[__name__] = _implementation
