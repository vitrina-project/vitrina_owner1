from django.contrib import admin

from core.permissions import StafferPermissionMixin
from shop.models import Style, CatalogItem, ItemSKU, Brand, Property, Category, PropertyKey, Image, LifeStyle, Shop


@admin.register(Shop)
class ShopAdmin(StafferPermissionMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'address')

    def has_add_permission(self, request):
        return request.user.is_superuser

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(user=request.user)


@admin.register(Image)
class ImageAdmin(StafferPermissionMixin, admin.ModelAdmin):
    list_display = ('image',)

    def has_module_permission(self, request):
        return False


@admin.register(LifeStyle)
class LifeStyleAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_filter = ('type', 'key')
    list_display = ('id', 'key', 'type', 'value')

    def has_view_permission(self, request, obj=None):
        return True

@admin.register(PropertyKey)
class PropertyAdmin(admin.ModelAdmin):
    list_filter = ('name',)

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        return False


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    readonly_fields = ('slug',)

    def has_view_permission(self, request, obj=None):
        return True

class ItemSKUImageInline(StafferPermissionMixin, admin.StackedInline):
    model = ItemSKU.images.through
    extra = 0


class ItemImageInline(StafferPermissionMixin, admin.StackedInline):
    model = CatalogItem.images.through
    extra = 0

    def has_add_permission(self, *args, **kwargs):
        return True


class PropertyInline(admin.TabularInline):
    extra = 0
    model = Property
    # fields = ('pk', 'item',)
    # readonly_fields = ('pk', 'sku_id',)


@admin.register(ItemSKU)
class ItemSKUAdmin(StafferPermissionMixin, admin.ModelAdmin):
    inlines = [ItemSKUImageInline]
    # list_filter = ('item',)
    raw_id_fields = ('item',)
    search_fields = ('sku_id', 'id')
    list_display = ('id', 'item', 'discount')
    exclude = ('images',)

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(item__shop__user=request.user)

    def has_delete_permission(self, request, obj=None):
        return True

    # readonly_fields = ('properties', 'item')

    # def get_queryset(self, request):
    #     queryset = super().get_queryset(request)
    #     return queryset.select_related('item').prefetch_related('properties')

    # def has_module_permission(self, request):
    #     return False


@admin.register(Style)
class StyleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'count_items')
    list_filter = ('is_show',)
    search_fields = ('name', 'slug',)
    readonly_fields = ('slug',)

    def count_items(self, obj):
        return obj.items.count()

    def has_view_permission(self, request, obj=None):
        return True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'count_items')
    list_filter = ('is_show',)
    search_fields = ('name', 'slug',)
    readonly_fields = ('slug',)

    def has_view_permission(self, request, obj=None):
        return True

    def count_items(self, obj):
        return obj.items.count()


class ItemSKUInline(StafferPermissionMixin, admin.StackedInline):
    extra = 0
    model = ItemSKU
    show_change_link = True
    # fields = ('pk',)
    readonly_fields = ('pk',)
    raw_id_fields = ('properties',)

    # form = LinkInlineForm
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('properties')


@admin.register(CatalogItem)
class CatalogItemAdmin(StafferPermissionMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'score', 'created_at')
    list_filter = ('styles', 'categories')
    exclude = ('images',)
    inlines = [ItemSKUInline, ItemImageInline]
    list_per_page = 100
    search_fields = ('name', 'slug', 'skus__sku_id', 'id')
    readonly_fields = ('slug',)
    list_select_related = ('properties', 'skus__properties')
    raw_id_fields = ('properties',)

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if request.user.is_superuser:
            list_display += ('shop',)
        return list_display

    def has_delete_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(
            shop__user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "shop" and not request.user.is_superuser:
            kwargs["queryset"] = Shop.objects.filter(user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
