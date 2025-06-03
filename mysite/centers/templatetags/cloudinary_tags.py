from django import template
from django.conf import settings
import os

register = template.Library()

@register.filter
def cloudinary_url(image_obj, transformations=None):
    """
    이미지 객체에서 Cloudinary URL을 우선적으로 반환하는 필터
    
    사용법:
    {{ therapist.photo|cloudinary_url }}
    {{ center_image|cloudinary_url }}
    """
    if not image_obj:
        return None
    
    # CenterImage나 Therapist 객체인 경우
    if hasattr(image_obj, 'image_url') and image_obj.image_url:
        return image_obj.image_url
    elif hasattr(image_obj, 'photo_url') and image_obj.photo_url:
        return image_obj.photo_url
    
    # 로컬 이미지 파일인 경우
    if hasattr(image_obj, 'url'):
        return image_obj.url
    elif hasattr(image_obj, 'image') and hasattr(image_obj.image, 'url'):
        return image_obj.image.url
    elif hasattr(image_obj, 'photo') and hasattr(image_obj.photo, 'url'):
        return image_obj.photo.url
    
    return None

@register.filter
def optimize_cloudinary(url, params="w_300,h_200,c_fill,q_auto"):
    """
    Cloudinary URL에 최적화 파라미터를 추가하는 필터
    
    사용법:
    {{ image_url|optimize_cloudinary:"w_400,h_300,c_fill" }}
    """
    if not url or 'cloudinary.com' not in str(url):
        return url
    
    try:
        parts = str(url).split('/upload/')
        if len(parts) == 2:
            return f"{parts[0]}/upload/{params}/{parts[1]}"
        return url
    except:
        return url

@register.simple_tag
def cloudinary_config():
    """
    Cloudinary 설정이 있는지 확인하는 태그
    
    사용법:
    {% cloudinary_config as has_cloudinary %}
    {% if has_cloudinary %}...{% endif %}
    """
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key = os.getenv('CLOUDINARY_API_KEY')
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
    
    return bool(cloud_name and api_key and api_secret)

@register.inclusion_tag('centers/includes/responsive_image.html')
def responsive_image(image_obj, alt_text="", css_class="", sizes=None):
    """
    반응형 이미지를 렌더링하는 포함 태그
    
    사용법:
    {% responsive_image therapist.photo "상담사 사진" "img-fluid" "300,600,900" %}
    """
    if not sizes:
        sizes = ["300", "600", "900"]  # 기본 크기들
    
    base_url = cloudinary_url(image_obj)
    if not base_url:
        return {'image_url': None}
    
    # 여러 크기의 이미지 URL 생성
    srcset = []
    if 'cloudinary.com' in base_url:
        for size in sizes:
            optimized_url = optimize_cloudinary(base_url, f"w_{size},h_{size},c_fill,q_auto")
            srcset.append(f"{optimized_url} {size}w")
    
    return {
        'image_url': base_url,
        'srcset': ', '.join(srcset) if srcset else None,
        'alt_text': alt_text,
        'css_class': css_class,
        'sizes': "(max-width: 768px) 300px, (max-width: 1024px) 600px, 900px"
    } 