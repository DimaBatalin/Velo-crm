from fastapi import APIRouter

from app.enums.bike_status import BikeStatus
from app.enums.bike_type import BikeType
from app.enums.bike_owner_type import BikeOwnerType
from app.enums.repair_status import RepairStatus
from app.enums.rental_status import RentalStatus
from app.enums.owner_type import OwnerType
from app.enums.person_status import PersonStatus


router = APIRouter(
    prefix="/enums",
    tags=["Enums"],
)


def _enum_to_list(enum_cls) -> list[dict]:
    """Возвращает список {value, label} для фронтенда."""
    labels = {
        # BikeStatus
        BikeStatus.READY:   "Готов",
        BikeStatus.RENTED:  "В аренде",
        BikeStatus.REPAIR:  "Ремонт",
        BikeStatus.STOLEN:  "Кража",
        # BikeType
        BikeType.ELECTRO:  "Электровелосипед",
        BikeType.MECHANIC: "Механический велосипед",
        # BikeOwnerType — кому принадлежит велосипед (арендодатель)
        BikeOwnerType.VM:     "Великий мастер",
        BikeOwnerType.VITALY: "Виталий",
        # RepairStatus
        RepairStatus.NEW:           "Новый",
        RepairStatus.IN_PROGRESS:   "В работе",
        RepairStatus.WAITING_PARTS: "Ожидание запчастей",
        RepairStatus.DONE:          "Выполнен",
        RepairStatus.CANCELLED:     "Отменён",
        # RentalStatus
        RentalStatus.ACTIVE:   "Активна",
        RentalStatus.RETURNED: "Возвращён",
        RentalStatus.OVERDUE:  "Просрочена",
        # OwnerType — кому принадлежат запчасти/услуги
        OwnerType.KIRILL: "Кирилл",
        OwnerType.VITALY: "Виталий",
        # PersonStatus
        PersonStatus.ACTIVE:   "Активен",
        PersonStatus.BLOCKED:  "Заблокирован",
        PersonStatus.ARCHIVED: "Архивирован",
        PersonStatus.FIRED:    "Уволен",
    }
    return [
        {"value": member.value, "label": labels.get(member, member.value)}
        for member in enum_cls
    ]


@router.get("")
async def get_all_enums():
    """Возвращает все enum-справочники для фронтенда одним запросом."""
    return {
        "bike_status":     _enum_to_list(BikeStatus),
        "bike_type":       _enum_to_list(BikeType),
        "bike_owner_type": _enum_to_list(BikeOwnerType),
        "repair_status":   _enum_to_list(RepairStatus),
        "rental_status":   _enum_to_list(RentalStatus),
        "owner_type":      _enum_to_list(OwnerType),
        "person_status":   _enum_to_list(PersonStatus),
    }
