# app/services/matching_explanation.py
import json
import os
from typing import Dict, List

from openai import AzureOpenAI
from pydantic import BaseModel

from app.schemas.matching import MatchRecommendation


class SimpleUserContext(BaseModel):
    id: int
    nickname: str


def _get_azure_client() -> AzureOpenAI:
    """
    Azure OpenAI 클라이언트 생성.
    .env에서 아래 환경변수 사용:
      - AZURE_OPENAI_ENDPOINT
      - AZURE_OPENAI_API_KEY
      - AZURE_OPENAI_CHAT_API_VERSION (없으면 기본값 사용)
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    # 사용자가 .env에 이미 설정해둔 값을 우선 사용
    api_version = os.getenv("AZURE_OPENAI_CHAT_API_VERSION", "2025-01-01-preview")

    if not endpoint or not api_key:
        raise RuntimeError(
            "AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다."
        )

    return AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=endpoint,
    )


def generate_match_reasons(
    current_user: SimpleUserContext,
    candidates: List[MatchRecommendation],
) -> Dict[int, str]:
    """
    gpt-4o-mini를 사용해 각 후보별 추천 이유 한 줄 생성.
    반환값: {candidate_user_id: reason_ko}
    """
    if not candidates:
        return {}

    client = _get_azure_client()
    # .env에 이미 있는 값과 맞춤
    deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")

    # 프롬프트에 넘길 최소 정보만 구성
    payload = {
        "current_user": current_user.model_dump(),
        "candidates": [
            {
                "candidate_user_id": c.candidate_user_id,
                "nickname": c.nickname,
                "scores": c.scores.model_dump(),
            }
            for c in candidates
        ],
    }

    system_prompt = (
        "너는 기억 교집합 기반 친구찾기 앱 'Intersection'의 추천 이유를 만들어주는 카피라이터야.\n"
        "응답은 반드시 JSON 형식의 리스트로만 반환해야 한다.\n"
        "각 원소는 {\"candidate_user_id\": number, \"reason\": string} 형식이다.\n"
        "reason은 한국어 한 문장, 40자 이내로 따뜻하고 구체적으로 작성해라.\n"
        "점수가 높은 요소(학교, 지역, 연도, 키워드)를 위주로 설명하되 점수 숫자는 노출하지 않는다."
    )

    user_prompt = (
        "아래 current_user와 후보자 리스트, 점수 정보를 보고,\n"
        "각 후보자별로 한 줄짜리 추천 이유를 만들어줘.\n"
        "JSON 외의 다른 텍스트는 절대 포함하지 말 것.\n\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.6,
        max_tokens=512,
    )

    content = response.choices[0].message.content.strip()

    reasons: Dict[int, str] = {}

    try:
        data = json.loads(content)
        if isinstance(data, list):
            for item in data:
                cid = item.get("candidate_user_id")
                reason = item.get("reason")
                if isinstance(cid, int) and isinstance(reason, str):
                    reasons[cid] = reason.strip()
    except json.JSONDecodeError:
        # 파싱 실패 시, fallback: 공통 멘트
        for c in candidates:
            reasons[c.candidate_user_id] = (
                "같은 시기와 비슷한 학교/지역에서 생활했던 인연일 가능성이 높아요."
            )

    return reasons
