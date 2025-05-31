"""
데이터베이스 호환성 유틸리티
PostgreSQL과 SQLite 모두에서 작동하는 코드를 위한 헬퍼 함수들
"""

from django.db import connection


def is_sqlite():
    """현재 데이터베이스가 SQLite인지 확인"""
    return connection.vendor == 'sqlite'


def is_postgresql():
    """현재 데이터베이스가 PostgreSQL인지 확인"""
    return connection.vendor == 'postgresql'


def execute_db_specific_sql(sqlite_sql=None, postgresql_sql=None, mysql_sql=None):
    """
    데이터베이스별로 다른 SQL을 실행하는 함수
    
    Args:
        sqlite_sql: SQLite에서 실행할 SQL
        postgresql_sql: PostgreSQL에서 실행할 SQL  
        mysql_sql: MySQL에서 실행할 SQL
    """
    with connection.cursor() as cursor:
        if connection.vendor == 'sqlite' and sqlite_sql:
            cursor.execute(sqlite_sql)
        elif connection.vendor == 'postgresql' and postgresql_sql:
            cursor.execute(postgresql_sql)
        elif connection.vendor == 'mysql' and mysql_sql:
            cursor.execute(mysql_sql)
        else:
            # 지원하지 않는 데이터베이스이거나 해당 SQL이 없는 경우
            print(f"⚠️ {connection.vendor} 데이터베이스에 대한 SQL이 제공되지 않았습니다.")


def safe_foreign_key_operation(operation_func):
    """
    Foreign Key 제약 조건을 안전하게 처리하면서 작업을 수행하는 데코레이터
    
    Args:
        operation_func: 실행할 함수
    """
    def wrapper(*args, **kwargs):
        try:
            # SQLite에서만 Foreign Key 제약 조건 임시 비활성화
            if is_sqlite():
                execute_db_specific_sql(sqlite_sql='PRAGMA foreign_keys = OFF;')
            
            # 실제 작업 수행
            result = operation_func(*args, **kwargs)
            
            return result
            
        finally:
            # SQLite에서만 Foreign Key 제약 조건 다시 활성화
            if is_sqlite():
                execute_db_specific_sql(sqlite_sql='PRAGMA foreign_keys = ON;')
    
    return wrapper


def get_database_info():
    """현재 데이터베이스 정보 반환"""
    return {
        'vendor': connection.vendor,
        'database_name': connection.settings_dict.get('NAME'),
        'host': connection.settings_dict.get('HOST'),
        'port': connection.settings_dict.get('PORT'),
    }


# 데이터베이스별 권장 사항 출력
def print_database_compatibility_guide():
    """데이터베이스 호환성 가이드 출력"""
    print("=" * 60)
    print("🗄️ 데이터베이스 호환성 가이드")
    print("=" * 60)
    print("✅ 권장사항:")
    print("  1. PRAGMA 문 사용 금지 - SQLite 전용")
    print("  2. Django ORM 사용 - 모든 DB 호환")
    print("  3. Raw SQL 최소화")
    print("  4. ForeignKey에 on_delete=CASCADE 설정")
    print("  5. 마이그레이션에서 데이터베이스별 조건문 사용")
    print()
    print("❌ 피해야 할 것들:")
    print("  - PRAGMA foreign_keys = OFF/ON")
    print("  - SQLite 전용 함수들")
    print("  - 데이터베이스별 특수 문법")
    print("=" * 60)


if __name__ == "__main__":
    # 직접 실행시 가이드 출력
    print_database_compatibility_guide()
    print(f"현재 데이터베이스: {get_database_info()}") 