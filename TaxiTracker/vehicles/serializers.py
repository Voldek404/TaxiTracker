from rest_framework import serializers
from vehicles.models import Vehicle

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields =('prod_date','odometer','price','color','plate_number', 'brand')

