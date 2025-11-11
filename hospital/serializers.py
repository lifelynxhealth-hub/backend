from rest_framework import serializers

from .models import Hospital

class HospitalSerializer(serializers.ModelSerializer):
    google_maps_link = serializers.ReadOnlyField()

    class Meta:
        model = Hospital
        exclude = ['verified', 'approved_by_admin', 'owner', 'date_registered']
        read_only_fields = ['google_maps_link']
