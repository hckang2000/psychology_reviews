import os
import json
import gzip
from django.core.management.base import BaseCommand
from django.core import serializers
from django.db import transaction
from django.apps import apps
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
    help = '백업된 데이터를 복원합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            help='복원할 백업 파일의 경로 또는 이름'
        )
        parser.add_argument(
            '--storage',
            choices=['github', 's3', 'local'],
            default='github',
            help='백업 파일이 저장된 위치 (기본값: github)'
        )
        parser.add_argument(
            '--models',
            nargs='+',
            help='복원할 모델들을 지정합니다 (미지정시 모든 모델 복원)'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='복원 전에 기존 데이터를 삭제합니다 (주의: 데이터 손실 위험)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 복원하지 않고 복원 과정만 시뮬레이션합니다'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== 데이터 복원 시작 ==='))
        
        # GitHub 사용시 설정 확인
        if options['storage'] == 'github':
            token = getattr(settings, 'GITHUB_TOKEN', None) or os.getenv('GITHUB_TOKEN')
            repo = getattr(settings, 'GITHUB_BACKUP_REPO', None) or os.getenv('GITHUB_BACKUP_REPO')
            
            if not token or not repo:
                self.stdout.write(
                    self.style.ERROR('GitHub 복원을 위해서는 GITHUB_TOKEN과 GITHUB_BACKUP_REPO가 필요합니다.')
                )
                return
        
        # S3 사용시 boto3 확인
        if options['storage'] == 's3' and not HAS_BOTO3:
            self.stdout.write(
                self.style.ERROR('S3 복원을 위해서는 boto3 패키지가 필요합니다. pip install boto3')
            )
            return
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN 모드: 실제 데이터는 변경되지 않습니다.'))
        
        # 백업 파일 읽기
        backup_data = self._load_backup_file(options['backup_file'], options['storage'])
        
        if not backup_data:
            self.stdout.write(self.style.ERROR('백업 파일을 읽을 수 없습니다.'))
            return
        
        # 메타데이터 확인
        metadata = backup_data.get('_metadata', {})
        self.stdout.write(f"백업 생성 시간: {metadata.get('backup_time', '알 수 없음')}")
        self.stdout.write(f"백업 형식: {metadata.get('backup_format', '알 수 없음')}")
        self.stdout.write(f"총 모델 수: {metadata.get('total_models', '알 수 없음')}")
        self.stdout.write(f"저장 방식: {metadata.get('storage_type', '알 수 없음')}")
        
        # 복원할 모델들 결정
        models_to_restore = options.get('models') or [
            key for key in backup_data.keys() if key != '_metadata'
        ]
        
        self.stdout.write(f"복원할 모델들: {', '.join(models_to_restore)}")
        
        if not options['dry_run']:
            # 사용자 확인 (dry-run이 아닌 경우)
            confirm = input('\n정말로 데이터를 복원하시겠습니까? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('복원이 취소되었습니다.'))
                return
        
        # 데이터 복원 실행
        with transaction.atomic():
            for model_name in models_to_restore:
                if model_name not in backup_data:
                    self.stdout.write(
                        self.style.WARNING(f'{model_name} 모델 데이터가 백업에 없습니다.')
                    )
                    continue
                
                self._restore_model_data(
                    model_name, 
                    backup_data[model_name], 
                    options['clear_existing'],
                    options['dry_run']
                )
        
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('=== DRY RUN 완료 ==='))
        else:
            self.stdout.write(self.style.SUCCESS('=== 데이터 복원 완료 ==='))

    def _load_backup_file(self, backup_file, storage):
        """백업 파일을 로드합니다"""
        try:
            if storage == 'local':
                return self._load_local_file(backup_file)
            elif storage == 'github':
                return self._load_github_file(backup_file)
            elif storage == 's3':
                return self._load_s3_file(backup_file)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'백업 파일 로드 실패: {str(e)}')
            )
            return None

    def _load_local_file(self, backup_file):
        """로컬 백업 파일을 로드합니다"""
        # 절대 경로가 아닌 경우 backups 디렉토리에서 찾기
        if not os.path.isabs(backup_file):
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            backup_file = os.path.join(backup_dir, backup_file)
        
        if not os.path.exists(backup_file):
            raise FileNotFoundError(f'백업 파일을 찾을 수 없습니다: {backup_file}')
        
        # 파일 확장자에 따라 압축 여부 판단
        is_compressed = backup_file.endswith('.gz')
        
        if is_compressed:
            with gzip.open(backup_file, 'rb') as f:
                content = f.read().decode('utf-8')
                return json.loads(content)
        else:
            with open(backup_file, 'r', encoding='utf-8') as f:
                return json.load(f)

    def _load_github_file(self, backup_file):
        """GitHub Releases에서 백업 파일을 로드합니다"""
        try:
            token = getattr(settings, 'GITHUB_TOKEN', None) or os.getenv('GITHUB_TOKEN')
            repo = getattr(settings, 'GITHUB_BACKUP_REPO', None) or os.getenv('GITHUB_BACKUP_REPO')
            
            if not token or not repo:
                raise ValueError('GitHub 설정이 완료되지 않았습니다.')
            
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # GitHub Releases에서 파일 찾기
            url = f'https://api.github.com/repos/{repo}/releases'
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f'GitHub API 호출 실패: {response.status_code}')
            
            releases = response.json()
            download_url = None
            
            # 파일명으로 검색
            for release in releases:
                if release['tag_name'].startswith('backup-'):
                    for asset in release.get('assets', []):
                        if asset['name'] == backup_file:
                            download_url = asset['browser_download_url']
                            break
                    if download_url:
                        break
            
            if not download_url:
                raise FileNotFoundError(f'GitHub에서 백업 파일을 찾을 수 없습니다: {backup_file}')
            
            # 파일 다운로드
            self.stdout.write(f'GitHub에서 파일 다운로드 중: {download_url}')
            download_response = requests.get(download_url, headers={'Authorization': f'token {token}'})
            download_response.raise_for_status()
            
            file_content = download_response.content
            
            # 압축 여부 판단
            is_compressed = backup_file.endswith('.gz')
            
            if is_compressed:
                import io
                with gzip.GzipFile(fileobj=io.BytesIO(file_content)) as f:
                    return json.load(f)
            else:
                return json.loads(file_content.decode('utf-8'))
                
        except Exception as e:
            raise Exception(f'GitHub에서 파일을 다운로드할 수 없습니다: {str(e)}')

    def _load_s3_file(self, backup_file):
        """S3 백업 파일을 로드합니다"""
        if not HAS_BOTO3:
            raise Exception('boto3 패키지가 필요합니다.')
            
        try:
            # AWS 설정 확인
            aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            bucket_name = getattr(settings, 'AWS_BACKUP_BUCKET_NAME', None)
            
            if not all([aws_access_key, aws_secret_key, bucket_name]):
                raise ValueError('AWS 설정이 완료되지 않았습니다.')
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'ap-northeast-2')
            )
            
            # S3 키 생성
            s3_key = f'backups/{backup_file}' if not backup_file.startswith('backups/') else backup_file
            
            # S3에서 파일 다운로드
            response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
            file_content = response['Body'].read()
            
            # 압축 여부 판단
            is_compressed = backup_file.endswith('.gz')
            
            if is_compressed:
                import io
                with gzip.GzipFile(fileobj=io.BytesIO(file_content)) as f:
                    return json.load(f)
            else:
                return json.loads(file_content.decode('utf-8'))
                
        except ClientError as e:
            raise Exception(f'S3에서 파일을 다운로드할 수 없습니다: {str(e)}')

    def _restore_model_data(self, model_name, model_data, clear_existing, dry_run):
        """특정 모델의 데이터를 복원합니다"""
        try:
            app_label = 'centers'
            model = apps.get_model(app_label, model_name)
            
            record_count = model_data.get('count', 0)
            backup_records = model_data.get('data', [])
            
            self.stdout.write(f'{model_name} 모델 복원 중... ({record_count}개 레코드)')
            
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ [DRY RUN] {model_name}: {record_count}개 레코드 복원 예정')
                )
                return
            
            # 기존 데이터 삭제 (옵션)
            if clear_existing:
                deleted_count = model.objects.count()
                model.objects.all().delete()
                self.stdout.write(f'기존 {model_name} 데이터 {deleted_count}개 삭제')
            
            # 데이터 복원
            if backup_records:
                # JSON 데이터를 다시 serialize 형태로 변환
                serialized_data = json.dumps(backup_records)
                
                # deserialize하여 객체 생성
                objects = []
                for deserialized_obj in serializers.deserialize('json', serialized_data):
                    objects.append(deserialized_obj.object)
                
                # bulk_create로 효율적으로 생성
                if objects:
                    model.objects.bulk_create(objects, ignore_conflicts=True)
                    
                    # 실제 생성된 객체 수 확인
                    created_count = len(objects)
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {model_name}: {created_count}개 레코드 복원 완료')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'- {model_name}: 복원할 데이터가 없습니다')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- {model_name}: 백업 데이터가 비어있습니다')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ {model_name} 복원 실패: {str(e)}')
            ) 