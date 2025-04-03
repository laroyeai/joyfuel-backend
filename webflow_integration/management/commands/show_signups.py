from django.core.management.base import BaseCommand
from webflow_integration.models import BetaUser

class Command(BaseCommand):
    help = 'Shows all beta signups'

    def handle(self, *args, **options):
        users = BetaUser.objects.all()
        if not users:
            self.stdout.write(self.style.WARNING('No signups yet!'))
            return
            
        self.stdout.write(self.style.SUCCESS('Beta Signups:'))
        for user in users:
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Platform: {user.platform}')
            self.stdout.write('---') 