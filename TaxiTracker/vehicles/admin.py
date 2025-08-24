from django.contrib import admin
from .models import Vehicle, Brand, Driver, Enterprise
from .forms import VehicleAdminForm

# Register your models here.



class BrandNoneFilter(admin.SimpleListFilter):
    title = 'бренд'
    parameter_name = 'brand_null'

    def lookups(self, request, model_admin):
        return (
            ('NONE', 'Без бренда'),
            ('not_NONE', 'С брендом'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'NONE':
            return queryset.filter(brand__isnull=True)
        if self.value() == 'not_NONE':
            return queryset.filter(brand__isnull=False)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id','product_name', 'vehicle_count')

    def vehicle_count(self,obj):
        return obj.vehicles.count()
    vehicle_count.short_description = 'Количество машин'

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    form = VehicleAdminForm
    list_filter = (BrandNoneFilter,)
    list_display = ('id', 'plate_number', 'brand', 'enterprise', 'driver')


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'enterprise', 'is_active')

@admin.register(Enterprise)
class EnterpriseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'city')


