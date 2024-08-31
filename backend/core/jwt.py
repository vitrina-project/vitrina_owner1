# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework_simplejwt.exceptions import InvalidToken, TokenError, AuthenticationFailed
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from rest_framework_simplejwt.views import TokenViewBase
#
#
# class InActiveUser(AuthenticationFailed):
#     status_code = status.HTTP_406_NOT_ACCEPTABLE
#     default_detail = ("User is not active, please confirm your email")
#     default_code = 'user_is_inactive'
#
#
import enum

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as BaseTokenObtainPairSerializer


class TokenTypes(enum.Enum):
    INDIVIDUAL = 0
    BUSINESS = 0


class TokenObtainPairSerializer(BaseTokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user, company_id: int = None):
        token = super().get_token(user)
        token['type'] = TokenTypes.BUSINESS.value if company_id is not None else TokenTypes.INDIVIDUAL.value
        token['company_id'] = company_id
        return token

    # def validate(self, attrs):
    #     data = super().validate(attrs)
    #     if not self.user.active:
    #         raise InActiveUser()
    #
    #     refresh = self.get_token(self.user)
    #
    #     data['refresh'] = str(refresh)
    #     data['access'] = str(refresh.access_token)
    #
    #     if api_settings.UPDATE_LAST_LOGIN:
    #         update_last_login(None, self.user)
    #
    #     return data
#
# class TokenObtainPairView(TokenViewBase):
#     """
#     Takes a set of user credentials and returns an access and refresh JSON web
#     token pair to prove the authentication of those credentials.
#     """
#     serializer_class = TokenObtainPairSerializer
#
#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#         except AuthenticationFailed as e:
#             raise InvalidUser(e.args[0])
#         except TokenError as e:
#             raise InvalidToken(e.args[0])
#
#         return Response(serializer.validated_data, status=status.HTTP_200_OK)
#
#
# class InvalidUser(AuthenticationFailed):
#     status_code = status.HTTP_406_NOT_ACCEPTABLE
#     default_detail = 'Неверные учетные данные'
#     default_code = 'user_credentials_not_valid'
