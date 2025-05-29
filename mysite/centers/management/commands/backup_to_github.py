import os
import json
import gzip
import base64
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core import serializers
from django.apps import apps
from django.conf import settings
import requests


class Command(BaseCommand):
    help = 'GitHub Releases를 이용해 데이터를 백업합니다 (무료)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--models',
            nargs='+',
            default=['Center', 'Review', 'ExternalReview', 'Therapist', 'CenterImage'],
            help='백업할 모델들을 지정합니다'
        )
        parser.add_argument(
            '--repo',
            required=True,
            help='GitHub 레포지토리 (예: username/repo-name)'
        )
        parser.add_argument(
            '--token',
            help='GitHub Personal Access Token (환경변수 GITHUB_TOKEN 사용 가능)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== GitHub 백업 시작 ==='))
        
        # GitHub 토큰 확인
        token = options.get('token') or os.getenv('GITHUB_TOKEN')
        if not token:
            self.stdout.write(
                self.style.ERROR('GitHub Token이 필요합니다. --token 옵션이나 GITHUB_TOKEN 환경변수를 설정하세요.')
            )
            return
        
        repo = options['repo']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 데이터 백업
        backup_data = self._create_backup_data(options['models'])
        if not backup_data:
            return
        
        # JSON 압축
        backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        import io
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb') as f:
            f.write(backup_json.encode('utf-8'))
        compressed_data = buffer.getvalue()
        
        # GitHub Release 생성
        filename = f'backup_{timestamp}.json.gz'
        success = self._upload_to_github(repo, token, filename, compressed_data, timestamp)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f'=== GitHub 백업 완료: {filename} ===')
            )
        else:
            self.stdout.write(self.style.ERROR('GitHub 백업 실패'))

    def _create_backup_data(self, model_names):
        """백업 데이터를 생성합니다"""
        backup_data = {}
        
        for model_name in model_names:
            try:
                app_label = 'centers'
                model = apps.get_model(app_label, model_name)
                
                self.stdout.write(f'{model_name} 모델 백업 중...')
                
                queryset = model.objects.all()
                serialized_data = serializers.serialize('json', queryset)
                
                backup_data[model_name] = {
                    'count': queryset.count(),
                    'data': json.loads(serialized_data)
                }
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {model_name}: {queryset.count()}개 레코드')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ {model_name} 백업 실패: {str(e)}')
                )
                continue
        
        if backup_data:
            # 메타데이터 추가
            backup_data['_metadata'] = {
                'backup_time': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'total_models': len(backup_data),
                'backup_format': 'json',
                'backup_method': 'github_releases'
            }
        
        return backup_data

    def _upload_to_github(self, repo, token, filename, data, timestamp):
        """GitHub Releases에 파일을 업로드합니다"""
        try:
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
                self.stdout.write(
                    self.style.ERROR(f'Release 생성 실패: {response.status_code} - {response.text}')
                )
                return False
            
            release_id = response.json()['id']
            upload_url = response.json()['upload_url'].replace('{?name,label}', '')
            
            # 2. 파일 업로드
            upload_headers = {
                'Authorization': f'token {token}',
                'Content-Type': 'application/gzip'
            }
            
            upload_response = requests.post(
                f'{upload_url}?name={filename}',
                headers=upload_headers,
                data=data
            )
            
            if upload_response.status_code == 201:
                download_url = upload_response.json()['browser_download_url']
                self.stdout.write(f'업로드 완료: {download_url}')
                return True
            else:
                self.stdout.write(
                    self.style.ERROR(f'파일 업로드 실패: {upload_response.status_code}')
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'GitHub 업로드 중 오류: {str(e)}')
            )
            return False 