import logging

from core.mixins import GetSerializerClassMixin
from django.db import transaction
from django.db.models import OuterRef, Exists, Subquery, FloatField, CharField, Prefetch, Count, Max
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status, permissions, mixins, filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from shop.filters import CatalogItemFilter
from shop.models import Brand, CatalogItem, Favorite, ShoppingCart, ItemSKUImage, ItemSKU, Category, Order, \
    Sources, PopularSearch, Feedback, PromoCode, RateInfo
from shop.paginations import PageLimitPagination
from shop.serializers import (BrandSerializer, CatalogItemDetailSerializer, CatalogItemListSerializer,
                              FavoriteSerializer, ShoppingCartUpdateSerializer, ShoppingCartCreateSerializer,
                              ShoppingCartSerializer, CategoryListSerializer, OrderSerializer, TotalCostSerializer,
                              OrderCreateSerializer, PopularSearchSerializer, FeedbackSerializer,
                              FeedbackCreateSerializer, CatalogDetailSerializer)
from shop.services import get_total_cost
from users.models import User

logger = logging.getLogger()


@extend_schema(tags=['Brands'])
class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BrandSerializer
    queryset = Brand.objects.filter(source=Sources.UNICORN, is_show=True)

    @extend_schema(parameters=[OpenApiParameter(name='category', many=True)])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        category = self.request.query_params.getlist('category', None)

        queryset = Brand.objects.filter(
            source=Sources.UNICORN
        )
        if category:
            queryset = queryset.filter(items__category__slug__in=category)

        queryset = queryset.annotate(
            items_count=Count('items')
        ).filter(items_count__gt=1).order_by('-items_count').distinct()[:1000]

        return queryset


class CategoryViewSet(GetSerializerClassMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CategoryListSerializer
    queryset = Category.objects.filter(source=Sources.UNICORN, level=0, is_hide=False).prefetch_related('children')
    lookup_url_kwarg = 'slug'
    lookup_field = 'slug'
    serializer_class_by_action = {
        'retrieve': CatalogDetailSerializer
    }

    def get_object(self):
        return get_object_or_404(Category, slug=self.kwargs['slug'])


@extend_schema(tags=['Catalog items'])
class CatalogViewSet(GetSerializerClassMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CatalogItemDetailSerializer
    pagination_class = PageLimitPagination
    queryset = CatalogItem.items_objects.filter(availability='AVAILABLE')
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ['name', 'spu_id', ]
    filterset_class = CatalogItemFilter
    serializer_class_by_action = {
        'list': CatalogItemListSerializer,
        'retrieve': CatalogItemDetailSerializer,
    }

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['yuan_rate'] = RateInfo.objects.order_by('-created_at').first().yuan_exchange_rate
        return context

    def get_object(self):
        self.queryset = self.queryset.prefetch_related('category__children')
        return super().get_object()

    @extend_schema(parameters=[
        OpenApiParameter(name='category', many=True),
        OpenApiParameter(name='brand', many=True),
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):

        categories = self.request.query_params.getlist('category')
        brand = self.request.query_params.getlist('brand')
        queryset = super().get_queryset()
        subquery_shopping_carts = ShoppingCart.objects.filter(
            item_sku_id=OuterRef('pk'),
            user_id=self.request.user.id
        )

        queryset = queryset.prefetch_related(Prefetch(
            'skus',
            queryset=ItemSKU.objects.filter(
                price__gt=0, cny_price__gt=0
            ).annotate(is_in_shopping_cart=Exists(subquery_shopping_carts)),
        ),
            'skus__images', 'skus__properties'
        )
        if categories:
            queryset = queryset.filter(category__slug__in=categories)
        if brand:
            queryset = queryset.filter(brand__slug__in=brand)

        subquery_cny_price = ItemSKU.objects.filter(
            item_id=OuterRef('pk')
        ).order_by('-cny_price').values('cny_price')[:1]
        subquery_price = ItemSKU.objects.filter(item_id=OuterRef('pk')).order_by('-price').values('price')[:1]
        subquery_image = ItemSKUImage.objects.filter(item_sku__item_id=OuterRef('pk')).values('link')[:1]
        subquery_max_category_price = Category.objects.filter(
            items__id=OuterRef('pk')
        ).annotate(max_price=Max('price')).values('max_price')[:1]
        queryset = queryset.annotate(
            cny_price=Subquery(subquery_cny_price, output_field=FloatField()),
            price=Subquery(subquery_price, output_field=FloatField()),
            image=Subquery(subquery_image, output_field=CharField()),
            max_category_price=Subquery(subquery_max_category_price, output_field=FloatField()),
        )

        if not self.request.user.is_authenticated:
            return queryset

        subquery_favorites = Favorite.objects.filter(
            user=self.request.user,
            item_id=OuterRef('pk')
        )

        return queryset.annotate(
            is_favorited=Exists(subquery_favorites),
        )

    @action(detail=True, methods=['POST'],
            permission_classes=[permissions.IsAuthenticated],
            serializer_class=None)
    def favorite(self, request, pk):
        data = {'item': pk, 'user': request.user.id}
        serializer = FavoriteSerializer(data=data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        obj = Favorite.objects.filter(user=request.user, item_id=pk)
        if not obj.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['POST'],
            permission_classes=[permissions.IsAuthenticated],
            serializer_class=ShoppingCartUpdateSerializer,
            url_path='shopping_cart/(?P<item_sku_id>[^/.]+)')
    def shopping_cart(self, request, item_sku_id):
        data = request.data | {'user': request.user.id, 'item_sku': item_sku_id}
        serializer = ShoppingCartCreateSerializer(data=data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.put
    def update_shopping_cart(self, request, item_sku_id):
        shopping_cart = get_object_or_404(ShoppingCart, user=request.user, item_sku=item_sku_id)
        serializer = self.get_serializer(shopping_cart, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['GET'],
            permission_classes=[permissions.IsAuthenticated],
            serializer_class=ShoppingCartSerializer,
            url_path='shopping_carts')
    def shopping_carts(self, request):
        shopping_carts = ShoppingCart.objects.filter(user=request.user)
        serializer = self.get_serializer(shopping_carts, many=True)
        return Response(serializer.data)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, item_sku_id):
        obj = ShoppingCart.objects.filter(user=request.user, item_sku_id=item_sku_id)
        if not obj.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('GET',), detail=False, serializer_class=PopularSearchSerializer)
    def popular_search(self, request):
        popular_search = PopularSearch.objects.all()
        serializer = self.get_serializer(popular_search, many=True)
        return Response(serializer.data)


@extend_schema(tags=['Orders'])
class OrderViewSet(GetSerializerClassMixin, mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class_by_action = {
        'create': OrderCreateSerializer
    }

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).annotate(
            feedback_exists=Exists(Feedback.objects.filter(order_id=OuterRef('pk'))),
        )

    @action(detail=False, methods=['POST'], serializer_class=TotalCostSerializer)
    def get_total_cost(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        skus: list[dict] = serializer.validated_data['skus']
        promo_code = serializer.validated_data.get('promo_code')

        if promo_code:
            promo_code = PromoCode.objects.filter(code=serializer.validated_data.get('promo_code')).first()
        else:
            promo_code = None
        return Response(get_total_cost(
            request.user,
            skus,
            is_split=serializer.validated_data.get('is_split'),
            bonuses=serializer.validated_data.get('bonuses'),
            promo_code=promo_code,
            delivery_type=serializer.validated_data['delivery_type'],
            address=serializer.validated_data.get('address'),
            pvz=serializer.validated_data.get('pvz') or request.user.pvz_cdek,
            city_id=serializer.validated_data.get('city_id'),
            is_express_delivered=serializer.validated_data.get('is_express_delivered', False),
        ))

    def create(self, request, *args, **kwargs):
        logger.info(f'Новый заказ: {request.data}')
        serializer = self.get_serializer(data=[request.data], many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data[0], status=status.HTTP_201_CREATED)

    @transaction.atomic
    @action(detail=True, methods=['POST'],
            serializer_class=FeedbackCreateSerializer, permission_classes=[])
    def feedback(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs['pk'])
        # if order.user != request.user:
        #     raise ValidationError('Нельзя оставить отзыв на чужой заказ')
        if order.status != order.OrderStatuses.COMPLETED:
            raise ValidationError('Заказ еще не завершен')
        if Feedback.objects.filter(order=order).exists():
            raise ValidationError('Отзыв уже оставлен')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(phone=serializer.validated_data['phone'])
        except User.DoesNotExist:
            return Response()
        if user != order.user:
            return Response()

        serializer.save(order=order)
        UserBonus.objects.create(user=order.user, bonuses=150, type=UserBonus.UserBonusTypes.FEEDBACK)
        return Response(status=status.HTTP_201_CREATED)


@extend_schema(tags=['Feedbacks'])
class FeedbackViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    pagination_class = PageLimitPagination

    def get_queryset(self):
        return super().get_queryset().filter(status=Feedback.FeedbackStatuses.PUBLISHED)
