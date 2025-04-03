from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import LoginSerializer
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserRegistrationSerializer
from .models import User
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from .tasks import process_file
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data
        refresh = RefreshToken.for_user(user)
        res = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        return Response(res, status=status.HTTP_200_OK)


class UserRegistrationAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@method_decorator(csrf_exempt, name='dispatch')
class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        data = request.data
        email = data.get("email")
        username = data.get("username")
        s3_file_path = data.get("s3_file_path")
        if email is None:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'error': 'Missing required parameter: "email".'}
            )
        if username is None:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'error': 'Missing required parameter: "username".'}
            )
        if s3_file_path is None:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'error': 'Missing required parameter: "s3_file_path".'}
            )
        file_exists = default_storage.exists(s3_file_path)
        if not file_exists:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={'error': f"'{s3_file_path}' not found in S3 bucket"}
            )
        process_file.delay(email, username, s3_file_path)
        return Response(
            status=status.HTTP_202_ACCEPTED,
            data={'message': 'File is being processed', 'file_url': s3_file_path}
        )
