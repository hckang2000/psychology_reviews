import os
import json
import gzip
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
import requests

# boto3는 선택적 import (S3 사용시에만 필요)
try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class Command(BaseCommand):
    help = '백업 파일 목록을 확인합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--storage',
            choices=['github', 's3', 'local', 'all'],
            default='github',
            help='확인할 저장소를 선택합니다 (기본값: github)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='표시할 백업 파일 개수 제한 (기본값: 20)'
        )
        parser.add_argument(
            '--details',
            action='store_true',
            help='백업 파일의 상세 정보를 표시합니다'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== 백업 파일 목록 ==='))
        
        storage = options['storage']
        limit = options['limit']
        show_details = options['details']
        
        # GitHub 설정 확인
        if storage in ['github', 'all']:
            github_token = getattr(settings, 'GITHUB_TOKEN', None) or os.getenv('GITHUB_TOKEN')
            github_repo = getattr(settings, 'GITHUB_BACKUP_REPO', None) or os.getenv('GITHUB_BACKUP_REPO')
            
            if not github_token or not github_repo:
                self.stdout.write(
                    self.style.WARNING('GitHub 백업 목록 조회를 위해 GITHUB_TOKEN과 GITHUB_BACKUP_REPO가 필요합니다.')
                )
        
        # S3 사용시 boto3 확인
        if storage in ['s3', 'all'] and not HAS_BOTO3:
            self.stdout.write(
                self.style.WARNING('S3 백업 목록 조회를 위해서는 boto3 패키지가 필요합니다.')
            )
        
        all_backups = []
        
        if storage in ['github', 'all']:
            github_backups = self._get_github_backups()
            all_backups.extend(github_backups)
        
        if storage in ['local', 'all']:
            local_backups = self._get_local_backups()
            all_backups.extend(local_backups)
        
        if storage in ['s3', 'all'] and HAS_BOTO3:
            s3_backups = self._get_s3_backups()
            all_backups.extend(s3_backups)
        
        if not all_backups:
            self.stdout.write(self.style.WARNING('백업 파일이 없습니다.'))
            return
        
        # 날짜순으로 정렬 (최신 순)
        all_backups.sort(key=lambda x: x['modified'], reverse=True)
        
        # 제한된 개수만 표시
        display_backups = all_backups[:limit]
        
        self.stdout.write(f"\n총 {len(all_backups)}개 백업 중 최신 {len(display_backups)}개 표시\n")
        
        for i, backup in enumerate(display_backups, 1):
            self._display_backup_info(i, backup, show_details)
        
        if len(all_backups) > limit:
            self.stdout.write(f"\n... 및 {len(all_backups) - limit}개 추가 백업")

    def _get_github_backups(self):
        """GitHub Releases에서 백업 파일 목록을 가져옵니다"""
        backups = []
        
        try:
            token = getattr(settings, 'GITHUB_TOKEN', None) or os.getenv('GITHUB_TOKEN')
            repo = getattr(settings, 'GITHUB_BACKUP_REPO', None) or os.getenv('GITHUB_BACKUP_REPO')
            
            if not token or not repo:
                return backups
            
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # GitHub Releases API 호출
            url = f'https://api.github.com/repos/{repo}/releases'
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                self.stdout.write(
                    self.style.ERROR(f'GitHub API 호출 실패: {response.status_code}')
                )
                return backups
            
            releases = response.json()
            
            for release in releases:
                if release['tag_name'].startswith('backup-'):
                    # 각 릴리즈의 assets (백업 파일들) 처리
                    for asset in release.get('assets', []):
                        if asset['name'].startswith('backup_'):
                            backup_info = {
                                'filename': asset['name'],
                                'storage': 'github',
                                'size': asset['size'],
                                'modified': datetime.strptime(
                                    asset['updated_at'], 
                                    '%Y-%m-%dT%H:%M:%SZ'
                                ),
                                'path': asset['browser_download_url'],
                                'release_tag': release['tag_name'],
                                'release_name': release['name'],
                                'download_count': asset.get('download_count', 0)
                            }
                            
                            backups.append(backup_info)
                            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'GitHub 백업 목록 조회 실패: {str(e)}')
            )
        
        return backups

    def _get_local_backups(self):
        """로컬 백업 파일 목록을 가져옵니다"""
        backups = []
        
        try:
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            
            if not os.path.exists(backup_dir):
                return backups
            
            for filename in os.listdir(backup_dir):
                if filename.startswith('backup_') and (filename.endswith('.json') or filename.endswith('.gz')):
                    filepath = os.path.join(backup_dir, filename)
                    
                    # 파일 정보 수집
                    stat = os.stat(filepath)
                    
                    backup_info = {
                        'filename': filename,
                        'storage': 'local',
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'path': filepath
                    }
                    
                    # 백업 파일 메타데이터 읽기
                    if filename.endswith('.gz'):
                        try:
                            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                                data = json.load(f)
                                backup_info.update(self._extract_metadata(data))
                        except:
                            pass
                    else:
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                backup_info.update(self._extract_metadata(data))
                        except:
                            pass
                    
                    backups.append(backup_info)
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'로컬 백업 목록 조회 실패: {str(e)}')
            )
        
        return backups

    def _get_s3_backups(self):
        """S3 백업 파일 목록을 가져옵니다"""
        backups = []
        
        if not HAS_BOTO3:
            return backups
        
        try:
            # AWS 설정 확인
            aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            bucket_name = getattr(settings, 'AWS_BACKUP_BUCKET_NAME', None)
            
            if not all([aws_access_key, aws_secret_key, bucket_name]):
                self.stdout.write(
                    self.style.WARNING('AWS 설정이 완료되지 않아 S3 백업을 확인할 수 없습니다.')
                )
                return backups
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'ap-northeast-2')
            )
            
            # S3에서 백업 파일 목록 가져오기
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix='backups/',
                MaxKeys=1000
            )
            
            if 'Contents' not in response:
                return backups
            
            for obj in response['Contents']:
                key = obj['Key']
                filename = os.path.basename(key)
                
                if filename.startswith('backup_') and (filename.endswith('.json') or filename.endswith('.gz')):
                    backup_info = {
                        'filename': filename,
                        'storage': 's3',
                        'size': obj['Size'],
                        'modified': obj['LastModified'].replace(tzinfo=None),
                        'path': f's3://{bucket_name}/{key}',
                        's3_key': key
                    }
                    
                    backups.append(backup_info)
                    
        except ClientError as e:
            self.stdout.write(
                self.style.ERROR(f'S3 백업 목록 조회 실패: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'S3 백업 목록 조회 중 오류: {str(e)}')
            )
        
        return backups

    def _extract_metadata(self, data):
        """백업 파일에서 메타데이터를 추출합니다"""
        metadata = {}
        
        if '_metadata' in data:
            meta = data['_metadata']
            metadata.update({
                'backup_time': meta.get('backup_time'),
                'total_models': meta.get('total_models'),
                'backup_format': meta.get('backup_format'),
                'storage_type': meta.get('storage_type', 'unknown')
            })
        
        # 각 모델의 레코드 수 계산
        total_records = 0
        models_info = []
        
        for key, value in data.items():
            if key != '_metadata' and isinstance(value, dict) and 'count' in value:
                count = value['count']
                total_records += count
                models_info.append(f"{key}({count})")
        
        metadata.update({
            'total_records': total_records,
            'models_info': ', '.join(models_info)
        })
        
        return metadata

    def _display_backup_info(self, index, backup, show_details):
        """백업 정보를 표시합니다"""
        filename = backup['filename']
        storage = backup['storage']
        size = self._format_size(backup['size'])
        modified = backup['modified'].strftime('%Y-%m-%d %H:%M:%S')
        
        # 기본 정보 표시
        self.stdout.write(f"{index:2d}. {filename}")
        self.stdout.write(f"    위치: {storage.upper()} | 크기: {size} | 수정일: {modified}")
        
        # GitHub 추가 정보
        if storage == 'github':
            if 'release_tag' in backup:
                self.stdout.write(f"    릴리즈: {backup['release_name']} ({backup['release_tag']})")
            if 'download_count' in backup:
                self.stdout.write(f"    다운로드: {backup['download_count']}회")
        
        if show_details:
            # 상세 정보 표시
            if 'total_records' in backup:
                self.stdout.write(f"    총 레코드: {backup['total_records']}개")
            
            if 'models_info' in backup:
                self.stdout.write(f"    모델별 데이터: {backup['models_info']}")
            
            if 'backup_time' in backup:
                self.stdout.write(f"    백업 시간: {backup['backup_time']}")
            
            if 'storage_type' in backup:
                self.stdout.write(f"    저장 방식: {backup['storage_type']}")
            
            self.stdout.write(f"    경로: {backup['path']}")
        
        self.stdout.write("")  # 빈 줄

    def _format_size(self, size_bytes):
        """파일 크기를 읽기 쉬운 형태로 변환합니다"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        
        return f"{s} {size_names[i]}" 