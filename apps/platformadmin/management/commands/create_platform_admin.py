from django.core.management.base import BaseCommand
from platformadmin.models import PlatformAdmin


class Command(BaseCommand):
    help = 'Create the initial platform superadmin account.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='superadmin', help='Admin username')
        parser.add_argument('--password', default='Admin@123', help='Admin password')
        parser.add_argument('--email', default='admin@ovm.local', help='Admin email')
        parser.add_argument('--name', default='Platform Super Admin', help='Full name')

    def handle(self, *args, **options):
        username = options['username']
        if PlatformAdmin.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Admin "{username}" already exists. Skipping.'))
            return

        admin = PlatformAdmin(
            username=username,
            full_name=options['name'],
            email=options['email'],
            role='superadmin',
            status='active',
        )
        admin.set_password(options['password'])
        admin.save()
        self.stdout.write(self.style.SUCCESS(
            f'Superadmin created: username="{username}"  password="{options["password"]}"'
        ))
