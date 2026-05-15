import csv
import json

from django.core.exceptions import ValidationError

from vehicles.models import ENTERPRISE_TIMEZONES
from vehicles.models import Enterprise

from vehicles.services.dto import EnterpriseImportDTO


class UnsupportedFileFormat(Exception):
    pass


class InvalidImportFile(Exception):
    pass


class EnterpriseImporter:

    def import_file(
        self,
        file,
        manager=None,
    ):
        if file.name.endswith(".csv"):
            rows = self._import_csv(file)

        elif file.name.endswith(".json"):
            rows = self._import_json(file)

        else:
            raise UnsupportedFileFormat()

        return self._import_rows(
            rows=rows,
            manager=manager,
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
            and "enterprise" in data
        ):
            return [data["enterprise"]]

        if isinstance(data, list):
            return data

        raise InvalidImportFile()

    def _import_rows(
        self,
        rows,
        manager=None,
    ):
        imported_count = 0

        for row in rows:

            if not isinstance(row, dict):
                continue

            dto = self._build_dto(row)

            if not dto:
                continue

            enterprise = self._create_enterprise(dto)

            if not enterprise:
                continue

            imported_count += 1

            if manager:
                manager.enterprises.add(enterprise)

        return imported_count

    def _build_dto(
        self,
        row,
    ) -> EnterpriseImportDTO | None:

        name = row.get("name")
        city = row.get("city")

        if not name or not city:
            return None

        timezone = row.get(
            "timezone",
            "UTC",
        )

        if timezone not in dict(ENTERPRISE_TIMEZONES):
            timezone = "UTC"

        return EnterpriseImportDTO(
            name=name,
            city=city,
            timezone=timezone,
        )

    def _create_enterprise(
        self,
        dto: EnterpriseImportDTO,
    ):
        try:
            return Enterprise.objects.create(
                name=dto.name,
                city=dto.city,
                timezone=dto.timezone,
            )

        except ValidationError:
            return None