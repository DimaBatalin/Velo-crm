from enum import Enum


class PersonStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    ARCHIVED = "archived"
    FIRED = "fired"      # уволен (для клиентов-курьеров)
