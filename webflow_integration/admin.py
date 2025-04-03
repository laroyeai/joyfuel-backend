from django.contrib import admin
from .models import BetaUser

@admin.register(BetaUser)
class BetaUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'platform', 'is_subscribed', 'newsletter_confirmed', 'created_at')
    list_filter = ('platform', 'is_subscribed', 'newsletter_confirmed')
    search_fields = ('email',)
    readonly_fields = ('created_at',) 