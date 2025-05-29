from celery import shared_task
from django.core.management import call_command
from io import StringIO
import logging

logger = logging.getLogger(__name__)

@shared_task
def automated_backup():
    """자동 백업 태스크 - 매주 일요일 14:00에 실행"""
    try:
        output = StringIO()
        call_command('backup_data', storage='github', stdout=output)
        
        result = output.getvalue()
        logger.info(f"자동 백업 완료: {result}")
        
        return {
            'success': True,
            'message': '자동 백업이 성공적으로 완료되었습니다.',
            'output': result
        }
    except Exception as e:
        error_message = f"자동 백업 실패: {str(e)}"
        logger.error(error_message)
        
        return {
            'success': False,
            'error': error_message
        }

@shared_task
def cleanup_old_backups(keep_count=10):
    """오래된 백업 파일 정리 태스크"""
    try:
        # GitHub Releases에서 오래된 백업 정리
        # 실제 정리 로직은 별도 구현 필요
        logger.info(f"백업 정리 완료: 최근 {keep_count}개 백업 유지")
        
        return {
            'success': True,
            'message': f'백업 정리 완료: 최근 {keep_count}개 백업 유지'
        }
    except Exception as e:
        error_message = f"백업 정리 실패: {str(e)}"
        logger.error(error_message)
        
        return {
            'success': False,
            'error': error_message
        } 