import logging

from django_filters.rest_framework import filters, FilterSet
from rest_framework.filters import SearchFilter

from .models import CatalogItem, Style, Brand

logger = logging.getLogger()


class BrandSearchFilter(SearchFilter):
    search_param = 'name'


# class CatalogOrderingFilter(filters.OrderingFilter):

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.extra['choices'] += [
    #         ('sku_discount', 'Discount'),
    #         ('-sku_discount', 'Discount (descending)'),
    #     ]

    # def filter(self, qs, value):
    #     if any(v == 'discount' for v in value):
    #         qs = qs.order_by('skus__discount')
    #
    #     if any(v == '-discount' for v in value):
    #         qs = qs.order_by('-skus__discount')
    #
    #     return super().filter(qs, value)


class CatalogItemFilter(FilterSet):
    is_favorited = filters.BooleanFilter(method='get_favorited_filter')
    from_price = filters.NumberFilter(method='get_from_price_filter')
    to_price = filters.NumberFilter(method='get_to_price_filter')
    ordering = filters.OrderingFilter(
        fields=('price', 'score', 'created_at', 'sku_discount'),
        field_labels={
            'price': 'price',
        }
    )

    class Meta:
        model = CatalogItem
        fields = ('is_favorited', 'gender', 'from_price', 'to_price')

    def get_favorited_filter(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
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
    styles = filters.ModelMultipleChoiceFilter(
        queryset=Style.objects.all(),
        to_field_name='slug',
        field_name='items__styles__slug',
    )

    class Meta:
        model = Brand
        fields = ('styles',)
