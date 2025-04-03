from django.urls import path
from . import views

urlpatterns = [
    path('beta/register/', views.register_beta, name='register_beta'),
    path('beta/test-email/', views.test_email, name='test_email'),
    path('beta/confirm/<str:token>/', views.confirm_newsletter, name='confirm_newsletter'),
    path('beta/csrf-token/', views.get_csrf_token, name='get_csrf_token'),
] 