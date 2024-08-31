from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    def _create_user(self, phone, password, **extra_fields):
        if not phone:
            raise ValueError("The given phone must be set")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone=None, password='None', **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone=None, password='samsa123', **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", 'ADMIN')

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(phone, password, **extra_fields)


class User(AbstractUser):
    class UserRoles(models.TextChoices):
        ADMIN = 'ADMIN', 'Администратор'
        SERVICE = 'SERVICE', 'Сервис'
        USER = 'USER', 'Пользователь'
        MODERATOR = 'MODERATOR', 'Модератор'

    class Genders(models.IntegerChoices):
        MALE = 1
        FEMALE = 2

    username = models.CharField(max_length=120, blank=True, null=True)
    email = models.EmailField('Email', db_index=True, unique=True)
    gender = models.IntegerField('Пол', choices=Genders.choices)
    city = models.CharField(max_length=120, blank=True)

    notify_email = models.BooleanField('Уведомлять по email да/нет', default=False)
    confirm_email = models.BooleanField('Почта подтверждена да/нет', default=False)
    role = models.CharField('Роль', max_length=20, choices=UserRoles.choices, default=UserRoles.USER, db_index=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'middle_name', 'password']

    objects = UserManager()

    def __str__(self):
        return str(self.email)

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name}'

    class Meta:
        verbose_name = 'Пользователи'
        verbose_name_plural = 'Пользователи'


class ConfirmCode(models.Model):
    class ConfirmCodeTypes(models.TextChoices):
        REGISTER = 'REGISTER', 'регистрация'
        AUTH = 'AUTH', 'авторизация'
        CONFIRM_PHONE = 'CONFIRM_PHONE', 'подтверждение почты'

    email = models.CharField('Email', max_length=120)
    code = models.CharField('код', max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(choices=ConfirmCodeTypes.choices, max_length=30)

    class Meta:
        verbose_name = 'Код для действия с аккаунтом'
        verbose_name_plural = 'Коды для действий с аккаунтами'

    def __str__(self):
        return f'{self.email} код {self.code}'
