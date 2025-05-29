import os
import subprocess
import gzip
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json


class Command(BaseCommand):
    help = 'PostgreSQL pg_dump를 이용해 전체 데이터베이스를 백업합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--upload-to',
            choices=['github', 'dropbox', 'local'],
            default='local',
            help='백업 파일을 업로드할 위치'
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            default=True,
            help='백업 파일을 압축합니다'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== PostgreSQL 데이터베이스 백업 시작 ==='))
        
        # 데이터베이스 URL 파싱
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            self.stdout.write(
                self.style.ERROR('DATABASE_URL 환경변수가 설정되지 않았습니다.')
            )
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'pgdump_{timestamp}.sql'
        
        # pg_dump 실행
        success = self._create_pg_dump(db_url, filename, options['compress'])
        
        if not success:
            return
        
        # 업로드 처리
        if options['upload_to'] != 'local':
            self._upload_backup(filename, options['upload_to'])
        
        self.stdout.write(
            self.style.SUCCESS(f'=== PostgreSQL 백업 완료: {filename} ===')
        )

    def _create_pg_dump(self, db_url, filename, compress):
        """pg_dump를 사용하여 백업을 생성합니다"""
        try:
            # 백업 디렉토리 생성
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            filepath = os.path.join(backup_dir, filename)
            
            # pg_dump 명령어 구성
            if compress:
                filepath += '.gz'
                # 압축과 함께 덤프
                cmd = f'pg_dump "{db_url}" | gzip > "{filepath}"'
            else:
                # 일반 덤프
                cmd = f'pg_dump "{db_url}" > "{filepath}"'
            
            self.stdout.write(f'백업 명령어 실행 중: pg_dump')
            
            # Windows에서는 shell=True 필요
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 파일 크기 확인
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    size_mb = size / (1024 * 1024)
                    self.stdout.write(f'백업 파일 생성 완료: {size_mb:.2f} MB')
                    return True
                else:
                    self.stdout.write(self.style.ERROR('백업 파일이 생성되지 않았습니다.'))
                    return False
            else:
                self.stdout.write(
                    self.style.ERROR(f'pg_dump 실행 실패: {result.stderr}')
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'백업 생성 중 오류: {str(e)}')
            )
            return False

    def _upload_backup(self, filename, upload_to):
        """백업 파일을 업로드합니다"""
        try:
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            filepath = os.path.join(backup_dir, filename + '.gz')
            
            if not os.path.exists(filepath):
                self.stdout.write(self.style.ERROR(f'백업 파일을 찾을 수 없습니다: {filepath}'))
                return
            
            with open(filepath, 'rb') as f:
                data = f.read()
            
            if upload_to == 'github':
                self._upload_to_github(filename + '.gz', data)
            elif upload_to == 'dropbox':
                self._upload_to_dropbox(filename + '.gz', data)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'업로드 중 오류: {str(e)}')
            )

    def _upload_to_github(self, filename, data):
        """GitHub에 업로드"""
        token = os.getenv('GITHUB_TOKEN')
        repo = os.getenv('GITHUB_BACKUP_REPO')
        
        if not token or not repo:
            self.stdout.write(
                self.style.WARNING('GitHub 업로드를 위해 GITHUB_TOKEN과 GITHUB_BACKUP_REPO가 필요합니다.')
            )
            return
        
        # GitHub Release API 호출 (간단 버전)
        self.stdout.write('GitHub 업로드 구현 필요')

    def _upload_to_dropbox(self, filename, data):
        """Dropbox에 업로드"""
        token = os.getenv('DROPBOX_TOKEN')
        
        if not token:
            self.stdout.write(
                self.style.WARNING('Dropbox 업로드를 위해 DROPBOX_TOKEN이 필요합니다.')
            )
            return
        
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/octet-stream',
                'Dropbox-API-Arg': json.dumps({
                    'path': f'/database_backups/{filename}',
                    'mode': 'overwrite'
                })
            }
            
            response = requests.post(
                'https://content.dropboxapi.com/2/files/upload',
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                self.stdout.write('Dropbox 업로드 완료')
            else:
                self.stdout.write(f'Dropbox 업로드 실패: {response.status_code}')
                
        except Exception as e:
            self.stdout.write(f'Dropbox 업로드 오류: {str(e)}') 