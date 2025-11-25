# app/core/config.py

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ===== 환경 =====
    env: str = Field("dev", alias="ENV")

    # ===== 보안 =====
    secret_key: str = Field(..., alias="SECRET_KEY")

    # ===== DB 설정 =====
    # 1순위: DATABASE_URL
    database_url: Optional[str] = Field(
        default=None,
        alias="DATABASE_URL",
    )

    # 2순위: 개별 항목(DB_HOST 등) 조합
    db_host: Optional[str] = Field(default=None, alias="DB_HOST")
    db_port: int = Field(5432, alias="DB_PORT")
    db_name: Optional[str] = Field(default=None, alias="DB_NAME")
    db_user: Optional[str] = Field(default=None, alias="DB_USER")
    db_password: Optional[str] = Field(default=None, alias="DB_PASSWORD")

    # ===== Azure OpenAI 설정 =====
    azure_openai_endpoint: str | None = Field(
        default=None,
        alias="AZURE_OPENAI_ENDPOINT",
    )
    azure_openai_api_key: str | None = Field(
        default=None,
        alias="AZURE_OPENAI_API_KEY",
    )

    # 임베딩용(text-embedding-3-small)
    azure_openai_embedding_deployment: str | None = Field(
        default=None,
        alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    )
    azure_openai_embedding_api_version: str = Field(
        default="2023-05-15",
        alias="AZURE_OPENAI_EMBEDDING_API_VERSION",
    )

    # 채팅용(gpt-4o-mini)
    azure_openai_chat_deployment: str | None = Field(
        default=None,
        alias="AZURE_OPENAI_CHAT_DEPLOYMENT",
    )
    azure_openai_chat_api_version: str = Field(
        default="2025-01-01-preview",
        alias="AZURE_OPENAI_CHAT_API_VERSION",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @property
    def sqlalchemy_database_uri(self) -> str:
        """
        FastAPI / SQLAlchemy에서 사용할 PostgreSQL 접속 URI.
        1순위: DATABASE_URL
        2순위: DB_HOST/DB_NAME/DB_USER/DB_PASSWORD 조합
        """
        if self.database_url:
            return self.database_url

        if not (self.db_host and self.db_name and self.db_user and self.db_password):
            raise ValueError(
                "DB 설정이 부족합니다. DATABASE_URL 또는 "
                "DB_HOST/DB_NAME/DB_USER/DB_PASSWORD를 설정하세요."
            )

        from urllib.parse import quote_plus

        password_quoted = quote_plus(self.db_password)
        return (
            f"postgresql+psycopg2://{self.db_user}:{password_quoted}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?sslmode=require"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
