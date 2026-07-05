from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    MECHANIC = "mechanic"
    MANAGER = "manager"
