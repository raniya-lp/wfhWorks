"""roadmap URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view
from rest_framework.authentication import BasicAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static
schema_view = get_schema_view(
    title="Roadmap",
    description="APIs for Roadmap",
    version="2.0.0",
    authentication_classes=[BasicAuthentication, JWTAuthentication])


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),    
    path('api/v1/user/', include('users.urls'), name="User"),
    path('api/v1/organization/', include('organizations.urls'), name="Organization"),
    path('api/v1/projects/', include('projects.urls'), name="Projects"),
    path('api/v1/pattern-library/', include('patterns.urls'), name="Projects"),
    path('api/v1/context/', include('context.urls'), name="Projects"),
    path('api/v1/service-blueprint/', include('blueprint.urls'), name="blueprint"),
    path('api/v1/momentumReport/', include('momentum_report.urls'), name="momentumReport"),
    path('api/v1/apiservices/',include('ApiServices.urls'),name='apiservices'),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
