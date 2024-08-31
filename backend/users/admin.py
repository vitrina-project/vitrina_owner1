from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from users.models import ConfirmCode, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('email', 'last_name', 'first_name', 'date_joined')
    readonly_fields = (
        'email',)
    search_fields = ('email',)
    fieldsets = (
        (_("Personal info"),
         {'fields': (
             'first_name', 'last_name', 'role',
             'email', 'notify_email', 'confirm_email',
         )
         }),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )


@admin.register(ConfirmCode)
class ConfirmCodeAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'type', 'created_at')

    def has_module_permission(self, request):
        return False
