from enum import Enum


class BikeStatus(str, Enum):
    READY = "ready"        # готов
    RENTED = "rented"      # в аренде
    REPAIR = "repair"      # ремонт
    STOLEN = "stolen"      # кража