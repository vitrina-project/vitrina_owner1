import logging

from django.db.models import OuterRef, Exists, Subquery, FloatField, Prefetch, Count, IntegerField, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status, permissions, filters, mixins
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from core.mixins import GetSerializerClassMixin
from shop.filters import CatalogItemFilter
from shop.models import Brand, CatalogItem, Favorite, ShoppingCart, ItemSKU, Style, Category, LifeStyle, UserLifeStyle, \
    BrandSubscription, UserStyle, Property
from shop.paginations import PageLimitPagination
from shop.serializers import (BrandSerializer, CatalogItemDetailSerializer, CatalogItemListSerializer,
                              FavoriteSerializer, ShoppingCartUpdateSerializer, ShoppingCartCreateSerializer,
                              ShoppingCartSerializer, StyleListSerializer, CategoryListSerializer, LifeStyleSerializer,
                              LifeStyleViewSerializer, BrandSubscriptionCreateSerializer,
                              StyleSubscriptionCreateSerializer, PropertySerializer)

logger = logging.getLogger()


@extend_schema(tags=['Brands'])
class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BrandSerializer
    queryset = Brand.objects.all()
    pagination_class = PageLimitPagination

    @extend_schema(parameters=[OpenApiParameter(name='styles', many=True)])
    @extend_schema(parameters=[OpenApiParameter(name='is_subscribe', type=bool)])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        styles = self.request.query_params.getlist('styles', None)
        is_subscribe = self.request.query_params.get('is_subscribe', None)

        queryset = Brand.objects.all()
        if styles:
            queryset = queryset.filter(items__styles__slug__in=styles)
        subquery_is_subscribe = BrandSubscription.objects.filter(brand_id=OuterRef('pk'), user_id=self.request.user.id)
        queryset = queryset.annotate(is_subscribe=Exists(subquery_is_subscribe))
        if is_subscribe and self.request.user.is_authenticated:
            is_subscribe = is_subscribe.lower() == 'true'
            queryset = queryset.filter(is_subscribe=is_subscribe)

        queryset = queryset.annotate(
            items_count=Count('items')
        ).filter(items_count__gt=0).order_by('-items_count').distinct()

        return queryset

    @action(detail=True, methods=['POST'],
            permission_classes=[permissions.IsAuthenticated],
            serializer_class=None)
    def subscribe(self, request, pk):
        data = {'brand': pk, 'user': request.user.id}
        serializer = BrandSubscriptionCreateSerializer(data=data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk):
        obj = BrandSubscription.objects.filter(user=request.user, brand_id=pk)
        if not obj.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['Styles'])
class StyleViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = StyleListSerializer
    queryset = Style.objects.filter(is_show=True)
    lookup_url_kwarg = 'slug'
    lookup_field = 'slug'
    pagination_class = PageLimitPagination

    @extend_schema(parameters=[OpenApiParameter(name='is_subscribe', type=bool)])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        is_subscribe = self.request.query_params.get('is_subscribe', None)

        queryset = self.queryset
        subquery_is_subscribe = UserStyle.objects.filter(style_id=OuterRef('pk'), user_id=self.request.user.id)
        queryset = queryset.annotate(is_subscribe=Exists(subquery_is_subscribe))
        if is_subscribe and self.request.user.is_authenticated:
            is_subscribe = is_subscribe.lower() == 'true'
            queryset = queryset.filter(is_subscribe=is_subscribe)

        #
        # queryset = queryset.annotate(
        #     items_count=Count('items')
        # ).filter(items_count__gt=0).order_by('-items_count').distinct()

        return queryset

    @action(detail=True, methods=['POST'],
            permission_classes=[permissions.IsAuthenticated],
            serializer_class=None)
    def subscribe(self, request, slug):
        data = {'style': self.get_object().id, 'user': request.user.id}
        serializer = StyleSubscriptionCreateSerializer(data=data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, slug):
        style = self.get_object()
        obj = UserStyle.objects.filter(user=request.user, style_id=style.id)
        if not obj.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['Categories'])
class CategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CategoryListSerializer
    queryset = Category.objects.filter(is_show=True)
    lookup_url_kwarg = 'slug'
    lookup_field = 'slug'
    pagination_class = PageLimitPagination


@extend_schema(tags=['Catalog items'])
class CatalogViewSet(GetSerializerClassMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CatalogItemDetailSerializer
    pagination_class = PageLimitPagination
    queryset = CatalogItem.objects.select_related('shop')
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ['name', ]
    filterset_class = CatalogItemFilter
    serializer_class_by_action = {
        'list': CatalogItemListSerializer,
        'retrieve': CatalogItemDetailSerializer,
    }

    @extend_schema(parameters=[
        OpenApiParameter(name='styles', many=True),
        OpenApiParameter(name='brands', many=True),
        OpenApiParameter(name='categories', many=True),
        OpenApiParameter(name='properties', type=int, many=True),
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        styles = self.request.query_params.getlist('styles')
        brands = self.request.query_params.getlist('brands')
        categories = self.request.query_params.getlist('categories')
        properties: list[str] = self.request.query_params.getlist('properties')
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
        if categories:
            queryset = queryset.filter(categories__slug__in=categories)
        if properties:
            property_ids = []
            for prop in properties:
                if prop.isdigit():
                    property_ids.append(int(prop))
            queryset = queryset.filter(Q(properties__in=property_ids) | Q(skus__properties__in=property_ids)).distinct()

        subquery_price = ItemSKU.objects.filter(item_id=OuterRef('pk')).order_by('-price').values('price')[:1]
        subquery_sku_id = ItemSKU.objects.filter(item_id=OuterRef('pk')).order_by('-price').values('id')[:1]
        subquery_sku_discount = ItemSKU.objects.filter(item_id=OuterRef('pk')).order_by('-price').values('discount')[:1]
        queryset = queryset.annotate(
            price=Subquery(subquery_price, output_field=FloatField()),
            sku_id=Subquery(subquery_sku_id, output_field=IntegerField()),
            sku_discount=Subquery(subquery_sku_discount, output_field=IntegerField()),
        )

        if not self.request.user.is_authenticated:
            return queryset

        subquery_favorites = Favorite.objects.filter(
            user=self.request.user,
            item_id=OuterRef('pk')
        )
        subquery_is_in_shopping_cart = ShoppingCart.objects.filter(
            user=self.request.user,
            item_sku__item_id=OuterRef('pk')
        )

        return queryset.annotate(
            is_favorited=Exists(subquery_favorites),
            is_in_shopping_cart=Exists(subquery_is_in_shopping_cart),
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
        shopping_carts = ShoppingCart.objects.filter(user=request.user)
        return Response(ShoppingCartSerializer(shopping_carts, many=True).data)

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


@extend_schema(tags=['LifeStyle'], description='Образы')
class LifeStyleViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = LifeStyle.objects.all().prefetch_related('categories')
    serializer_class = LifeStyleSerializer
    pagination_class = PageLimitPagination

    @extend_schema(parameters=[
        OpenApiParameter(name='is_like', type=bool),
        OpenApiParameter(name='viewed', type=bool),
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_anonymous:
            return queryset
        is_like = self.request.query_params.get('is_like')
        viewed = self.request.query_params.get('viewed')
        subquery_is_like = UserLifeStyle.objects.filter(
            style_id=OuterRef('pk'), user=self.request.user
        )
        queryset = queryset.annotate(viewed=Exists(subquery_is_like))
        if is_like is not None:
            is_like = is_like.lower() == 'true'
            queryset = queryset.filter(user_lifestyles__user=self.request.user, user_lifestyles__liked=is_like)
        if viewed is not None:
            viewed = viewed.lower() == 'true'
            queryset = queryset.filter(viewed=viewed)

        return queryset

    @action(methods=['POST'], detail=True,
            permission_classes=[permissions.IsAuthenticated],
            serializer_class=LifeStyleViewSerializer)
    def like(self, request, *args, **kwargs):
        lifestyle = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if request.user.user_lifestyles.filter(style=lifestyle).exists():
            request.user.user_lifestyles.filter(style=lifestyle).update(liked=serializer.validated_data['liked'])
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer.save(style=lifestyle, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PropertyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PropertySerializer
    queryset = Property.objects.filter(
        ~Q(type=Property.Types.OTHER), ~Q(type=Property.Types.OPTION)
    ).order_by('key__name')

    def get_queryset(self):
        queryset = super().get_queryset()
        property_type = self.request.query_params.get('type')
        if property_type:
            return queryset.filter(type=property_type)
        return queryset

    @extend_schema(parameters=[
        OpenApiParameter(name='type', type=int),
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
