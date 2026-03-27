from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

openapi_info = openapi.Info(
    title="Hope Backend API",
    default_version='v1',
    description="Hope Backend REST API",
    contact=openapi.Contact(email="afsalkallingal77@gmail.com"),
    license=openapi.License(name="BSD License"),
)

schema_view = get_schema_view(
    openapi_info,
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Define urlpatterns
urlpatterns = [
    path("api/v1/", include("apps.user_account.api_v1.api_router", namespace="user_account_api_router_v1")),
    path("api/v1/", include("apps.stories.api_v1.api_router", namespace="stories_api_v1")),
    

    path(settings.ADMIN_URL, admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API URLs for Swagger and Redoc
urlpatterns += [
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Debug mode URLs
if settings.DEBUG:
    urlpatterns += [
        path("400/", default_views.bad_request, kwargs={"exception": Exception("Bad Request!")}),
        path("403/", default_views.permission_denied, kwargs={"exception": Exception("Permission Denied")}),
        path("404/", default_views.page_not_found, kwargs={"exception": Exception("Page not Found")}),
        path("500/", default_views.server_error),
    ]

    # Include Debug Toolbar URLs
    if "debug_toolbar" in settings.INSTALLED_APPS:
        urlpatterns += [
            path('__debug__/', include('debug_toolbar.urls')),
        ]
