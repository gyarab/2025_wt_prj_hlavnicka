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
from app.views import custom_404, test_view, home_view, about_view, detail_prvku, detail_stitku, pridat_prvek, upravit_prvek, smazat_prvek, detail_seznamu, stitek_api, registrace_view, api_playground_view
from django.contrib.auth import views as auth_views 
from django.contrib.sitemaps.views import sitemap
from app.sitemaps import PrvekSitemap, SeznamSitemap, StitekSitemap, StaticViewSitemap

from app.api import api

sitemaps = {
    'static': StaticViewSitemap,
    'prvky': PrvekSitemap,
    'seznamy': SeznamSitemap,
    'stitky': StitekSitemap,
}

handler404 = custom_404


urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path("test-404/", test_view),
    path("about/", about_view, name='about'),
    path("home/", home_view, name='home'),
    path('prihlasit/', auth_views.LoginView.as_view(), name='login'),
    path('odhlasit/', auth_views.LogoutView.as_view(), name='logout'),
    path('registrace/', registrace_view, name='registrace'),

    # Změna a reset hesla
    path('zmena-hesla/', auth_views.PasswordChangeView.as_view(template_name='registration/zmena_hesla.html'), name='password_change'),
    path('zmena-hesla/hotovo/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/zmena_hesla_hotovo.html'), name='password_change_done'),
    path('reset-hesla/', auth_views.PasswordResetView.as_view(template_name='registration/reset_hesla.html'), name='password_reset'),
    path('reset-hesla/hotovo/', auth_views.PasswordResetDoneView.as_view(template_name='registration/reset_hesla_hotovo.html'), name='password_reset_done'),
    path('reset-hesla/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/reset_hesla_potvrzeni.html'), name='password_reset_confirm'),
    path('reset-hesla/dokonceno/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/reset_hesla_dokonceno.html'), name='password_reset_complete'),

    path('pridat/', pridat_prvek, name='pridat_prvek'),
    path('prvek/<int:id>/', detail_prvku, name='detail_prvku'),
    path('prvek/<int:id>/upravit/', upravit_prvek, name='upravit_prvek'),
    path('prvek/<int:id>/smazat/', smazat_prvek, name='smazat_prvek'),
    path('', home_view, name='home'),
    path("stitek/<int:id>/", detail_stitku, name="detail_stitku"),
    path("seznam/<int:id>/", detail_seznamu, name="detail_seznamu"),
    path("api/stitek/<int:id>/", stitek_api, name="stitek_prvky_api"),

    path("api/", api.urls),
    path("api_playground/", api_playground_view, name="api_playground"),
]
