from django.contrib import admin
from .models import Vehicle, Brand, Driver, Enterprise, VehicleDriver
from .forms import VehicleAdminForm

# Register your models here.



class VehicleDriverInline(admin.TabularInline):
    model = VehicleDriver
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "driver":
            if request._obj_ is not None:
                kwargs["queryset"] = Driver.objects.filter(enterprise=request._obj_.enterprise)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
    inlines = [VehicleDriverInline]
    form = VehicleAdminForm
    list_filter = (BrandNoneFilter,)
    list_display = ('id', 'plate_number', 'brand', 'enterprise', 'driver', 'get_drivers_status')

    def get_drivers_status(self, obj):
        drivers_info = []

        if obj.driver:
            status = "✅ активен" if obj.driver.is_active else "❌ неактивен"
            drivers_info.append(f"{obj.driver.full_name} (основной, {status})")

        other_drivers = obj.vehicle_drivers.exclude(driver=obj.driver) if obj.driver else obj.vehicle_drivers.all()
        for vd in other_drivers:
            status = "✅ активен" if vd.is_active else "❌ неактивен"
            drivers_info.append(f"{vd.driver.full_name} ({status})")

        return ", ".join(drivers_info) if drivers_info else "Нет водителей"

    get_drivers_status.short_description = 'Статус водителей'

    def get_form(self, request, obj=None, **kwargs):
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)



@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'enterprise', 'is_active')

@admin.register(Enterprise)
class EnterpriseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'city')


