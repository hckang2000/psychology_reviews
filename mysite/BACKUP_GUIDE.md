# 데이터 백업 시스템 가이드

MindScanner 프로젝트의 데이터 백업 시스템 사용법입니다.

## 🎯 주요 기능

- **자동/수동 백업**: Django management 명령어로 백업 실행
- **다중 저장소 지원**: Local, AWS S3, GitHub, Dropbox, PostgreSQL dump 지원
- **압축 백업**: gzip 압축으로 저장 공간 절약
- **스케줄링**: 일/주/시간 단위 자동 백업
- **복원 기능**: 백업된 데이터를 안전하게 복원
- **백업 관리**: 백업 파일 목록 조회 및 관리

## 💰 백업 방법별 비교

| 방법 | 무료 용량 | 장점 | 단점 |
|------|----------|------|------|
| **GitHub Releases** | 2GB/파일, 무제한 | 개발자 친화적, 버전관리 | Public repo시 백업 공개 |
| **Dropbox** | 2GB | 쉬운 설정, 안정적 | 용량 제한 |
| **AWS S3** | 5GB (12개월) | 전문적, 확장성 좋음 | 계정 필요, 유료 전환 |
| **로컬 백업** | 서버 용량 | 빠름, 간단 | 서버 장애시 위험 |
| **PostgreSQL Dump** | 서버 용량 | 완전한 DB 백업 | 파일 크기 큼 |

## 🆓 **무료 백업 솔루션 (AWS 계정 없이도 OK!)**

### 1. GitHub Releases 백업 (🌟 추천!)

#### 설정 방법:
1. GitHub Personal Access Token 생성:
   - GitHub → Settings → Developer settings → Personal access tokens
   - `repo` 권한 체크
2. 환경변수 설정: `GITHUB_TOKEN=your_token`

#### 사용법:
```bash
# GitHub에 백업
python manage.py backup_to_github --repo username/repo-name

# 환경변수로 토큰 설정시
export GITHUB_TOKEN=your_token
python manage.py backup_to_github --repo username/repo-name
```

### 2. Dropbox 백업 (무료 2GB)

#### 설정 방법:
1. Dropbox App 생성: https://www.dropbox.com/developers/apps
2. Access Token 생성
3. 환경변수 설정: `DROPBOX_TOKEN=your_token`

#### 사용법:
```bash
# Dropbox에 백업
python manage.py backup_to_dropbox

# 토큰을 직접 지정
python manage.py backup_to_dropbox --token your_token
```

### 3. PostgreSQL 전체 DB 백업

#### 사용법:
```bash
# 로컬에 PostgreSQL dump 백업
python manage.py backup_with_pg_dump

# Dropbox에 업로드하면서 백업
python manage.py backup_with_pg_dump --upload-to dropbox

# 압축 없이 백업
python manage.py backup_with_pg_dump --compress=False
```

## 📋 백업되는 데이터

- **Center**: 상담센터 정보
- **InternalReview**: 내부 리뷰
- **ExternalReview**: 외부 리뷰  
- **Therapist**: 상담사 정보

## 🚀 **기본 백업 사용법** (GitHub 중심)

### 1. 수동 백업

#### GitHub에 백업 (기본, 추천)
```bash
# 기본 백업 명령어 (GitHub로 자동 저장)
python manage.py backup_data

# 특정 리포지토리 지정
python manage.py backup_data --repo username/backup-repo

# 특정 모델만 백업
python manage.py backup_data --models Center Therapist

# 압축하지 않고 백업
python manage.py backup_data --compress=False
```

#### 기존 GitHub 명령어
```bash
# 별도 GitHub 백업 명령어 (기존 유지)
python manage.py backup_to_github --repo username/repo-name
```

#### 다른 저장소에 백업
```bash
# 로컬에 백업
python manage.py backup_data --storage local

# AWS S3에 백업
python manage.py backup_data --storage s3
```

### 2. 백업 파일 목록 확인

#### GitHub 백업 목록 (기본)
```bash
# GitHub 백업 파일 목록
python manage.py list_backups

# 상세 정보와 함께 목록
python manage.py list_backups --details

# 최신 10개만 표시
python manage.py list_backups --limit 10
```

#### 모든 저장소 확인
```bash
# 모든 저장소의 백업 파일 목록
python manage.py list_backups --storage all

# 로컬 백업만 확인
python manage.py list_backups --storage local

# S3 백업만 확인
python manage.py list_backups --storage s3
```

### 3. 데이터 복원

#### GitHub에서 복원 (기본)
```bash
# GitHub 백업 파일 복원
python manage.py restore_data backup_20231201_143000.json.gz

# 복원 시뮬레이션 (실제 복원하지 않음)
python manage.py restore_data backup_20231201_143000.json.gz --dry-run

# 기존 데이터 삭제 후 복원 (주의!)
python manage.py restore_data backup_20231201_143000.json.gz --clear-existing
```

#### 다른 저장소에서 복원
```bash
# 로컬 백업 파일 복원
python manage.py restore_data backup_20231201_143000.json.gz --storage local

# S3 백업 파일 복원
python manage.py restore_data backup_20231201_143000.json.gz --storage s3
```

### 4. 자동 백업 스케줄링

#### GitHub 자동 백업 (기본)
```bash
# 매일 새벽 2시에 GitHub 백업
python manage.py schedule_backups

# 매일 새벽 3시에 백업
python manage.py schedule_backups --time 03:00

# 매주 일요일 새벽 2시에 백업
python manage.py schedule_backups --interval weekly

# 한 번만 백업하고 종료
python manage.py schedule_backups --once
```

#### 백그라운드에서 실행
```bash
# 백그라운드에서 자동 백업 실행
python manage.py schedule_backups --daemon --interval daily --time 02:00

# 매시간 백업 (테스트용)
python manage.py schedule_backups --interval hourly --daemon
```

#### 다른 저장소로 자동 백업
```bash
# S3로 자동 백업
python manage.py schedule_backups --storage s3 --time 02:00

# 로컬로 자동 백업
python manage.py schedule_backups --storage local --interval daily
```

## ⚙️ 환경변수 설정

`.env` 파일에 다음 변수들을 설정하세요:

### GitHub 백업용 (무료, 추천!)
```env
GITHUB_TOKEN=your_personal_access_token
GITHUB_BACKUP_REPO=username/repo-name
```

### Dropbox 백업용 (무료 2GB)
```env
DROPBOX_TOKEN=your_dropbox_access_token
```

### AWS S3 백업용 (선택사항)
```env
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_BACKUP_BUCKET_NAME=your-backup-bucket-name
AWS_S3_REGION_NAME=ap-northeast-2
```

### Google Drive 백업용 (선택사항)
```env
GOOGLE_DRIVE_WEBHOOK_URL=https://your-webhook-url.com/backup
```

### 백업 기본 설정
```env
BACKUP_RETENTION_DAYS=30
BACKUP_DEFAULT_STORAGE=local
BACKUP_COMPRESS_DEFAULT=True
```

## 🏗️ Render 배포 환경 설정

### 무료 옵션 사용시 (GitHub/Dropbox)

#### 1. 환경변수 설정 (Render 대시보드)
```env
# GitHub 백업 (추천)
GITHUB_TOKEN=your_token
GITHUB_BACKUP_REPO=username/repo-name

# 또는 Dropbox 백업
DROPBOX_TOKEN=your_dropbox_token
```

#### 2. Cron Job 설정 (Render Cron Jobs 서비스)
```bash
# GitHub에 매일 새벽 2시 백업
0 2 * * * cd /opt/render/project/src && python manage.py backup_to_github --repo username/repo-name

# Dropbox에 매일 새벽 2시 백업  
0 2 * * * cd /opt/render/project/src && python manage.py backup_to_dropbox

# PostgreSQL dump 백업 (더 완전한 백업)
0 2 * * * cd /opt/render/project/src && python manage.py backup_with_pg_dump --upload-to dropbox
```

### AWS 사용시

#### 1. 환경변수 설정
Render 대시보드에서 Environment Variables 설정:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_BACKUP_BUCKET_NAME`
- `BACKUP_DEFAULT_STORAGE=s3`

#### 2. Cron Job 설정
```bash
# 매일 새벽 2시에 백업 실행
0 2 * * * cd /opt/render/project/src && python manage.py backup_data --storage s3
```

## 🔧 고급 사용법

### 백업 파일 구조
```json
{
  "Center": {
    "count": 10,
    "data": [...]
  },
  "InternalReview": {
    "count": 25,
    "data": [...]
  },
  "_metadata": {
    "backup_time": "20231201_143000",
    "total_models": 4,
    "backup_format": "json"
  }
}
```

### GitHub Personal Access Token 생성 방법
1. GitHub 로그인 → Settings
2. Developer settings → Personal access tokens → Tokens (classic)
3. Generate new token (classic)
4. 권한: `repo` 체크
5. 생성된 토큰 복사

### Dropbox App 설정
1. https://www.dropbox.com/developers/apps 접속
2. Create app 클릭
3. Scoped access → Full Dropbox 선택
4. App name 입력
5. Settings → Generate access token

### AWS S3 버킷 설정
1. S3 버킷 생성
2. IAM 사용자 생성 및 권한 부여:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:PutObject",
           "s3:DeleteObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::your-backup-bucket/*",
           "arn:aws:s3:::your-backup-bucket"
         ]
       }
     ]
   }
   ```

## 🚨 주의사항

1. **복원 시 주의**: `--clear-existing` 옵션은 기존 데이터를 완전히 삭제합니다.
2. **권한 확인**: 백업/복원은 충분한 권한이 있는 사용자만 실행해야 합니다.
3. **용량 관리**: 정기적으로 오래된 백업 파일을 정리하세요.
4. **테스트**: 복원 전에 반드시 `--dry-run` 옵션으로 테스트하세요.
5. **보안**: Private 저장소 사용을 권장합니다.

## 💡 추천 백업 전략

### 소규모 프로젝트 (무료)
```bash
# 매일 GitHub에 자동 백업
0 2 * * * python manage.py backup_to_github --repo username/backup-repo
```

### 중간 규모 프로젝트
```bash
# 매일 GitHub + 주간 PostgreSQL dump
0 2 * * * python manage.py backup_to_github --repo username/backup-repo
0 3 * * 0 python manage.py backup_with_pg_dump --upload-to dropbox
```

### 대규모 프로젝트
```bash
# AWS S3 + 이중화
0 2 * * * python manage.py backup_data --storage s3
0 3 * * * python manage.py backup_to_github --repo username/backup-repo
```

## 🆘 문제 해결

### 백업 실패시
1. 권한 확인 (토큰, API 키)
2. 네트워크 연결 확인
3. 디스크 공간 확인
4. 로그 파일 확인: `logs/backup.log`

### 복원 실패시
1. 백업 파일 무결성 확인
2. 데이터베이스 연결 확인
3. 모델 호환성 확인

## 📞 지원

문제가 발생하면 다음 로그를 확인하세요:
- `logs/backup.log`
- Django 로그
- 서버 로그

---

**⚠️ 중요**: 백업은 정기적으로 실행하고, 복원 테스트를 주기적으로 수행하여 백업의 유효성을 확인하세요.

**🎉 무료 옵션 추천**: AWS 계정이 없다면 GitHub Releases를 이용한 백업이 가장 좋습니다! 