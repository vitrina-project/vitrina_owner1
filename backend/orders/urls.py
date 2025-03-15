from rest_framework import routers

from orders import views

router = routers.DefaultRouter()
router.register('orders', views.OrderViewSet, basename='orders')

urlpatterns = router.urls
