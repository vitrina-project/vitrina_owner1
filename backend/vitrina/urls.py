from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.versioning import URLPathVersioning

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(versioning_class=URLPathVersioning), name='docs'),

    path('api/v1/', include('users.urls')),
    path('api/v1/', include('shop.urls')),
    path('api/v1/', include('orders.urls')),
]
if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path('api/__debug__/', include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
