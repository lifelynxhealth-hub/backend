from django.shortcuts import render
from rest_framework import generics, permissions
from .models import Notification
from .serializers import NotificationSerializer
from .pagination import StandardResultsSetPagination

# Create your views here.

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(recipient=user)
        
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            if is_read.lower() in ['true', '1']:
                queryset = queryset.filter(is_read=True)
            elif is_read.lower() in ['false', '0']:
                queryset = queryset.filter(is_read=False)
        
        return queryset
