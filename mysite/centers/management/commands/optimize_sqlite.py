from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'SQLite 데이터베이스 최적화 및 WAL 모드 설정'

    def handle(self, *args, **options):
        if 'sqlite' not in settings.DATABASES['default']['ENGINE']:
            self.stdout.write(
                self.style.WARNING('SQLite 데이터베이스가 아니므로 최적화를 건너뜁니다.')
            )
            return

        self.stdout.write('SQLite 데이터베이스 최적화 시작...')

        with connection.cursor() as cursor:
            # WAL 모드 설정
            cursor.execute("PRAGMA journal_mode=WAL;")
            result = cursor.fetchone()
            self.stdout.write(f'Journal 모드: {result[0]}')

            # 동기화 모드 설정
            cursor.execute("PRAGMA synchronous=NORMAL;")
            
            # 캐시 크기 설정
            cursor.execute("PRAGMA cache_size=1000;")
            
            # 임시 저장소를 메모리로 설정
            cursor.execute("PRAGMA temp_store=MEMORY;")
            
            # 대기 타임아웃 설정 (30초)
            cursor.execute("PRAGMA busy_timeout=30000;")
            
            # 데이터베이스 최적화
            cursor.execute("VACUUM;")
            
            # 통계 업데이트
            cursor.execute("ANALYZE;")

        self.stdout.write(
            self.style.SUCCESS('SQLite 데이터베이스 최적화가 완료되었습니다!')
        ) 