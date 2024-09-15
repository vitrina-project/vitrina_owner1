import logging

from django_filters.rest_framework import filters, FilterSet
from rest_framework.filters import SearchFilter

from .models import CatalogItem, Category, Brand, SizeTypes

logger = logging.getLogger()


class BrandSearchFilter(SearchFilter):
    search_param = 'name'


class CatalogItemFilter(FilterSet):
    is_favorited = filters.BooleanFilter(method='get_favorited_filter')
    # is_in_shopping_cart = filters.BooleanFilter(
    #     method='get_shopping_cart_filter')
    # brand = filters.ModelMultipleChoiceFilter(
    #     field_name='brand__slug',
    #     queryset=Brand.objects.filter(source=Sources.UNICORN, is_show=True),
    #     to_field_name='slug',
    # )
    size_type = filters.ChoiceFilter(choices=SizeTypes.choices + [('apparel', 'apparel')],
                                     method='get_size_type_filter', )
    size_value = filters.CharFilter(method='get_size_value_filter')
    from_price = filters.NumberFilter(method='get_from_price_filter')
    to_price = filters.NumberFilter(method='get_to_price_filter')
    # name = filters.CharFilter(lookup_expr='icontains')
    ordering = filters.OrderingFilter(
        fields=(('price', 'score', 'created_at')),
        field_labels={
            'price': 'price',
        }
    )

    class Meta:
        model = CatalogItem
        fields = ('is_favorited', 'fit', 'size_type', 'size_value', 'from_price', 'to_price')

    def get_category_filter(self, queryset, name, value):
        logger.info(name, value)
        return queryset

    def get_favorited_filter(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_size_type_filter(self, queryset, name, value):
        if value and value != 'apparel':
            return queryset.filter(sizes__type=value)
        return queryset

    def get_size_value_filter(self, queryset, name, value):
        if value:
            size_type = self.request.query_params.get('size_type', 'eu')
            if size_type == 'apparel':
                return queryset.filter(skus__properties__value=value.upper(), skus__properties__type=6).distinct()
            value = int(value) if value.isdigit() else float(value)
            _filter = {
                f'skus__size__{size_type.lower()}': f'{value}'
            }

            return queryset.filter(**_filter)
            # return queryset.filter(sizes__values__contains=[value])
        return queryset

    def get_from_price_filter(self, queryset, name, value):
        if value:
            return queryset.filter(price__gte=int(value))
        return queryset

    def get_to_price_filter(self, queryset, name, value):
        if value:
            return queryset.filter(price__lte=int(value))
        return queryset


class BrandFilter(FilterSet):
    category = filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.all(),
        to_field_name='slug',
        field_name='items__category__slug',
    )

    class Meta:
        model = Brand
        fields = ('category',)
