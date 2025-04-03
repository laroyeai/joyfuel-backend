from rest_framework import serializers
from .models import BetaUser

class BetaUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BetaUser
        fields = ['email', 'platform']
        
    def validate_email(self, value):
        if BetaUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered for beta testing.")
        return value 