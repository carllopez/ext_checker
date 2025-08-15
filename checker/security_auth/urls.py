from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_and_challenge_view, name='login_and_challenge'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),
]