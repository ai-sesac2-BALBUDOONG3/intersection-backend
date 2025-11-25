# app/services/azure_openai.py

from __future__ import annotations

from typing import List, Optional

from app.core.config import settings

try:
    from openai import AzureOpenAI  # openai==1.x
except ImportError:  # openai 패키지 없으면 None
    AzureOpenAI = None  # type: ignore[assignment]


def _has_common_config() -> bool:
    return bool(
        settings.azure_openai_endpoint
        and settings.azure_openai_api_key
    )


def _get_embeddings_client() -> Optional["AzureOpenAI"]:
    """
    임베딩용 클라이언트(text-embedding-3-small, 2023-05-15)
    """
    if AzureOpenAI is None:
        return None
    if not _has_common_config():
        return None
    if not settings.azure_openai_embedding_deployment:
        return None

    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_embedding_api_version,
    )


def _get_chat_client() -> Optional["AzureOpenAI"]:
    """
    채팅/설명용 클라이언트(gpt-4o-mini, 2025-01-01-preview)
    """
    if AzureOpenAI is None:
        return None
    if not _has_common_config():
        return None
    if not settings.azure_openai_chat_deployment:
        return None

    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_chat_api_version,
    )


def get_embedding(text: str) -> Optional[List[float]]:
    """
    텍스트를 Azure OpenAI 임베딩 벡터로 변환.
    - 설정/패키지/디플로이 없으면 None 반환.
    """
    client = _get_embeddings_client()
    if client is None:
        print("[AzureOpenAI] Embedding 호출 불가: 설정 또는 패키지/디플로이 없음")
        return None

    response = client.embeddings.create(
        input=text,
        model=settings.azure_openai_embedding_deployment,  # type: ignore[arg-type]
    )
    return response.data[0].embedding  # type: ignore[no-any-return]


def chat_completion(system_prompt: str, user_content: str) -> Optional[str]:
    """
    간단한 ChatCompletion 헬퍼.
    - 설정/패키지/디플로이 없으면 None 반환.
    """
    client = _get_chat_client()
    if client is None:
        print("[AzureOpenAI] Chat 호출 불가: 설정 또는 패키지/디플로이 없음")
        return None

    response = client.chat.completions.create(
        model=settings.azure_openai_chat_deployment,  # type: ignore[arg-type]
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        max_tokens=256,
        temperature=0.3,
    )

    content = response.choices[0].message.content or ""
    return content.strip()
