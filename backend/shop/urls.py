from rest_framework import routers

from shop import views

router = routers.DefaultRouter()
router.register('catalog', views.CatalogViewSet)
router.register('brands', views.BrandViewSet)
router.register('styles', views.StyleViewSet)
router.register('categories', views.CategoryViewSet)

urlpatterns = router.urls
