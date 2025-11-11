from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Hospital
from .serializers import HospitalSerializer

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
        serializer.save(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
