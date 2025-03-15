import logging

from rest_framework import serializers

from shop.models import (Brand, CatalogItem, Style, ItemSKU, Image, Property, ShoppingCart,
                         Favorite, LifeStyle, UserLifeStyle, BrandSubscription, UserStyle, Shop)

logger = logging.getLogger()


class BrandSerializer(serializers.ModelSerializer):
    items_count = serializers.IntegerField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_subscribe = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Brand
        fields = ('id', 'name', 'slug', 'items_count', 'description', 'is_subscribe')
        read_only_fields = fields


class StyleListSerializer(serializers.ModelSerializer):
    description = serializers.CharField(read_only=True)

    class Meta:
        model = Style
        fields = ('id', 'name', 'slug', 'image', 'description')
        read_only_fields = fields


class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Style
        fields = ('id', 'name', 'slug',)
        read_only_fields = fields


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('image',)
        read_only_fields = fields


class PropertySerializer(serializers.ModelSerializer):
    key = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Property
        fields = ('id', 'type', 'value', 'key')


class ItemSKUSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    is_in_shopping_cart = serializers.BooleanField(default=False)
    properties = PropertySerializer(many=True, read_only=True)
    price = serializers.FloatField()

    class Meta:
        model = ItemSKU
        fields = ('id', 'price',
                  'discount', 'images', 'is_in_shopping_cart', 'properties')
        read_only_fields = fields


class CatalogItemListSerializer(serializers.ModelSerializer):
    price = serializers.FloatField(default=0, read_only=True)
    is_favorited = serializers.BooleanField(default=False, read_only=True)
    category = serializers.SlugRelatedField(slug_field='slug', read_only=True, many=True)
    brand = serializers.StringRelatedField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True, default=False)
    sku_id = serializers.IntegerField(read_only=True, default=None, allow_null=True)
    store_address = serializers.CharField(read_only=True, source='shop.address')
    sku_discount = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = CatalogItem
        fields = ('id', 'name', 'slug', 'category', 'gender', 'article', 'brand', 'sku_discount',
                  'price', 'is_favorited', 'score', 'store_address', 'main_image', 'is_in_shopping_cart', 'sku_id')
        read_only_fields = fields


class CatalogItemDetailSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField(many=True, read_only=True)
    skus = ItemSKUSerializer(many=True, read_only=True)
    is_favorited = serializers.BooleanField(default=False)
    brand = BrandSerializer(read_only=True)
    images = ImageSerializer(many=True, read_only=True)
    properties = PropertySerializer(many=True, read_only=True)
    styles = StyleListSerializer(many=True, read_only=True)

    class Meta:
        model = CatalogItem
        fields = ('id', 'name', 'slug', 'category', 'gender', 'description', 'article', 'brand',
                  'skus', 'is_favorited', 'images', 'properties', 'styles')
        read_only_fields = fields

    # def get_properties(self, obj):
    #     skus = []
    #     for sku in obj.skus.all():
    #         skus.append({
    #             'item_sku': sku.id,
    #             'properties': PropertySerializer(sku.properties.all(), many=True).data
    #         })
    #     return {'skus': skus}


class ShoppingCartItemSkuSerializer(ItemSKUSerializer):
    brand = BrandSerializer(read_only=True, source='item.brand')
    article = serializers.CharField(source='item.article', read_only=True)
    store_address = serializers.CharField(source='item.shop.address', read_only=True)

    class Meta:
        model = ItemSKU
        fields = ('id', 'price', 'discount', 'images', 'properties', 'brand', 'article', 'store_address')


class ShoppingCartSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='item_sku.item.name')
    properties = PropertySerializer(many=True, read_only=True, source='item_sku.item.properties')
    item_sku = ShoppingCartItemSkuSerializer(read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('id', 'item_sku', 'count', 'name', 'properties')
        read_only_fields = fields


class ShoppingCartUpdateSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(min_value=1, max_value=10)

    class Meta:
        model = ShoppingCart
        fields = ('count',)

    def to_representation(self, instance):
        return ShoppingCartSerializer(instance).data


class ShoppingCartCreateSerializer(ShoppingCartUpdateSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('count', 'item_sku', 'user')

    def validate(self, data):
        if ShoppingCart.objects.filter(
                user=self.context['request'].user, item_sku=data['item_sku']
        ).exists():
            raise serializers.ValidationError('Товар уже добавлен в корзину')
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'item')

    # def to_representation(self, instance):
    #     return CatalogItemDetailSerializer(instance.item, context=self.context).data

    def validate(self, data):
        if Favorite.objects.filter(
                user=data['user'], item=data['item']).exists():
            raise serializers.ValidationError('Товар уже добавлен в избранное')
        return data


class LifeStyleSerializer(serializers.ModelSerializer):
    categories = CategoryListSerializer(many=True, read_only=True)
    viewed = serializers.BooleanField(default=False)

    class Meta:
        model = LifeStyle
        fields = ('id', 'image', 'description', 'categories', 'viewed')
        read_only_fields = fields


class LifeStyleViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLifeStyle
        fields = ('user', 'style', 'liked')
        read_only_fields = ('user', 'style')


class BrandSubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandSubscription
        fields = ('user', 'brand')


class StyleSubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStyle
        fields = ('user', 'style')


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('name', 'address')
