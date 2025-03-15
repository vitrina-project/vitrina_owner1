from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from users.models import ConfirmCode, User

admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('email', 'last_name', 'first_name', 'date_joined')
    # readonly_fields = ('email',)
    search_fields = ('email',)

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", 'role', 'shop', "password1", "password2"),
            },
        ),
    )

    fieldsets = (
        (_("Personal info"),
         {'fields': (
             'first_name', 'last_name', 'role', 'shop',
             'email', 'notify_email', 'password'
         )
         }),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_superuser",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return False


@admin.register(ConfirmCode)
class ConfirmCodeAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'type', 'created_at')

    def has_module_permission(self, request):
        return False
