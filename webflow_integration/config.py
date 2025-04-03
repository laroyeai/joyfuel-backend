from django.conf import settings

# Beta testing links
BETA_LINKS = {
    'ios': getattr(settings, 'IOS_TESTFLIGHT_LINK', 'https://testflight.apple.com/join/YOUR_TESTFLIGHT_CODE'),
    'android': getattr(settings, 'ANDROID_BETA_LINK', 'https://play.google.com/apps/testing/YOUR_APP_PACKAGE_NAME')
} 