from django.urls import path
from .views import UserRegistrationAPIView, LoginAPIView, FileUploadView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('signup/', UserRegistrationAPIView.as_view(), name='signup'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('upload/', FileUploadView.as_view(), name='file_upload'),
]