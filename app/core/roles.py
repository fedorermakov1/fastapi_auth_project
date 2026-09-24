from enum import Enum

class RoleEnum(str, Enum):
    admin = "admin"
    moderator = "moderator"
    user = "user"