from django.contrib import admin
from .models import Vehicle, Brand

# Register your models here.
admin.site.register(Vehicle)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'id', 'vehicle_count')

    def vehicle_count(self,obj):
        return obj.vehicles.count()
    vehicle_count.short_description = 'Количество машин'