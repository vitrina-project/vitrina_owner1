from django.contrib import admin

from core.permissions import StafferPermissionMixin
from .models import Order, OrderItem


class OrderItemInline(StafferPermissionMixin, admin.StackedInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('item_sku',)

    def has_delete_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(item_sku__item__shop=request.user.shop)

@admin.register(Order)
class OrderAdmin(StafferPermissionMixin, admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    inlines = [OrderItemInline]
    exclude = ('shop', 'status')
    readonly_fields = ('user',)

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(items__item_sku__item__shop=request.user.shop).distinct()
