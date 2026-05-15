import csv
import json

from django.core.exceptions import ValidationError

from vehicles.models import Brand, Vehicle

from vehicles.services.dto import VehicleImportDTO


class UnsupportedFileFormat(Exception):
    pass


class InvalidImportFile(Exception):
    pass


class VehicleImporter:

    def import_file(
        self,
        file,
        enterprise_id,
    ):
        if file.name.endswith(".csv"):
            rows = self._import_csv(file)

        elif file.name.endswith(".json"):
            rows = self._import_json(file)

        else:
            raise UnsupportedFileFormat()

        dtos = self._build_dtos(rows)

        return self._import_rows(
            dtos=dtos,
            enterprise_id=enterprise_id,
        )

    # -------------------------
    # parsing layer (raw input)
    # -------------------------

    def _import_csv(self, file):
        try:
            decoded_file = (
                file.read()
                .decode("utf-8")
                .splitlines()
            )

            reader = csv.DictReader(decoded_file)
            return list(reader)

        except Exception:
            raise InvalidImportFile()

    def _import_json(self, file):
        try:
            data = json.load(file)

        except json.JSONDecodeError:
            raise InvalidImportFile()

        if isinstance(data, dict) and "vehicle" in data:
            return [data["vehicle"]]

        if isinstance(data, list):
            return data

        raise InvalidImportFile()

    # -------------------------
    # DTO mapping layer
    # -------------------------

    def _build_dtos(self, rows):
        dtos = []

        for row in rows:
            if not isinstance(row, dict):
                continue

            brand = row.get("brand")
            if not brand:
                continue

            dtos.append(
                VehicleImportDTO(
                    brand=brand,
                    prod_date=row.get("prod_date"),
                    car_purchase_time=row.get("car_purchase_time"),
                    odometer=int(row.get("odometer") or 0),
                    price=int(row.get("price") or 0),
                    color=row.get("color"),
                    plate_number=row.get("plate_number"),
                )
            )

        return dtos

    def _import_rows(
        self,
        dtos: list[VehicleImportDTO],
        enterprise_id,
    ):
        imported_count = 0
        warnings = []

        for dto in dtos:
            result = self._create_vehicle(dto, enterprise_id)

            if result["status"] == "success":
                imported_count += 1

            elif result["status"] == "warning":
                warnings.append(result["message"])

        return {
            "count": imported_count,
            "warnings": warnings,
        }

    def _create_vehicle(
        self,
        dto: VehicleImportDTO,
        enterprise_id,
    ):
        try:
            brand = Brand.objects.get(
                product_name=dto.brand
            )

        except Brand.DoesNotExist:
            return {
                "status": "warning",
                "message": (
                    f"Бренд '{dto.brand}' не найден. "
                    "Автомобиль пропущен."
                ),
            }

        try:
            Vehicle.objects.create(
                prod_date=dto.prod_date,
                car_purchase_time=dto.car_purchase_time,
                odometer=dto.odometer,
                price=dto.price,
                color=dto.color,
                plate_number=dto.plate_number,
                brand=brand,
                enterprise_id=enterprise_id,
            )

            return {"status": "success"}

        except ValidationError:
            return {
                "status": "warning",
                "message": "Ошибка валидации при создании автомобиля",
            }

        except Exception:
            return {
                "status": "warning",
                "message": "Ошибка при импорте автомобиля",
            }