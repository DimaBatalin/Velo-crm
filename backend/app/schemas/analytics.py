from pydantic import BaseModel
from pydantic import Field


class OwnerFinancials(BaseModel):
    cost: float = Field(description="Закупочная стоимость списанных запчастей")
    revenue: float = Field(description="Выручка от продажи запчастей клиенту")
    profit: float = Field(description="revenue - cost")


class PartsProfitResponse(BaseModel):
    kirill: OwnerFinancials
    vitaly: OwnerFinancials


class TopPartItem(BaseModel):
    part_id: int
    name: str
    usage_count: int = Field(description="Суммарное количество списаний (шт.)")


class TopServiceItem(BaseModel):
    service_id: int
    name: str
    usage_count: int = Field(description="Количество использований в ремонтах")


class PartConsumptionItem(BaseModel):
    part_id: int
    name: str
    quantity: int = Field(description="Списано штук за период")


class PartsConsumptionResponse(BaseModel):
    period: str
    since: str
    total_quantity: int
    items: list[PartConsumptionItem]


class ServiceRevenueItem(BaseModel):
    service_id: int
    name: str
    usage_count: int
    revenue: float


class ServicesRevenueResponse(BaseModel):
    period: str
    since: str
    total_revenue: float
    items: list[ServiceRevenueItem]
