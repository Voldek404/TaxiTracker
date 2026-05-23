from datetime import datetime
from pydantic import BaseModel


class EnterpriseImportDTO(BaseModel):
    name: str
    city: str
    timezone: str = "UTC"


class VehicleImportDTO(BaseModel):
    brand: str
    prod_date: str | None = None
    car_purchase_time: str | None = None
    odometer: int = 0
    price: int = 0
    color: str | None = None
    plate_number: str | None = None

class RawPointDTO(BaseModel):
    lat: float | None = None
    lng: float | None = None
    address: str | None = None
    timestamp: str | None = None


class ProcessedPointDTO(BaseModel):
    lat: float
    lng: float
    timestamp: datetime