"""Backward-compatible schema exports from feature modules."""
from app.requests.schemas import Category, RequestStatus, RequestCreate, RequestUpdate
from app.auth.schemas import RegisterInput, LoginInput
from app.users.schemas import ProfileUpdate, PasswordChange
from app.groups.schemas import (
    GroupCreate,
    GroupUpdate,
    GroupMemberInput,
    GroupRequestCreate,
    GroupRequestUpdate,
)
from app.admin.schemas import (
    RoleChange,
    BanInput,
    BulkUserAction,
    BulkDeleteInput,
    BulkRequestDeleteInput,
)
