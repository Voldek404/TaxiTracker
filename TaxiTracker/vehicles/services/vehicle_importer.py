# services/vehicle_importer.py

import csv
import json

from django.core.exceptions import ValidationError

from vehicles.models import (
    Brand,
    Vehicle,
)


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

        return self._import_rows(
            rows=rows,
            enterprise_id=enterprise_id,
        )

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

        if (
            isinstance(data, dict)
            and "vehicle" in data
        ):
            return [data["vehicle"]]

        if isinstance(data, list):
            return data

        raise InvalidImportFile()

    def _import_rows(
        self,
        rows,
        enterprise_id,
    ):
        imported_count = 0
        warnings = []

        for row in rows:

            if not isinstance(row, dict):
                continue

            result = self._create_vehicle(
                row=row,
                enterprise_id=enterprise_id,
            )

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
        row,
        enterprise_id,
    ):

        brand_name = row.get("brand")

        if not brand_name:
            return {
                "status": "warning",
                "message": (
                    "Не указан бренд автомобиля"
                ),
            }

        try:
            brand = Brand.objects.get(
                product_name=brand_name,
            )

        except Brand.DoesNotExist:

            return {
                "status": "warning",
                "message": (
                    f"Бренд '{brand_name}' "
                    f"не найден. "
                    f"Автомобиль пропущен."
                ),
            }

        try:

            Vehicle.objects.create(
                prod_date=row.get("prod_date"),
                car_purchase_time=row.get(
                    "car_purchase_time"
                ),
                odometer=row.get(
                    "odometer",
                    0,
                ),
                price=row.get(
                    "price",
                    0,
                ),
                color=row.get("color"),
                plate_number=row.get(
                    "plate_number"
                ),
                brand=brand,
                enterprise_id=enterprise_id,
            )

            return {
                "status": "success",
            }

        except ValidationError:

            return {
                "status": "warning",
                "message": (
                    "Ошибка валидации "
                    "при создании автомобиля"
                ),
            }

        except Exception:

            return {
                "status": "warning",
                "message": (
                    "Ошибка при импорте автомобиля"
                ),
            }