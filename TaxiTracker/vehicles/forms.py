from django import forms
from django.contrib import admin
from .models import Vehicle, Driver


class VehicleAdminForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        enterprise = None

        if self.instance and self.instance.pk:
            enterprise = self.instance.enterprise
        else:
            data = self.data or None
            if data and 'enterprise' in data:
                try:
                    enterprise = int(data.get('enterprise'))
                except (TypeError, ValueError):
                    enterprise = None
            elif 'enterprise' in self.initial:
                enterprise = self.initial['enterprise']

        if enterprise:
            self.fields['driver'].queryset = Driver.objects.filter(
                enterprise_id=enterprise,
                is_active=False
            )
        else:
            self.fields['driver'].queryset = Driver.objects.none()