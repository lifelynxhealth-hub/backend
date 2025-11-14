from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()

router.register(r'chat-sessions', ChatSessionViewSet, basename='chatsession')

urlpatterns = [
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('', include(router.urls)),
]
