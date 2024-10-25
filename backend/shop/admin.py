from django.contrib import admin

from core.admin import LinkInlineForm
from shop.models import Style, CatalogItem, ItemSKU, Brand, Property, Category, PropertyKey, Image


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('image',)

    def has_module_permission(self, request):
        return False


# ItemSize)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_filter = ('type',)
    list_display = ('id', 'key', 'type', 'value')


@admin.register(PropertyKey)
class PropertyAdmin(admin.ModelAdmin):
    list_filter = ('name',)

    def has_module_permission(self, request):
        return False


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    readonly_fields = ('slug',)


class ItemSKUImageInline(admin.StackedInline):
    model = ItemSKU.images.through
    extra = 0

class ItemImageInline(admin.StackedInline):
    model = CatalogItem.images.through
    extra = 0


class PropertyInline(admin.TabularInline):
    extra = 0
    model = Property
    # fields = ('pk', 'item',)
    # readonly_fields = ('pk', 'sku_id',)


@admin.register(ItemSKU)
class ItemSKUAdmin(admin.ModelAdmin):
    inlines = [ItemSKUImageInline]
    # list_filter = ('item',)
    raw_id_fields = ('item',)
    search_fields = ('sku_id', 'id')
    list_display = ('id', 'item', 'discount')
    exclude = ('images',)
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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'count_items')
    list_filter = ('is_show',)
    search_fields = ('name', 'slug',)
    readonly_fields = ('slug',)

    def count_items(self, obj):
        return obj.items.count()


class ItemSKUInline(admin.TabularInline):
    extra = 0
    model = ItemSKU
    show_change_link = True
    fields = ('pk',)
    readonly_fields = ('pk',)
    form = LinkInlineForm


@admin.register(CatalogItem)
class CatalogItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'score', 'created_at')
    list_filter = ('styles',)
    exclude = ('images',)
    inlines = [ItemSKUInline, ItemImageInline]
    list_per_page = 100
    search_fields = ('name', 'slug', 'skus__sku_id', 'id')
    readonly_fields = ('slug',)
