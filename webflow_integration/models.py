from django.db import models

class BetaUser(models.Model):
    PLATFORM_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
    ]
    
    email = models.EmailField(unique=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_subscribed = models.BooleanField(default=True)
    newsletter_confirmed = models.BooleanField(default=False)
    confirmation_token = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    def __str__(self):
        return f"{self.email} - {self.platform}"
        
    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['platform']),
            models.Index(fields=['confirmation_token']),
        ] 