import logging

from django.db.models import OuterRef, Exists, Subquery, FloatField, CharField, Prefetch, Count
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status, permissions, filters, mixins
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from core.mixins import GetSerializerClassMixin
from shop.filters import CatalogItemFilter
from shop.models import Brand, CatalogItem, Favorite, ShoppingCart, Image, ItemSKU, Style, Category
from shop.paginations import PageLimitPagination
from shop.serializers import (BrandSerializer, CatalogItemDetailSerializer, CatalogItemListSerializer,
                              FavoriteSerializer, ShoppingCartUpdateSerializer, ShoppingCartCreateSerializer,
                              ShoppingCartSerializer, StyleListSerializer, CategoryListSerializer)

logger = logging.getLogger()


@extend_schema(tags=['Brands'])
class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BrandSerializer
    queryset = Brand.objects.all()
    pagination_class = PageLimitPagination

    @extend_schema(parameters=[OpenApiParameter(name='styles', many=True)])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        styles = self.request.query_params.getlist('styles', None)

        queryset = Brand.objects.all()
        if styles:
            queryset = queryset.filter(items__styles__slug__in=styles)

        queryset = queryset.annotate(
            items_count=Count('items')
        ).filter(items_count__gt=0).order_by('-items_count').distinct()

        return queryset


@extend_schema(tags=['Styles'])
class StyleViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = StyleListSerializer
    queryset = Style.objects.filter(is_show=True)
    lookup_url_kwarg = 'slug'
    lookup_field = 'slug'


@extend_schema(tags=['Categories'])
class CategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CategoryListSerializer
    queryset = Category.objects.filter(is_show=True)
    lookup_url_kwarg = 'slug'
    lookup_field = 'slug'


@extend_schema(tags=['Catalog items'])
class CatalogViewSet(GetSerializerClassMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CatalogItemDetailSerializer
    pagination_class = PageLimitPagination
    queryset = CatalogItem.objects.all()
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ['name', 'spu_id', ]
    filterset_class = CatalogItemFilter
    serializer_class_by_action = {
        'list': CatalogItemListSerializer,
        'retrieve': CatalogItemDetailSerializer,
    }

    @extend_schema(parameters=[
        OpenApiParameter(name='styles', many=True),
        OpenApiParameter(name='brands', many=True),
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        styles = self.request.query_params.getlist('styles')
        brands = self.request.query_params.getlist('brands')
        queryset = super().get_queryset()
        subquery_shopping_carts = ShoppingCart.objects.filter(
            item_sku_id=OuterRef('pk'),
            user_id=self.request.user.id
        )

        queryset = queryset.prefetch_related(Prefetch(
            'skus',
            queryset=ItemSKU.objects.filter(
                price__gt=0, available=True,
            ).annotate(is_in_shopping_cart=Exists(subquery_shopping_carts)),
        ),
            'skus__images', 'skus__properties'
        )
        if styles:
            queryset = queryset.filter(styles__slug__in=styles)
        if brands:
            queryset = queryset.filter(brand__slug__in=brands)

        subquery_price = ItemSKU.objects.filter(item_id=OuterRef('pk')).order_by('-price').values('price')[:1]

        queryset = queryset.annotate(
            price=Subquery(subquery_price, output_field=FloatField()),
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
