from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from core.mixins import GetSerializerClassMixin
from orders.models import Order
from orders.serializers import OrderSerializer, OrderCreateSerializer


@extend_schema(tags=['Orders'])
class OrderViewSet(GetSerializerClassMixin,
                   mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.DestroyModelMixin,
                   viewsets.GenericViewSet):
    serializer_class = OrderCreateSerializer
    permission_classes = (IsAuthenticated,)
    serializer_class_by_action = {
        'list': OrderSerializer,
        'retrieve': OrderSerializer,
    }

    def get_queryset(self):
        return self.request.user.orders.all().prefetch_related(
            'items', 'items__item_sku', 'items__item_sku__images', 'items__item_sku__properties',
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_destroy(self, instance):
        instance.status = Order.OrderStatuses.CANCEL
