import os
import json
import gzip
import tarfile
import tempfile
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
    help = '상담센터 데이터를 백업합니다 (JSON 형식으로 압축하여 클라우드에 저장, 미디어 파일 포함)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--models',
            nargs='+',
            default=['Center', 'Review', 'ExternalReview', 'Therapist', 'CenterImage', 'ReviewComment'],
            help='백업할 모델들을 지정합니다 (기본값: Center Review ExternalReview Therapist CenterImage ReviewComment)'
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
            '--include-media',
            action='store_true',
            default=True,
            help='미디어 파일도 함께 백업합니다 (기본값: True)'
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
            'storage_type': options['storage'],
            'includes_media': options['include_media']
        }

        # JSON 문자열로 변환
        backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        # 파일명 생성
        data_filename = f'backup_{timestamp}.{options["format"]}'
        media_filename = f'media_{timestamp}.tar.gz'
        
        if options['compress']:
            data_filename += '.gz'

        # 미디어 파일 백업
        media_archive_path = None
        if options['include_media']:
            media_archive_path = self._create_media_archive(timestamp)
            if media_archive_path:
                self.stdout.write(self.style.SUCCESS('✓ 미디어 파일 아카이브 생성 완료'))

        # 저장 위치에 따른 처리
        if options['storage'] == 'local':
            self._save_local(backup_json, data_filename, options['compress'])
            if media_archive_path:
                self._save_media_local(media_archive_path, media_filename)
        elif options['storage'] == 'github':
            self._save_github(backup_json, data_filename, options['compress'], repo, token, timestamp, media_archive_path, media_filename)
        elif options['storage'] == 's3':
            self._save_s3(backup_json, data_filename, options['compress'])
        elif options['storage'] == 'google_drive':
            self._save_google_drive(backup_json, data_filename, options['compress'])

        # 임시 미디어 아카이브 파일 정리
        if media_archive_path and os.path.exists(media_archive_path):
            os.remove(media_archive_path)

        self.stdout.write(
            self.style.SUCCESS(f'=== 백업 완료: {data_filename} ===')
        )

    def _create_media_archive(self, timestamp):
        """미디어 파일들을 tar.gz로 압축합니다"""
        try:
            media_root = settings.MEDIA_ROOT
            if not os.path.exists(media_root):
                self.stdout.write(self.style.WARNING('미디어 폴더가 존재하지 않습니다.'))
                return None

            # 임시 파일 생성
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
            temp_file.close()
            
            with tarfile.open(temp_file.name, 'w:gz') as tar:
                # centers/ 폴더 (상담소 이미지)
                centers_path = os.path.join(media_root, 'centers')
                if os.path.exists(centers_path):
                    tar.add(centers_path, arcname='centers')
                    self.stdout.write(f'✓ 상담소 이미지 폴더 추가: {centers_path}')
                
                # therapists/ 폴더 (상담사 이미지)
                therapists_path = os.path.join(media_root, 'therapists')
                if os.path.exists(therapists_path):
                    tar.add(therapists_path, arcname='therapists')
                    self.stdout.write(f'✓ 상담사 이미지 폴더 추가: {therapists_path}')
                
                # 기타 업로드 파일들
                for item in os.listdir(media_root):
                    item_path = os.path.join(media_root, item)
                    if os.path.isfile(item_path):
                        tar.add(item_path, arcname=item)
            
            return temp_file.name
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'미디어 파일 아카이브 생성 실패: {str(e)}')
            )
            return None

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

    def _save_media_local(self, media_archive_path, media_filename):
        """로컬에 미디어 아카이브 저장"""
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        dest_path = os.path.join(backup_dir, media_filename)
        
        import shutil
        shutil.copy2(media_archive_path, dest_path)
        self.stdout.write(f'미디어 파일 로컬 저장 완료: {dest_path}')

    def _save_github(self, data, data_filename, compress, repo, token, timestamp, media_archive_path, media_filename):
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
                'name': f'Complete Backup {timestamp}',
                'body': f'''자동 백업 생성일: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

📊 **백업 내용:**
- 데이터베이스: {data_filename}
- 미디어 파일: {media_filename if media_archive_path else "미디어 파일 없음"}

⚠️ **복원 시 주의사항:**
- 두 파일을 모두 다운로드하여 복원해야 완전한 복원이 가능합니다
- 데이터 파일만으로는 이미지가 복원되지 않습니다''',
                'draft': False,
                'prerelease': True
            }
            
            create_url = f'https://api.github.com/repos/{repo}/releases'
            response = requests.post(create_url, headers=headers, json=release_data)
            
            if response.status_code != 201:
                raise Exception(f'Release 생성 실패: {response.status_code} - {response.text}')
            
            upload_url = response.json()['upload_url'].replace('{?name,label}', '')
            
            # 2. 데이터 파일 업로드
            upload_headers = {
                'Authorization': f'token {token}',
                'Content-Type': 'application/gzip' if compress else 'application/json'
            }
            
            upload_response = requests.post(
                f'{upload_url}?name={data_filename}',
                headers=upload_headers,
                data=upload_data
            )
            
            if upload_response.status_code == 201:
                download_url = upload_response.json()['browser_download_url']
                self.stdout.write(f'데이터 파일 GitHub에 저장 완료: {download_url}')
            else:
                raise Exception(f'데이터 파일 업로드 실패: {upload_response.status_code}')
            
            # 3. 미디어 파일 업로드
            if media_archive_path and os.path.exists(media_archive_path):
                with open(media_archive_path, 'rb') as f:
                    media_data = f.read()
                
                media_headers = {
                    'Authorization': f'token {token}',
                    'Content-Type': 'application/gzip'
                }
                
                media_response = requests.post(
                    f'{upload_url}?name={media_filename}',
                    headers=media_headers,
                    data=media_data
                )
                
                if media_response.status_code == 201:
                    media_download_url = media_response.json()['browser_download_url']
                    self.stdout.write(f'미디어 파일 GitHub에 저장 완료: {media_download_url}')
                else:
                    self.stdout.write(f'미디어 파일 업로드 실패: {media_response.status_code}')
                
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