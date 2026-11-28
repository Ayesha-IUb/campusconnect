import sys
from app.rbac import permissions as _implementation
sys.modules[__name__] = _implementation
