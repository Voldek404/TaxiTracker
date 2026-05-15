from dataclasses import dataclass


@dataclass(slots=True)
class EnterpriseImportDTO:
    name: str
    city: str
    timezone: str = "UTC"