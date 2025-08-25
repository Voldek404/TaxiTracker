

# vehicles/migrations/0003_vehicledriver.py
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("vehicles", "0002_driver_is_active"),
    ]

    operations = [
        migrations.CreateModel(
            name="VehicleDriver",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_active", models.BooleanField(default=False, help_text="Активный водитель для машины")),
                (
                    "driver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vehicle_links",
                        to="vehicles.driver",
                    ),
                ),
                (
                    "vehicle",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="driver_links",
                        to="vehicles.vehicle",
                    ),
                ),
            ],
            options={
                "unique_together": {("driver", "vehicle")},
            },
        ),
    ]

