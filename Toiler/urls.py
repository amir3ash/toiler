"""Toiler URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

import user.views

schema_view = get_schema_view(
    openapi.Info(
        title="Toiler API",
        default_version='v1',
        description="A gantt chart project",
        contact=openapi.Contact(name='Amir Hossein Shams', email="amir3.ash1@gmail.ocm"),
    ),
    public=True,
    permission_classes=[permissions.IsAuthenticated],
)

urlpatterns = [
    path('', user.views.index, name='index'),
    path('admin/', admin.site.urls),
    path('user/', include('user.urls')),
    path('gantt/', include('gantt.urls', namespace='gantt')),

    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=5000), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=5000), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=5000), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += [
        path('debug/', include('debug_toolbar.urls'))
        # IN PRODUCTION WE MUST DELETE PATH 'debug' FROM NGINX CONFIG.
    ]
