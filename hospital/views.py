from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Hospital
from .serializers import HospitalSerializer
from core.utils import geocode_address

# Create your views here.

class HospitalProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = HospitalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        if not user.is_hospital:
            raise PermissionDenied("Only hospital accounts can access this resource.")

        hospital, created = Hospital.objects.get_or_create(owner=user)
        return hospital

    def perform_update(self, serializer):
        instance = serializer.instance
        address = serializer.validated_data.get('address', instance.address)
        city = serializer.validated_data.get('city', instance.city)
        state = serializer.validated_data.get('state', instance.state)
        
        if (address != instance.address or city != instance.city or state != instance.state) and address and city and state:
            lat, lng = geocode_address(address, city, state)
            if (lat, lng):
                serializer.save(owner=self.request.user,
                                latitude=lat,
                                longitude=lng)
            else:
                serializer.save(owner=self.request.user)
        else:
            serializer.save(owner=self.request.user)

    def perform_create(self, serializer):
        address = serializer.validated_data.get('address')
        city = serializer.validated_data.get('city')
        state = serializer.validated_data.get('state')
        latitude = longitude = None

        if address and city and state:
            lat, lng = geocode_address(address, city, state)
            if (lat, lng):
                latitude = lat
                longitude =lng

        serializer.save(owner=self.request.user, latitude=latitude, longitude=longitude)
