# Intersection Backend — 로컬 실행 및 PostgreSQL 연결 가이드

요약
- 이 백엔드는 FastAPI + SQLAlchemy를 사용합니다.
- 로컬 PostgreSQL(`inter_section`)에 연결하려면 `DATABASE_URL` 환경변수를 설정하세요.

환경변수 설정
1. 루트(`intersection-backend`)에 `.env` 파일을 생성하거나 시스템 환경변수로 설정합니다.
   - 예시 파일: `.env.example`
2. 주요 값
   - DATABASE_URL: postgresql://postgres:password@localhost:5432/inter_section
   - SECRET_KEY: JWT 서명용 비밀키
   - ALGORITHM: HS256 (기본)
   - ACCESS_TOKEN_EXPIRE_MINUTES: 토큰 만료 분

로컬 PostgreSQL 도커 실행(간단)

    docker run --name intersection-postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=inter_section -p 5432:5432 -d postgres:15

의존성 설치

Windows (PowerShell):

    python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install -r requirements.txt

앱 실행

    .\.venv\Scripts\Activate.ps1; uvicorn main:app --reload --host 0.0.0.0 --port 8000

헬스체크
- HTTP: GET http://localhost:8000/health
- DB: GET http://localhost:8000/health/db

프론트엔드 연동
- CORS는 개발용으로 모든 출처를 허용합니다. Flutter에서 http 패키지로 API를 호출하면 됩니다.

문제 해결
- DB 연결 에러: `.env`의 DATABASE_URL 값을 확인하고 Postgres가 실행 중인지 확인하세요.

Docker Compose로 백엔드 + Postgres 실행

1. Docker와 Docker Compose가 설치되어 있어야 합니다.
2. 프로젝트의 `intersection-backend` 폴더에서 아래 명령을 실행하세요:

    docker compose up --build

3. 서비스가 올라오면 아래로 접속 가능합니다:

    - FastAPI: http://localhost:8000
    - DB 포트: 5432 (로컬에서 직접 접근 가능)

환경 변수: `docker-compose.yml`에서 `DATABASE_URL`이 컨테이너 이름 `db`를 가리키도록 설정되어 있습니다.
