from rest_framework import routers

from shop import views

router = routers.DefaultRouter()
router.register('catalog', views.CatalogViewSet, basename='catalog')
router.register('brands', views.BrandViewSet, basename='brands')
router.register('styles', views.StyleViewSet, basename='styles')
router.register('lifestyles', views.LifeStyleViewSet, basename='lifestyles')
router.register('categories', views.CategoryViewSet, basename='categories')
router.register('properties', views.PropertyViewSet, basename='properties')

urlpatterns = router.urls
