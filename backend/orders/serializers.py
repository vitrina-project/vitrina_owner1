from datetime import timedelta

from django.db import transaction
from rest_framework import serializers

from orders.models import Order, OrderItem
from shop.models import ShoppingCart
from shop.serializers import ItemSKUSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    item_sku = ItemSKUSerializer(read_only=True)
    name = serializers.CharField(source='item_sku.item.name', read_only=True)
    address = serializers.CharField(source='item_sku.item.shop.address', read_only=True)
    booking_and_date = serializers.SerializerMethodField()
    brand = serializers.CharField(source='item_sku.item.brand', read_only=True)

    class Meta:
        model = OrderItem
        fields = ('item_sku', 'count', 'total_cost', 'name', 'address', 'booking_and_date' ,'brand')
        read_only_fields = fields

    def get_booking_and_date(self, obj):
        return obj.created_at + timedelta(days=obj.item_sku.item.shop.booking_days)


class OrderItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('item_sku', 'count',)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'status', 'items', 'created_at')
        read_only_fields = fields


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ('items',)

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        item_sku_ids = []
        for item in items:
            item_sku_ids.append(item['item_sku'].id)
            OrderItem.objects.create(order=order, **item, total_cost=item['item_sku'].price)
        user = self.context['request'].user
        user.shopping_carts.filter(item_sku__in=item_sku_ids).delete()

        return order

    def to_representation(self, instance):
        return OrderSerializer(instance).data
