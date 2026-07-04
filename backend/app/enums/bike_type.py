from enum import Enum


class BikeType(str, Enum):
    ELECTRO  = "Электровелосипед"
    MECHANIC = "Механический велосипед"