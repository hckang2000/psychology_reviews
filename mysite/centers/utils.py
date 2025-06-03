import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.conf import settings
from django.core.files.storage import default_storage
import os
import logging

logger = logging.getLogger(__name__)

def upload_image_to_cloudinary(image_file, folder='centers'):
    """
    이미지를 Cloudinary에 업로드하고 URL을 반환합니다.
    
    Args:
        image_file: 업로드할 이미지 파일
        folder: Cloudinary 내 저장 폴더명
    
    Returns:
        dict: 업로드 결과 정보 (url, public_id 등)
    """
    try:
        # Cloudinary 설정이 모두 있는지 확인
        cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
        api_key = os.getenv('CLOUDINARY_API_KEY') 
        api_secret = os.getenv('CLOUDINARY_API_SECRET')
        
        if cloud_name and api_key and api_secret:
            # Cloudinary 설정이 있으면 업로드 시도
            print(f"🌐 Cloudinary 업로드 시작: {folder}")
            print(f"🔑 Cloud Name: {cloud_name[:10]}...")
            
            result = cloudinary.uploader.upload(
                image_file,
                folder=folder,
                resource_type="image",
                overwrite=True,
                transformation=[
                    {'quality': 'auto:good'},
                    {'fetch_format': 'auto'}
                ]
            )
            
            upload_url = result.get('secure_url')
            print(f"✅ Cloudinary 업로드 성공: {upload_url}")
            
            return {
                'success': True,
                'url': upload_url,
                'public_id': result.get('public_id'),
                'width': result.get('width'),
                'height': result.get('height')
            }
        else:
            # Cloudinary 설정이 없으면 로컬 저장소만 사용
            print(f"⚠️ Cloudinary 설정 없음 - 로컬 저장소만 사용")
            return {
                'success': True,
                'url': None,  # 로컬에서는 URL 없음
                'public_id': None,
                'message': 'No Cloudinary config - file saved locally only'
            }
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {str(e)}")
        print(f"❌ Cloudinary 업로드 실패: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def delete_image_from_cloudinary(public_id):
    """
    Cloudinary에서 이미지를 삭제합니다.
    
    Args:
        public_id: 삭제할 이미지의 public_id
    
    Returns:
        dict: 삭제 결과
    """
    try:
        # Cloudinary 설정이 모두 있는지 확인
        cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
        api_key = os.getenv('CLOUDINARY_API_KEY') 
        api_secret = os.getenv('CLOUDINARY_API_SECRET')
        
        if cloud_name and api_key and api_secret and public_id:
            result = cloudinary.uploader.destroy(public_id)
            return {
                'success': result.get('result') == 'ok',
                'result': result
            }
        return {'success': True, 'message': 'No Cloudinary config or public_id - no deletion needed'}
    except Exception as e:
        logger.error(f"Cloudinary delete failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_optimized_image_url(url, width=None, height=None, quality='auto:good'):
    """
    Cloudinary URL에 최적화 파라미터를 추가합니다.
    
    Args:
        url: 원본 Cloudinary URL
        width: 원하는 너비
        height: 원하는 높이
        quality: 이미지 품질
    
    Returns:
        str: 최적화된 URL
    """
    if not url:
        return url
    
    try:
        # Cloudinary URL 변환
        transformations = []
        if width:
            transformations.append(f'w_{width}')
        if height:
            transformations.append(f'h_{height}')
        transformations.append(f'q_{quality}')
        transformations.append('f_auto')
        
        if transformations and 'cloudinary.com' in url:
            # URL 구조: https://res.cloudinary.com/cloud_name/image/upload/...
            parts = url.split('/upload/')
            if len(parts) == 2:
                transform_string = ','.join(transformations)
                return f"{parts[0]}/upload/{transform_string}/{parts[1]}"
        
        return url
    except Exception as e:
        logger.error(f"URL optimization failed: {str(e)}")
        return url 