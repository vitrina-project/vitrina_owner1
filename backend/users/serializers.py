from rest_framework import serializers

from users.models import User, ConfirmCode


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'full_name',
                  'notify_email', 'gender', 'city')
        read_only_fields = ('email', 'full_name')


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ConfirmCodeSerializer(serializers.Serializer):
    code = serializers.CharField()
    email = serializers.EmailField()

    def validate(self, validate_data):
        if not ConfirmCode.objects.filter(
                email=validate_data['email'],
                code=validate_data['code']
        ).exists():
            raise serializers.ValidationError('Неверный код')

        return validate_data
