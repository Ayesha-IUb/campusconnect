import sys
from app.activity import service as _implementation
sys.modules[__name__] = _implementation
