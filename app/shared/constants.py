"""Application-wide constants."""

import enum


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class SortOrder(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"
