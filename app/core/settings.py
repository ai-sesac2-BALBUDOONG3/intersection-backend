from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional
from urllib.parse import quote_plus


class Settings:
    """
    Intersection 백엔드 공통 설정.

    - .env / App Service 애플리케이션 설정에서 값을 읽어서 사용
    - DATABASE_URL 이 명시되면 그 값을 우선, 없으면 DB_HOST/DB_USER 등으로 조합
    """

    def __init__(self) -> None:
        # ===== 기본 환경 =====
        self.env: str = os.getenv("ENV", "dev")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        # ===== 보안 키 =====
        self.secret_key: str = os.getenv("SECRET_KEY", "CHANGE_ME_SECRET_KEY")

        # ===== DB 설정 =====
        self.db_host: str = os.getenv("DB_HOST", "localhost")
        self.db_port: int = int(os.getenv("DB_PORT", "5432"))
        self.db_name: str = os.getenv("DB_NAME", "intersection_db")
        self.db_user: str = os.getenv("DB_USER", "postgres")
        self.db_password: str = os.getenv("DB_PASSWORD", "")

        explicit_url = os.getenv("DATABASE_URL")

        if explicit_url:
            # App Service / 로컬에서 DATABASE_URL 을 직접 지정한 경우
            self.database_url: str = explicit_url
        else:
            # Azure PostgreSQL 기본 접속 문자열 조합
            # 비밀번호는 URL 인코딩 처리 (예: @ -> %40)
            password_escaped = quote_plus(self.db_password)
            self.database_url = (
                f"postgresql+psycopg2://{self.db_user}:{password_escaped}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}?sslmode=require"
            )

        # ===== Azure OpenAI (aoai-intersection-prod) =====
        self.azure_openai_endpoint: Optional[str] = os.getenv(
            "AZURE_OPENAI_ENDPOINT"
        )
        self.azure_openai_api_key: Optional[str] = os.getenv(
            "AZURE_OPENAI_API_KEY"
        )

        # 임베딩(text-embedding-3-small)
        self.azure_openai_embedding_deployment: str = os.getenv(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"
        )
        self.azure_openai_embedding_api_version: str = os.getenv(
            "AZURE_OPENAI_EMBEDDING_API_VERSION", "2023-05-15"
        )

        # 채팅/매칭 설명(gpt-4o-mini)
        self.azure_openai_chat_deployment: str = os.getenv(
            "AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini"
        )
        self.azure_openai_chat_api_version: str = os.getenv(
            "AZURE_OPENAI_CHAT_API_VERSION", "2025-01-01-preview"
        )

    @property
    def is_prod(self) -> bool:
        return self.env.lower() == "prod"

    @property
    def is_dev(self) -> bool:
        return self.env.lower() == "dev"


@lru_cache()
def get_settings() -> Settings:
    """
    Settings 싱글톤.
    - import 후 어디서든 get_settings() 호출해서 재사용.
    """
    return Settings()
