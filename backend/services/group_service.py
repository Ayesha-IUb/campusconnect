import sys
from app.groups import service as _implementation
sys.modules[__name__] = _implementation
