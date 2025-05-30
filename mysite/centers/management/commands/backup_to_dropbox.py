import os
import json
import gzip
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core import serializers
from django.apps import apps
from django.conf import settings
import requests


class Command(BaseCommand):
    help = 'Dropbox API를 이용해 데이터를 백업합니다 (무료 2GB)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--models',
            nargs='+',
            default=['Center', 'Review', 'ExternalReview', 'Therapist', 'CenterImage', 'ReviewComment'],
            help='백업할 모델들을 지정합니다'
        )
        parser.add_argument(
            '--token',
            help='Dropbox Access Token (환경변수 DROPBOX_TOKEN 사용 가능)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Dropbox 백업 시작 ==='))
        
        # Dropbox 토큰 확인
        token = options.get('token') or os.getenv('DROPBOX_TOKEN')
        if not token:
            self.stdout.write(
                self.style.ERROR('Dropbox Token이 필요합니다. --token 옵션이나 DROPBOX_TOKEN 환경변수를 설정하세요.')
            )
            self.stdout.write('토큰 생성: https://www.dropbox.com/developers/apps')
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 데이터 백업
        backup_data = self._create_backup_data(options['models'])
        if not backup_data:
            return
        
        # JSON 압축
        backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        import io
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wt', encoding='utf-8') as f:
            f.write(backup_json)
        compressed_data = buffer.getvalue()
        
        # Dropbox 업로드
        filename = f'backups/backup_{timestamp}.json.gz'
        success = self._upload_to_dropbox(token, filename, compressed_data)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f'=== Dropbox 백업 완료: {filename} ===')
            )
        else:
            self.stdout.write(self.style.ERROR('Dropbox 백업 실패'))

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
                'backup_method': 'dropbox'
            }
        
        return backup_data

    def _upload_to_dropbox(self, token, filename, data):
        """Dropbox에 파일을 업로드합니다"""
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/octet-stream',
                'Dropbox-API-Arg': json.dumps({
                    'path': f'/{filename}',
                    'mode': 'overwrite',
                    'autorename': False
                })
            }
            
            response = requests.post(
                'https://content.dropboxapi.com/2/files/upload',
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.stdout.write(f'업로드 완료: {result["name"]} ({result["size"]} bytes)')
                return True
            else:
                self.stdout.write(
                    self.style.ERROR(f'업로드 실패: {response.status_code} - {response.text}')
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Dropbox 업로드 중 오류: {str(e)}')
            )
            return False 