import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.jwt import TokenObtainPairSerializer
from users.models import ConfirmCode, User
from users.serializers import (ConfirmCodeSerializer, UserSerializer,
                               LoginSerializer)

logger = logging.getLogger()


@extend_schema(tags=['Users'])
class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    @action(methods=['GET'],
            detail=False,
            permission_classes=(IsAuthenticated,),
            serializer_class=UserSerializer)
    def me(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.request.user)
        return Response(serializer.data)

    @me.mapping.patch
    def update_me(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.request.user,
                                         data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


@extend_schema(tags=['Tokens'])
class TokenViewSet(GenericViewSet):
    @action(detail=False, methods=['post'], serializer_class=LoginSerializer)
    def login(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        exists_recovery_code = ConfirmCode.objects.filter(email=email, type=ConfirmCode.ConfirmCodeTypes.AUTH)
        if exists_recovery_code.exists():
            exists_recovery_code.delete()

        # code = send_sms_to_phone(phone)
        code = 1234

        ConfirmCode.objects.create(
            email=email,
            code=int(code),
            type=ConfirmCode.ConfirmCodeTypes.AUTH
        )
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'],
            serializer_class=ConfirmCodeSerializer, url_path='create')
    def create_token(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        recovery_code = ConfirmCode.objects.get(email=email, type=ConfirmCode.ConfirmCodeTypes.AUTH)

        exists_user = False
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(email=email, password='vitr123', is_active=True)
        else:
            exists_user = True
            user = User.objects.get(email=email)
        recovery_code.delete()
        token = TokenObtainPairSerializer.get_token(user)
        return Response(
            {'access_token': str(token.access_token),
             'exists_user': exists_user},
            status=status.HTTP_200_OK
        )
