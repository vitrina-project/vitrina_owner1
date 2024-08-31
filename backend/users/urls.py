from django.urls import include, path
from rest_framework import routers

from users.views import UserViewSet, TokenViewSet

users_router = routers.DefaultRouter(trailing_slash=False)
users_router.register('token', TokenViewSet, 'token')
users_router.register('users', UserViewSet, 'users')

urlpatterns = [
    path('', include(users_router.urls)),
]
