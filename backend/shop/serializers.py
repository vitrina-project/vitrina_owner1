import logging
from datetime import timezone, datetime
from math import ceil

from django.db import transaction
from django.db.models import Max
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from delivery.models import Pvz
from shop.models import Brand, CatalogItem, Category, ItemSKU, ItemSKUImage, ItemSize, ItemProperty, ShoppingCart, \
    Favorite, Order, PromoCode, PopularSearch, RateInfo, Feedback, FeedbackImage, Carousel
from shop.services import get_total_cost

logger = logging.getLogger()


class BrandSerializer(serializers.ModelSerializer):
    items_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Brand
        fields = ('id', 'name', 'slug', 'items_count')
        read_only_fields = fields


class SubCategoryListSerializer(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(slug_field='slug', read_only=True)

    class Meta:
        model = Category
        fields = ('title', 'slug', 'parent')
        read_only_fields = fields


class SubCategoryDetailSerializer(SubCategoryListSerializer):
    children = serializers.SerializerMethodField()

    class Meta(SubCategoryListSerializer.Meta):
        fields = SubCategoryListSerializer.Meta.fields + ('children',)

    def get_children(self, obj):
        return SubCategoryDetailSerializer(obj.children, many=True).data


class CategoryListSerializer(serializers.ModelSerializer):
    children = SubCategoryListSerializer(read_only=True, many=True)

    class Meta:
        model = Category
        fields = ('id', 'title', 'slug', 'parent', 'children')
        read_only_fields = fields


class CatalogDetailSerializer(CategoryListSerializer):
    children = SubCategoryDetailSerializer(read_only=True, many=True)
    # pass


class ItemSKUImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemSKUImage
        fields = ('link',)
        read_only_fields = fields


class ItemSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemSize
        fields = ('id', 'type', 'values')


class ItemPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemProperty
        fields = ('id', 'type', 'value',)


class ItemSKUSerializer(serializers.ModelSerializer):
    images = ItemSKUImageSerializer(many=True, read_only=True)
    is_in_shopping_cart = serializers.BooleanField(default=False)
    properties = ItemPropertySerializer(many=True, read_only=True)
    name = serializers.CharField(read_only=True, source='item.name')
    price = serializers.SerializerMethodField()

    class Meta:
        model = ItemSKU
        fields = ('id', 'sku_id', 'cny_price', 'price', 'size', 'name',
                  'discount', 'images', 'is_in_shopping_cart', 'properties')
        read_only_fields = fields

    def get_price(self, obj):
        yuan_rate = self.context.get('yuan_rate')
        if not yuan_rate:
            yuan_rate = RateInfo.objects.order_by('-created_at').first().yuan_exchange_rate
        if not hasattr(obj.item, 'max_category_price'):
            category_price = obj.item.category.aggregate(max_price=Max('price'))['max_price']
        else:
            category_price = obj.item.max_category_price or 220
        return ceil(((float(obj.cny_price) * float(yuan_rate) * 1.08) + float(category_price) + 220) * 1.04)


class CatalogItemListSerializer(serializers.ModelSerializer):
    image = serializers.CharField(read_only=True)
    price = serializers.SerializerMethodField(default=0, read_only=True)
    is_favorited = serializers.BooleanField(default=False, read_only=True)
    category = serializers.SlugRelatedField(slug_field='slug', read_only=True, many=True)
    brand = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CatalogItem
        fields = ('id', 'name', 'slug', 'spu_id', 'category', 'fit', 'article', 'availability', 'brand',
                  'image', 'price', 'is_favorited', 'parse_date', 'score')
        read_only_fields = fields

    def get_price(self, obj):
        yuan_rate = self.context['yuan_rate']
        category_price = obj.max_category_price or 220
        return ceil(((float(obj.cny_price) * float(yuan_rate) * 1.08) + float(category_price) + 220) * 1.04)


class CatalogItemDetailSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField(many=True, read_only=True)
    skus = ItemSKUSerializer(many=True, read_only=True)
    sizes = ItemSizeSerializer(many=True, read_only=True)
    properties = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField(default=False)

    class Meta:
        model = CatalogItem
        fields = ('id', 'name', 'slug', 'spu_id', 'category', 'fit', 'description', 'article', 'availability', 'brand',
                  'from_availability', 'skus', 'sizes', 'properties', 'is_favorited', 'parse_date')
        read_only_fields = fields

    def get_properties(self, obj):
        skus = []
        for sku in obj.skus.all():
            skus.append({
                'item_sku': sku.id,
                'properties': ItemPropertySerializer(sku.properties.all(), many=True).data
            })
        return {'skus': skus}


class ShoppingCartSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='item_sku.item.name')
    properties = ItemPropertySerializer(many=True, read_only=True, source='item_sku.item.properties')
    item_sku = ItemSKUSerializer(read_only=True)

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


class OrderSerializer(serializers.ModelSerializer):
    item_sku = ItemSKUSerializer(read_only=True)
    feedback_exists = serializers.BooleanField(default=False)

    class Meta:
        model = Order
        fields = ('id', 'total_cost', 'status', 'is_split', 'item_sku', 'count', 'address', 'city',
                  'track_number', 'cost_delivered', 'is_express_delivered', 'delivery_type', 'delivery_cost_after',
                  'user_full_name', 'user_phone', 'user_email', 'cdek_address', 'created_at', 'updated_at', 'bonuses',
                  'feedback_exists', 'total_cost_without_promo_code_and_bonuses', 'promo_code_discount')
        read_only_fields = fields


class ItemSkuOrderSerializer(serializers.Serializer):
    item_sku = serializers.PrimaryKeyRelatedField(queryset=ItemSKU.objects.all())
    count = serializers.IntegerField(min_value=1, max_value=100)


class TotalCostSerializer(serializers.Serializer):
    skus = ItemSkuOrderSerializer(many=True)
    delivery_type = serializers.ChoiceField(choices=Order.DeliveredTypes.choices)
    promo_code = serializers.CharField(required=False, allow_null=True)
    bonuses = serializers.IntegerField(required=False)
    is_split = serializers.BooleanField(default=False)
    address = serializers.CharField(required=False)
    pvz = serializers.PrimaryKeyRelatedField(queryset=Pvz.objects.all(), required=False, allow_null=True)
    is_express_delivered = serializers.BooleanField(default=False)
    city_id = serializers.IntegerField(required=False)
    delivery_cost_after = serializers.BooleanField(default=False)

    def validate(self, attrs):
        user = self.context['request'].user
        if attrs['delivery_type'] == Order.DeliveredTypes.CDEK and not (attrs.get('pvz') or user.pvz_cdek):
            raise serializers.ValidationError('Не указан пункт выдачи')
        if attrs['delivery_type'] == Order.DeliveredTypes.COURIER and not (
                (attrs.get('address') or user.delivery_address) and attrs.get('city_id')):
            raise serializers.ValidationError('Не указан адрес доставки')
        return attrs

    def validate_bonuses(self, bonuses):
        if bonuses is not None and self.context['request'].user.bonus_rubles < bonuses:
            raise serializers.ValidationError('У вас нет столько бонусов')
        return bonuses

    def validate_promo_code(self, promo_code):
        if promo_code is not None and not PromoCode.objects.filter(
                code=promo_code, expired__gte=datetime.now(timezone.utc)).exists():
            raise serializers.ValidationError('Промокод не существует или недействителен')
        return promo_code


class OrderCreateSerializer(TotalCostSerializer):
    user_full_name = serializers.CharField(required=False)
    user_phone = serializers.CharField(required=False)
    user_email = serializers.CharField(required=False)
    city = serializers.CharField(required=False)

    # class Meta:
    #     model = Order
    #     fields = ('delivery_type', 'promo_code', 'skus', 'address', 'city', 'city_id',
    #               'address', 'is_express_delivered', 'bonuses', 'user_full_name', 'user_phone', 'user_email', 'pvz')

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        skus = validated_data.pop('skus')
        bonuses = validated_data.get('bonuses')
        promo_code = PromoCode.objects.filter(code=validated_data.get('promo_code')).first()
        is_split = validated_data.get('is_split', False)
        pvz = validated_data.get('pvz') or user.pvz_cdek
        delivery_type = validated_data.get('delivery_type')
        address = validated_data.get('address')
        city_id = validated_data.get('city_id')
        orders = []
        total_cost = get_total_cost(
            user,
            skus,
            is_split=is_split,
            bonuses=bonuses,
            promo_code=promo_code,
            delivery_type=delivery_type,
            address=address,
            pvz=pvz,
            city_id=city_id,
            is_express_delivered=validated_data.get('is_express_delivered', False),
        )
        if is_split and total_cost['total_cost'] > 50000:
            raise serializers.ValidationError('Невозможно провести split если сумма заказа более 50000')
        if pvz:
            cdek_address = pvz.full_address
        elif user.pvz_cdek:
            cdek_address = user.pvz_cdek.full_address
        else:
            cdek_address = ''

        for sku in total_cost['items']:
            if total_cost['total_cost'] == 0 and total_cost['total_cost_without_promo_code_and_bonuses'] > 0:
                status = Order.OrderStatuses.PAID
            else:
                status = Order.OrderStatuses.AWAITING_PAYMENT
            orders.append(Order(
                user=user,
                user_email=validated_data.get('user_email') if validated_data.get('user_email') else user.email,
                user_phone=validated_data.get('user_phone') if validated_data.get('user_phone') else user.phone,
                city=validated_data.get('city') if validated_data.get('city') else user.city,
                user_full_name=validated_data.get('user_full_name') if validated_data.get(
                    'user_full_name') else user.full_name,
                item_sku_id=sku['item_sku'],
                total_cost=total_cost['total_cost'],
                is_split=is_split,
                count=sku['count'],
                status=status,
                address=validated_data.get('address') if validated_data.get('address') else user.delivery_address,
                cdek_address=cdek_address,
                delivery_type=validated_data['delivery_type'],
                is_express_delivered=validated_data.get('is_express_delivered', False),
                cost_delivered=sku['delivered_price'],
                delivery_cost_after=total_cost['delivery_cost_after'],
                statuses_history=[status],
                bonuses=total_cost['bonuses'],
                total_cost_without_promo_code_and_bonuses=total_cost['total_cost_without_promo_code_and_bonuses'],
                promo_code_discount=total_cost['promo_code_discount']

            ))
        Order.objects.bulk_create(orders)
        user.bonus_rubles -= bonuses
        user.save()
        return orders

    def to_representation(self, orders):
        user = self.context['request'].user
        return OrderSerializer(user.orders.all(), many=True).data


class PopularSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopularSearch
        fields = ('text',)


class ItemFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogItem
        fields = ('name',)


class FeedbackImageSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = FeedbackImage
        fields = ('image',)


class FeedbackSerializer(serializers.ModelSerializer):
    images = FeedbackImageSerializer(many=True, read_only=True)
    item = ItemFeedbackSerializer(read_only=True, source='order.item_sku.item')

    class Meta:
        model = Feedback
        fields = ('id', 'text', 'images', 'created_at', 'updated_at', 'item')
        read_only_fields = fields


class FeedbackCreateSerializer(serializers.ModelSerializer):
    # images = FeedbackImageSerializer(many=True, required=False)
    phone = serializers.IntegerField()

    class Meta:
        model = Feedback
        fields = ('text', 'phone')

    def create(self, validated_data):
        # images = validated_data.pop('images', [])
        phone = validated_data.pop('phone', None)
        feedback = Feedback.objects.create(**validated_data)
        create_images = []
        # for image in images:
        #     create_images.append(FeedbackImage(**image, feedback=feedback))
        # FeedbackImage.objects.bulk_create(create_images)
        return feedback


class CarouselItemSerializer(serializers.ModelSerializer):
    image = serializers.CharField(allow_null=True, allow_blank=True)

    class Meta:
        model = CatalogItem
        fields = ('id', 'image')
        read_only_fields = fields


class CarouselSerializer(serializers.ModelSerializer):
    items = CarouselItemSerializer(many=True, read_only=True)
    category = serializers.SlugRelatedField(slug_field='slug', many=True, read_only=True)

    class Meta:
        model = Carousel
        fields = ('category', 'name', 'description', 'items')
        read_only_fields = fields
