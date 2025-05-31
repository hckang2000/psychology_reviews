# 🗄️ 데이터베이스 호환성 가이드

## 📋 개요

이 프로젝트는 **개발환경(SQLite)**과 **운영환경(PostgreSQL)**을 모두 지원합니다.
데이터베이스별 문법 차이로 인한 오류를 방지하기 위한 가이드입니다.

## ⚠️ 발생했던 문제들

### 1. **PRAGMA 문 오류** 
```
psycopg2.errors.SyntaxError: syntax error at or near "PRAGMA"
```
- **원인**: SQLite 전용 `PRAGMA` 문을 PostgreSQL에서 실행
- **해결**: Django ORM 사용 또는 데이터베이스별 조건문 사용

### 2. **마이그레이션 오류**
```
django.db.utils.ProgrammingError: syntax error at or near "PRAGMA"
```
- **원인**: 마이그레이션 파일에 SQLite 전용 코드
- **해결**: `connection.vendor` 체크 후 조건부 실행

## ✅ 권장 사항

### 1. **Django ORM 우선 사용**
```python
# ❌ 피해야 할 방식 - Raw SQL
cursor.execute('PRAGMA foreign_keys = OFF;')

# ✅ 권장 방식 - Django ORM
center.delete()  # CASCADE 자동 처리
```

### 2. **ForeignKey CASCADE 설정**
```python
# models.py
class Therapist(models.Model):
    center = models.ForeignKey(
        Center, 
        on_delete=models.CASCADE,  # ✅ 필수!
        related_name='therapists'
    )
```

### 3. **데이터베이스별 조건문 사용**
```python
from django.db import connection

if connection.vendor == 'sqlite':
    # SQLite 전용 코드
    cursor.execute('PRAGMA foreign_keys = OFF;')
elif connection.vendor == 'postgresql':
    # PostgreSQL 전용 코드 (보통 불필요)
    pass
```

### 4. **유틸리티 함수 활용**
```python
# database_utils.py 활용
from database_utils import is_sqlite, execute_db_specific_sql

if is_sqlite():
    execute_db_specific_sql(sqlite_sql='PRAGMA foreign_keys = OFF;')
```

## ❌ 피해야 할 것들

### 1. **SQLite 전용 문법**
```python
# ❌ 절대 사용 금지
PRAGMA foreign_keys = OFF;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
```

### 2. **하드코딩된 SQL**
```python
# ❌ 피해야 할 방식
cursor.execute("ALTER TABLE ... DROP CONSTRAINT ...")

# ✅ 권장 방식
from django.db import migrations

def update_foreign_keys(apps, schema_editor):
    if connection.vendor == 'sqlite':
        # SQLite 로직
    elif connection.vendor == 'postgresql':
        # PostgreSQL 로직
```

### 3. **데이터베이스별 특수 함수**
```python
# ❌ SQLite 전용
SELECT ROWID FROM table;

# ❌ PostgreSQL 전용  
SELECT NEXTVAL('sequence_name');

# ✅ Django ORM 사용
Model.objects.create()  # 자동 ID 생성
```

## 🔧 해결된 문제들

### 1. **Admin 삭제 메서드 수정**
```python
# Before (❌)
def delete_model(self, request, obj):
    with connection.cursor() as cursor:
        cursor.execute('PRAGMA foreign_keys = OFF;')
    # 수동 삭제 코드...

# After (✅)  
def delete_model(self, request, obj):
    obj.delete()  # Django ORM CASCADE 사용
```

### 2. **Geocoding API 수정**
```python
# Before (❌)
url = 'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode'
headers = {'X-NCP-APIGW-API-KEY-ID': ...}

# After (✅)
url = 'https://maps.apigw.ntruss.com/map-geocode/v2/geocode'  
headers = {'x-ncp-apigw-api-key-id': ..., 'Accept': 'application/json'}
```

### 3. **마이그레이션 파일 수정**
```python
# Before (❌)
cursor.execute("PRAGMA foreign_keys = OFF;")

# After (✅)
if connection.vendor == 'sqlite':
    cursor.execute("PRAGMA foreign_keys = OFF;")
```

## 🧪 테스트 방법

### 1. **로컬 테스트 (SQLite)**
```bash
python manage.py runserver
# 정상 작동 확인
```

### 2. **PostgreSQL 테스트**
```bash
# Docker PostgreSQL 실행 후
export DATABASE_URL="postgresql://..."
python manage.py migrate
python manage.py runserver
```

### 3. **데이터베이스 유틸리티 테스트**
```bash
python database_utils.py
```

## 📚 참고 자료

- [Django Database Functions](https://docs.djangoproject.com/en/stable/ref/models/database-functions/)
- [Django Migrations](https://docs.djangoproject.com/en/stable/topics/migrations/)
- [PostgreSQL vs SQLite Differences](https://www.postgresql.org/docs/current/sql.html)

## 🚨 주의사항

1. **새로운 기능 개발 시** 항상 두 데이터베이스에서 테스트
2. **Raw SQL 사용 시** 반드시 `connection.vendor` 체크
3. **마이그레이션 작성 시** 데이터베이스 호환성 고려
4. **삭제 작업 시** Django ORM CASCADE 활용

## 📞 문제 발생 시

데이터베이스 호환성 문제 발생 시:

1. `database_utils.py`의 유틸리티 함수 확인
2. Django ORM으로 대체 가능한지 검토  
3. 데이터베이스별 조건문 적용
4. 이 가이드 문서 업데이트

---

**마지막 업데이트**: 2025-05-31  
**작성자**: AI Assistant  
**검토**: 개발팀 