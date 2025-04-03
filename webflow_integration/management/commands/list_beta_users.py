from django.core.management.base import BaseCommand
from webflow_integration.models import BetaUser

class Command(BaseCommand):
    help = 'Lists all beta users with their details'

    def handle(self, *args, **options):
        users = BetaUser.objects.all()
        if not users:
            self.stdout.write(self.style.WARNING('No beta users found in the database.'))
            return

        self.stdout.write(self.style.SUCCESS(f'\nFound {users.count()} beta users:\n'))
        for user in users:
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Platform: {user.platform}')
            self.stdout.write(f'Subscribed: {user.is_subscribed}')
            self.stdout.write(f'Newsletter Confirmed: {user.newsletter_confirmed}')
            self.stdout.write(f'Created: {user.created_at}')
            self.stdout.write('---') 