import os
import time
import threading
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import logging
import schedule

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '데이터 백업을 자동으로 스케줄링합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            choices=['hourly', 'daily', 'weekly'],
            default='daily',
            help='백업 주기를 설정합니다 (기본값: daily)'
        )
        parser.add_argument(
            '--time',
            default='02:00',
            help='백업 실행 시간을 설정합니다 (형식: HH:MM, 기본값: 02:00)'
        )
        parser.add_argument(
            '--storage',
            choices=['github', 's3', 'google_drive', 'local'],
            default='github',
            help='백업 저장 위치를 선택합니다 (기본값: github)'
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='백그라운드에서 계속 실행합니다'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='한 번만 백업하고 종료합니다'
        )
        parser.add_argument(
            '--retention-days',
            type=int,
            default=30,
            help='백업 파일 보관 기간 (일 단위, 기본값: 30일)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== 백업 스케줄러 시작 ==='))
        
        # GitHub 사용시 설정 확인
        if options['storage'] == 'github':
            token = getattr(settings, 'GITHUB_TOKEN', None) or os.getenv('GITHUB_TOKEN')
            repo = getattr(settings, 'GITHUB_BACKUP_REPO', None) or os.getenv('GITHUB_BACKUP_REPO')
            
            if not token or not repo:
                self.stdout.write(
                    self.style.ERROR('GitHub 백업을 위해서는 GITHUB_TOKEN과 GITHUB_BACKUP_REPO가 필요합니다.')
                )
                self.stdout.write('환경변수 설정: GITHUB_TOKEN=your_token, GITHUB_BACKUP_REPO=username/repo-name')
                return
        
        interval = options['interval']
        backup_time = options['time']
        storage = options['storage']
        daemon_mode = options['daemon']
        once_only = options['once']
        retention_days = options['retention_days']
        
        self.stdout.write(f"백업 주기: {interval}")
        self.stdout.write(f"백업 시간: {backup_time}")
        self.stdout.write(f"저장 위치: {storage}")
        self.stdout.write(f"보관 기간: {retention_days}일")
        
        if once_only:
            # 한 번만 백업하고 종료
            self.stdout.write("즉시 백업을 실행합니다...")
            self._run_backup(storage)
            return
        
        # 스케줄 설정
        schedule.clear()
        
        if interval == 'hourly':
            schedule.every().hour.do(lambda: self._run_backup(storage))
            # 정리 작업은 매일 한 번만
            schedule.every().day.at("03:00").do(lambda: self._cleanup_old_releases(retention_days))
        elif interval == 'daily':
            schedule.every().day.at(backup_time).do(lambda: self._run_backup(storage))
            # 정리 작업은 백업 후 1시간 뒤
            cleanup_hour = str(int(backup_time.split(':')[0]) + 1).zfill(2)
            cleanup_time = f"{cleanup_hour}:00"
            schedule.every().day.at(cleanup_time).do(lambda: self._cleanup_old_releases(retention_days))
        elif interval == 'weekly':
            # 매주 일요일에 실행
            schedule.every().sunday.at(backup_time).do(lambda: self._run_backup(storage))
            # 정리 작업은 백업 후 1시간 뒤
            cleanup_hour = str(int(backup_time.split(':')[0]) + 1).zfill(2)
            cleanup_time = f"{cleanup_hour}:00"
            schedule.every().sunday.at(cleanup_time).do(lambda: self._cleanup_old_releases(retention_days))
        
        self.stdout.write(f"다음 백업 예정: {schedule.next_run()}")
        
        if daemon_mode:
            self.stdout.write("백그라운드에서 실행됩니다. Ctrl+C로 중지하세요.")
        
        try:
            while True:
                schedule.run_pending()
                
                if not daemon_mode:
                    # 데몬 모드가 아니면 다음 실행까지 대기 후 종료
                    next_run = schedule.next_run()
                    if next_run:
                        self.stdout.write(f"다음 백업까지 대기 중... ({next_run})")
                    else:
                        break
                
                time.sleep(60)  # 1분마다 체크
                
        except KeyboardInterrupt:
            self.stdout.write("\n백업 스케줄러가 중지되었습니다.")

    def _run_backup(self, storage):
        """백업을 실행합니다"""
        try:
            self.stdout.write(f"\n[{datetime.now()}] 백업 시작 - 저장소: {storage}")
            
            if storage == 'github':
                # GitHub 설정 가져오기
                repo = getattr(settings, 'GITHUB_BACKUP_REPO', None) or os.getenv('GITHUB_BACKUP_REPO')
                if repo:
                    call_command('backup_data', storage='github', verbosity=1)
                else:
                    call_command('backup_to_github', repo=repo, verbosity=1)
            else:
                call_command('backup_data', storage=storage, verbosity=1)
            
            self.stdout.write(f"[{datetime.now()}] 백업 완료")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"[{datetime.now()}] 백업 실패: {str(e)}")
            )

    def _cleanup_old_releases(self, retention_days):
        """오래된 GitHub 릴리즈를 정리합니다"""
        try:
            self.stdout.write(f"\n[{datetime.now()}] 오래된 백업 정리 시작 ({retention_days}일 이상)")
            
            token = getattr(settings, 'GITHUB_TOKEN', None) or os.getenv('GITHUB_TOKEN')
            repo = getattr(settings, 'GITHUB_BACKUP_REPO', None) or os.getenv('GITHUB_BACKUP_REPO')
            
            if not token or not repo:
                self.stdout.write("GitHub 설정이 없어 정리를 건너뜁니다.")
                return
            
            import requests
            from datetime import datetime, timedelta
            
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # GitHub Releases 목록 가져오기
            url = f'https://api.github.com/repos/{repo}/releases'
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                self.stdout.write(f"GitHub API 호출 실패: {response.status_code}")
                return
            
            releases = response.json()
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            deleted_count = 0
            
            for release in releases:
                if release['tag_name'].startswith('backup-'):
                    # 릴리즈 생성 날짜 확인
                    created_at = datetime.strptime(
                        release['created_at'], 
                        '%Y-%m-%dT%H:%M:%SZ'
                    )
                    
                    if created_at < cutoff_date:
                        # 오래된 릴리즈 삭제
                        delete_url = f"https://api.github.com/repos/{repo}/releases/{release['id']}"
                        delete_response = requests.delete(delete_url, headers=headers)
                        
                        if delete_response.status_code == 204:
                            self.stdout.write(f"삭제: {release['name']} ({release['tag_name']})")
                            deleted_count += 1
                        else:
                            self.stdout.write(f"삭제 실패: {release['name']} - {delete_response.status_code}")
            
            if deleted_count > 0:
                self.stdout.write(f"[{datetime.now()}] {deleted_count}개 오래된 백업 삭제 완료")
            else:
                self.stdout.write(f"[{datetime.now()}] 삭제할 오래된 백업이 없습니다")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"[{datetime.now()}] 백업 정리 실패: {str(e)}")
            ) 