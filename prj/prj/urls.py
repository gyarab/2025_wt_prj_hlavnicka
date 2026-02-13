"""
URL configuration for prj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django import views
from django.contrib import admin
from django.urls import path

from django.conf.urls import handler404
from app.views import custom_404, test_view, home_view, about_view

handler404 = custom_404


urlpatterns = [
    path('admin/', admin.site.urls),
    path("test-404/", test_view),
    path("about/", about_view),
    path("home/", home_view),
]
