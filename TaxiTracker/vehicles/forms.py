from django import forms
from django.contrib import admin
from .models import Vehicle, Driver


class VehicleAdminForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        enterprise = None

        if self.instance and self.instance.pk:
            enterprise = self.instance.enterprise
        else:
            data = self.data or None
            if data and "enterprise" in data:
                try:
                    enterprise = int(data.get("enterprise"))
                except (TypeError, ValueError):
                    enterprise = None
            elif "enterprise" in self.initial:
                enterprise = self.initial["enterprise"]

        if "driver" in self.fields:
            if enterprise:
                self.fields["driver"].queryset = Driver.objects.filter(
                    enterprise_id=enterprise, is_active=False
                )
            else:
                self.fields["driver"].queryset = Driver.objects.none()


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "prod_date",
            "enterprise",
            "odometer",
            "price",
            "color",
            "plate_number",
            "brand",
            "driver",
        ]
        widgets = {
            "prod_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "odometer": forms.NumberInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "color": forms.TextInput(attrs={"class": "form-control"}),
            "plate_number": forms.TextInput(attrs={"class": "form-control"}),
            "brand": forms.TextInput(attrs={"class": "form-control"}),
            "enterprise": forms.Select(attrs={"class": "form-control"}),
            "driver": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Делаем driver необязательным
        self.fields["driver"].required = False

        if user and hasattr(user, "managers"):
            manager = user.managers
            # Ограничиваем выбор только предприятиями менеджера
            self.fields['enterprise'].queryset = manager.enterprises.all()

            # Делаем поле обязательным
            self.fields['enterprise'].required = True
            manager = user.managers
            self.fields["driver"].queryset = Driver.objects.filter(
                enterprise__in=manager.enterprises.all()
            ).select_related("enterprise")

            self.fields["driver"].label_from_instance = (
                lambda obj: f"{obj.full_name} ({obj.enterprise.name})"
            )
