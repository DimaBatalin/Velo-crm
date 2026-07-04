from enum import Enum


class RepairStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    WAITING_PARTS = "waiting_parts"
    DONE = "done"
    CANCELLED = "cancelled"