# path: ai_service.py
"""
Azure OpenAI 기반 임베딩 / 매칭 설명 서비스 레이어

- get_text_embedding(text): str -> list[float]
- build_match_explanation(...): 매칭 결과 설명 문장 생성

콘텐츠 안전 필터(check_text_safety)는 사용하지 않습니다.
"""

import os
from typing import List, Sequence, Optional

from dotenv import load_dotenv
from openai import AzureOpenAI

# ===========================
# 환경 변수 로드
# ===========================
load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
AZURE_OPENAI_EMBED_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

_AZURE_ENABLED = bool(
    AZURE_OPENAI_ENDPOINT
    and AZURE_OPENAI_API_KEY
    and AZURE_OPENAI_EMBED_DEPLOYMENT
    and AZURE_OPENAI_CHAT_DEPLOYMENT
)

_client: Optional[AzureOpenAI] = None
if _AZURE_ENABLED:
    _client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
    )


# ===========================
# 내부 헬퍼
# ===========================

def _ensure_client() -> AzureOpenAI:
    if _client is None:
        raise RuntimeError(
            "Azure OpenAI 클라이언트가 초기화되지 않았습니다. "
            "AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY / "
            "AZURE_OPENAI_EMBED_DEPLOYMENT / AZURE_OPENAI_CHAT_DEPLOYMENT "
            "환경변수를 확인하세요."
        )
    return _client


# ===========================
# 1) 임베딩 함수
# ===========================

def get_text_embedding(text: str) -> List[float]:
    """
    단일 텍스트를 임베딩 벡터(list[float])로 변환.
    - 모델: .env의 AZURE_OPENAI_EMBED_DEPLOYMENT
    """
    if not text or not text.strip():
        raise ValueError("임베딩을 생성할 text가 비어 있습니다.")

    client = _ensure_client()
    resp = client.embeddings.create(
        model=AZURE_OPENAI_EMBED_DEPLOYMENT,
        input=text,
    )
    embedding = resp.data[0].embedding
    return embedding


# ===========================
# 2) 설명 LLM: 매칭 결과 설명
# ===========================

def build_match_explanation(
    me_nickname: str,
    candidate_nickname: str,
    overlap_fragments: Sequence[str],
    extra_hint: Optional[str] = None,
    max_tokens: int = 256,
) -> str:
    """
    기억 교집합(같은 학교/시기/지역/별명 등) 리스트를 받아,
    사용자에게 보여줄 자연어 설명 문장을 생성.

    - overlap_fragments 예:
        [
            "초등학교 4~6학년 때 같은 학교(서울 강동초등학교)",
            "둘 다 강동구 성내동 근처 거주",
            "동아리 '대진' 같이 활동",
        ]
    """
    client = _ensure_client()

    if overlap_fragments:
        bullet = "\n".join(f"- {frag}" for frag in overlap_fragments)
        overlap_text = (
            "다음과 같은 기억의 교집합이 발견되었습니다:\n"
            f"{bullet}"
        )
    else:
        overlap_text = (
            "명시적인 교집합은 드러나지 않았지만, "
            "여러 조건을 종합해 추천된 친구입니다."
        )

    system_prompt = (
        "당신은 기억 교집합 기반 친구 추천 앱 'Humane / Intersection'의 설명 생성기입니다. "
        "추천된 친구 후보에 대해, 왜 추천되었는지 사용자가 이해하기 쉬운 자연어로 "
        "2~4문장 정도로 설명해 주세요. 톤은 따뜻하고 과장되지 않게, 존댓말을 사용합니다."
    )

    user_prompt = (
        f"나의 닉네임: {me_nickname}\n"
        f"추천된 친구 후보의 닉네임: {candidate_nickname}\n\n"
        f"{overlap_text}\n"
    )

    if extra_hint:
        user_prompt += f"\n추가 힌트:\n- {extra_hint}\n"

    resp = client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=max_tokens,
    )

    content = resp.choices[0].message.content or ""
    return content.strip()
