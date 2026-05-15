from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class EnterpriseImportDTO:
    name: str
    city: str
    timezone: str = "UTC"


@dataclass(slots=True)
class VehicleImportDTO:
    brand: str
    prod_date: str | None = None
    car_purchase_time: str | None = None
    odometer: int = 0
    price: int = 0
    color: str | None = None
    plate_number: str | None = None