import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = '환경변수를 사용하여 superuser를 생성합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username for superuser (optional, uses DJANGO_SUPERUSER_USERNAME env var if not provided)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for superuser (optional, uses DJANGO_SUPERUSER_EMAIL env var if not provided)',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for superuser (optional, uses DJANGO_SUPERUSER_PASSWORD env var if not provided)',
        )

    def handle(self, *args, **options):
        username = options['username'] or os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = options['email'] or os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = options['password'] or os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123!')

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser "{username}"가 이미 존재합니다.')
            )
            return

        try:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{username}"가 성공적으로 생성되었습니다!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Superuser 생성 중 오류 발생: {e}')
            ) 