# app/services/matching_explanation.py

from typing import Optional

from app.services.azure_openai import chat_completion


def build_explanation_with_fallback(
    base_school_name: str,
    base_year_range: str,
    cand_nickname: str,
    cand_school_name: str,
    cand_year_range: str,
) -> str:
    """
    Azure OpenAI가 설정되어 있으면 GPT로 설명을 만들고,
    아니면 기본 문장으로 대체.
    """
    system_prompt = (
        "당신은 사람 매칭 서비스의 설명 문구를 작성하는 어시스턴트입니다. "
        "두 사람이 같은 학교/비슷한 시기에 다녔다는 정보로, "
        "부드럽고 짧은 한국어 한 문장으로 '왜 매칭되었는지' 설명해 주세요. "
        "과장은 하지 말고, 존댓말로 작성하세요."
    )

    user_content = (
        f"기준 사용자: {base_school_name} {base_year_range} 재학.\n"
        f"후보 사용자({cand_nickname}): {cand_school_name} {cand_year_range} 재학.\n"
        "두 사람이 왜 매칭 후보가 되었는지 한 줄로 설명해 주세요."
    )

    ai_result: Optional[str] = chat_completion(system_prompt, user_content)

    if ai_result:
        return ai_result

    # Fallback 기본 문장
    if base_school_name == cand_school_name:
        return (
            f"두 분 모두 {base_school_name}에서 비슷한 시기에 "
            f"다니셨던 것으로 보여 함께 기억을 나누기 좋은 인연일 수 있어요."
        )
    else:
        return (
            f"{cand_nickname}님은 비슷한 시기의 인근 학교를 다니신 분으로, "
            f"당시의 추억을 공유하기 좋은 후보로 보여요."
        )
