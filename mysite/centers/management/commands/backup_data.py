import os
import json
import gzip
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core import serializers
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
    help = '상담센터 데이터를 백업합니다 (JSON 형식으로 압축하여 클라우드에 저장)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--models',
            nargs='+',
            default=['Center', 'Review', 'ExternalReview', 'Therapist', 'CenterImage'],
            help='백업할 모델들을 지정합니다 (기본값: Center Review ExternalReview Therapist CenterImage)'
        )
        parser.add_argument(
            '--storage',
            choices=['github', 's3', 'google_drive', 'local'],
            default='github',
            help='백업 저장 위치를 선택합니다 (기본값: github)'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'xml'],
            default='json',
            help='백업 데이터 형식을 선택합니다 (기본값: json)'
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            default=True,
            help='백업 파일을 gzip으로 압축합니다 (기본값: True)'
        )
        parser.add_argument(
            '--repo',
            help='GitHub 레포지토리 (예: username/repo-name, 환경변수 GITHUB_BACKUP_REPO 사용 가능)'
        )
        parser.add_argument(
            '--token',
            help='GitHub Personal Access Token (환경변수 GITHUB_TOKEN 사용 가능)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== 데이터 백업 시작 ==='))
        
        # GitHub 사용시 설정 확인
        if options['storage'] == 'github':
            repo = options.get('repo') or getattr(settings, 'GITHUB_BACKUP_REPO', None) or os.getenv('GITHUB_BACKUP_REPO')
            token = options.get('token') or getattr(settings, 'GITHUB_TOKEN', None) or os.getenv('GITHUB_TOKEN')
            
            if not repo or not token:
                self.stdout.write(
                    self.style.ERROR('GitHub 백업을 위해서는 GITHUB_TOKEN과 GITHUB_BACKUP_REPO가 필요합니다.')
                )
                self.stdout.write('환경변수 설정: GITHUB_TOKEN=your_token, GITHUB_BACKUP_REPO=username/repo-name')
                return
        
        # S3 사용시 boto3 확인
        if options['storage'] == 's3' and not HAS_BOTO3:
            self.stdout.write(
                self.style.ERROR('S3 백업을 위해서는 boto3 패키지가 필요합니다. pip install boto3')
            )
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_data = {}
        
        # 각 모델별로 데이터 백업
        for model_name in options['models']:
            try:
                app_label = 'centers'  # centers 앱의 모델들
                model = apps.get_model(app_label, model_name)
                
                self.stdout.write(f'{model_name} 모델 백업 중...')
                
                # 모델의 모든 데이터를 serialize
                queryset = model.objects.all()
                serialized_data = serializers.serialize(options['format'], queryset)
                
                backup_data[model_name] = {
                    'count': queryset.count(),
                    'data': json.loads(serialized_data) if options['format'] == 'json' else serialized_data
                }
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {model_name}: {queryset.count()}개 레코드 백업 완료')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ {model_name} 백업 실패: {str(e)}')
                )
                continue

        if not backup_data:
            self.stdout.write(self.style.ERROR('백업할 데이터가 없습니다.'))
            return

        # 백업 메타데이터 추가
        backup_data['_metadata'] = {
            'backup_time': timestamp,
            'django_version': getattr(settings, 'DJANGO_VERSION', 'unknown'),
            'total_models': len(backup_data) - 1,  # _metadata 제외
            'backup_format': options['format'],
            'storage_type': options['storage']
        }

        # JSON 문자열로 변환
        backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        # 파일명 생성
        filename = f'backup_{timestamp}.{options["format"]}'
        if options['compress']:
            filename += '.gz'

        # 저장 위치에 따른 처리
        if options['storage'] == 'local':
            self._save_local(backup_json, filename, options['compress'])
        elif options['storage'] == 'github':
            self._save_github(backup_json, filename, options['compress'], repo, token, timestamp)
        elif options['storage'] == 's3':
            self._save_s3(backup_json, filename, options['compress'])
        elif options['storage'] == 'google_drive':
            self._save_google_drive(backup_json, filename, options['compress'])

        self.stdout.write(
            self.style.SUCCESS(f'=== 백업 완료: {filename} ===')
        )

    def _save_local(self, data, filename, compress):
        """로컬에 백업 파일 저장"""
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        filepath = os.path.join(backup_dir, filename)
        
        if compress:
            with gzip.open(filepath, 'wb') as f:
                f.write(data.encode('utf-8'))
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(data)
                
        self.stdout.write(f'로컬에 저장 완료: {filepath}')

    def _save_github(self, data, filename, compress, repo, token, timestamp):
        """GitHub Releases에 백업 파일 저장"""
        try:
            # 데이터 압축 처리
            if compress:
                import io
                buffer = io.BytesIO()
                with gzip.GzipFile(fileobj=buffer, mode='wb') as f:
                    f.write(data.encode('utf-8'))
                upload_data = buffer.getvalue()
            else:
                upload_data = data.encode('utf-8')
            
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # 1. Release 생성
            tag_name = f'backup-{timestamp}'
            release_data = {
                'tag_name': tag_name,
                'name': f'Data Backup {timestamp}',
                'body': f'Automated backup created on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                'draft': False,
                'prerelease': True
            }
            
            create_url = f'https://api.github.com/repos/{repo}/releases'
            response = requests.post(create_url, headers=headers, json=release_data)
            
            if response.status_code != 201:
                raise Exception(f'Release 생성 실패: {response.status_code} - {response.text}')
            
            upload_url = response.json()['upload_url'].replace('{?name,label}', '')
            
            # 2. 파일 업로드
            upload_headers = {
                'Authorization': f'token {token}',
                'Content-Type': 'application/gzip' if compress else 'application/json'
            }
            
            upload_response = requests.post(
                f'{upload_url}?name={filename}',
                headers=upload_headers,
                data=upload_data
            )
            
            if upload_response.status_code == 201:
                download_url = upload_response.json()['browser_download_url']
                self.stdout.write(f'GitHub에 저장 완료: {download_url}')
            else:
                raise Exception(f'파일 업로드 실패: {upload_response.status_code}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'GitHub 백업 실패: {str(e)}')
            )

    def _save_s3(self, data, filename, compress):
        """AWS S3에 백업 파일 저장"""
        if not HAS_BOTO3:
            self.stdout.write(
                self.style.ERROR('boto3 패키지가 필요합니다.')
            )
            return
            
        try:
            # AWS 설정 확인
            aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            bucket_name = getattr(settings, 'AWS_BACKUP_BUCKET_NAME', None)
            
            if not all([aws_access_key, aws_secret_key, bucket_name]):
                self.stdout.write(
                    self.style.ERROR('AWS 설정이 완료되지 않았습니다. settings에서 AWS 설정을 확인하세요.')
                )
                return
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'ap-northeast-2')
            )
            
            # 데이터 준비
            if compress:
                import io
                buffer = io.BytesIO()
                with gzip.GzipFile(fileobj=buffer, mode='wb') as f:
                    f.write(data.encode('utf-8'))
                upload_data = buffer.getvalue()
            else:
                upload_data = data.encode('utf-8')
            
            # S3에 업로드
            s3_key = f'backups/{filename}'
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=upload_data,
                ContentType='application/gzip' if compress else 'application/json',
                Metadata={
                    'backup-type': 'django-data',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            self.stdout.write(f'S3에 저장 완료: s3://{bucket_name}/{s3_key}')
            
        except ClientError as e:
            self.stdout.write(
                self.style.ERROR(f'S3 업로드 실패: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'S3 백업 중 오류 발생: {str(e)}')
            )

    def _save_google_drive(self, data, filename, compress):
        """Google Drive에 백업 파일 저장 (Webhook 방식)"""
        try:
            webhook_url = getattr(settings, 'GOOGLE_DRIVE_WEBHOOK_URL', None)
            
            if not webhook_url:
                self.stdout.write(
                    self.style.ERROR('Google Drive Webhook URL이 설정되지 않았습니다.')
                )
                return
            
            # 데이터 준비
            if compress:
                import base64
                import io
                buffer = io.BytesIO()
                with gzip.GzipFile(fileobj=buffer, mode='wb') as f:
                    f.write(data.encode('utf-8'))
                upload_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            else:
                upload_data = data
            
            # Webhook으로 전송
            payload = {
                'filename': filename,
                'data': upload_data,
                'compressed': compress,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            
            self.stdout.write(f'Google Drive에 저장 완료: {filename}')
            
        except requests.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'Google Drive 업로드 실패: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Google Drive 백업 중 오류 발생: {str(e)}')
            ) 