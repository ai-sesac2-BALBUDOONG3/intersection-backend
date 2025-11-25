# app/services/ai_service.py
from __future__ import annotations

from typing import List

from openai import OpenAI
from app.core.config import get_settings

settings = get_settings()


def _get_embed_client() -> OpenAI:
    if not (settings.AZURE_OPENAI_EMBED_ENDPOINT and settings.AZURE_OPENAI_EMBED_API_KEY and settings.AZURE_OPENAI_EMBED_DEPLOYMENT):
        raise RuntimeError("임베딩용 Azure OpenAI 설정이 누락되었습니다.")
    return OpenAI(
        api_key=settings.AZURE_OPENAI_EMBED_API_KEY,
        base_url=f"{settings.AZURE_OPENAI_EMBED_ENDPOINT}/openai",
    )


def _get_chat_client() -> OpenAI:
    if not (settings.AZURE_OPENAI_CHAT_ENDPOINT and settings.AZURE_OPENAI_CHAT_API_KEY and settings.AZURE_OPENAI_CHAT_DEPLOYMENT):
        raise RuntimeError("챗용 Azure OpenAI 설정이 누락되었습니다.")
    return OpenAI(
        api_key=settings.AZURE_OPENAI_CHAT_API_KEY,
        base_url=f"{settings.AZURE_OPENAI_CHAT_ENDPOINT}/openai",
    )


def embed_texts(texts: List[str]) -> List[List[float]]:
    client = _get_embed_client()
    resp = client.embeddings.create(
        input=texts,
        model=settings.AZURE_OPENAI_EMBED_DEPLOYMENT,
    )
    return [item.embedding for item in resp.data]


def embed_text(text: str) -> List[float]:
    return embed_texts([text])[0]


def generate_match_explanation(
    base_user_nickname: str,
    candidate_nickname: str,
    institution_name: str | None,
    period_str: str | None,
    region_str: str | None,
) -> str:
    client = _get_chat_client()

    details = []
    if institution_name:
        details.append(f"학교/기관: {institution_name}")
    if period_str:
        details.append(f"시기: {period_str}")
    if region_str:
        details.append(f"지역: {region_str}")

    detail_str = "\n".join(details)

    prompt = f"""
당신은 기억 기반 친구 매칭 앱 'Intersection'의 매칭 설명 도우미입니다.

사용자 '{base_user_nickname}'와(과) 후보 '{candidate_nickname}' 간의 매칭 근거를
아래 정보에 기반하여 한국어로 2~3문장 정도로 부드럽고 조심스러운 톤으로 설명해주세요.

매칭 근거:
{detail_str}
"""

    resp = client.chat.completions.create(
        model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "당신은 배려 깊은 매칭 설명 도우미입니다."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
        max_tokens=200,
    )

    return resp.choices[0].message.content.strip()
