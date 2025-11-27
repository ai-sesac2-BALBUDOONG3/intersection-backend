# app/services/embedding_service.py

"""
Embedding service for Intersection.

- Uses Azure OpenAI text-embedding-3-small deployment
- Stores embeddings into PostgreSQL `user_school_anchors.anchor_embedding` (numeric[])

Environment variables (already aligned with your .env / App Service settings):

    AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_API_KEY
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT      # e.g. "text-embedding-3-small"
    AZURE_OPENAI_EMBEDDING_API_VERSION     # e.g. "2023-05-15"

DB schema (as of intersection_db.user_school_anchors):

    id                     BIGINT    PK
    user_id                BIGINT
    institution_id         BIGINT
    title                  TEXT      -- 앵커 제목(필수, 사람이 보는 문장)
    description            TEXT      -- 선택 설명 텍스트
    region_city            TEXT
    region_district        TEXT
    anchor_embedding       NUMERIC[] -- 임베딩 벡터 저장 컬럼
    anchor_embedding_model TEXT      -- 어떤 모델로 생성했는지
    anchor_embedding_at    TIMESTAMPTZ -- 생성 시각
    is_deleted             BOOLEAN
    created_at             TIMESTAMPTZ
    updated_at             TIMESTAMPTZ
"""

import os
from typing import Dict, List, Sequence

from openai import AzureOpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session


def _get_azure_embedding_client() -> AzureOpenAI:
    """
    Azure OpenAI 임베딩 클라이언트 생성.

    반드시 아래 환경변수가 설정되어 있어야 한다.
      - AZURE_OPENAI_ENDPOINT
      - AZURE_OPENAI_API_KEY
      - AZURE_OPENAI_EMBEDDING_API_VERSION (없으면 기본값 사용)
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION", "2023-05-15")

    if not endpoint or not api_key:
        raise RuntimeError(
            "Azure OpenAI embedding 환경변수(AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY)가 설정되어 있지 않습니다."
        )

    return AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=endpoint,
    )


def _get_embedding_deployment_name() -> str:
    """
    사용할 임베딩 모델 배포 이름.
    .env / App Service 환경변수에서 우선 읽고, 없으면 text-embedding-3-small 사용.
    """
    return os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")


def _build_anchor_text(title: str | None, description: str | None) -> str:
    """
    앵커용 텍스트 생성 로직.

    - title 은 NOT NULL 이라고 가정하지만, 방어적으로 처리
    - description 이 있으면 "title - description" 형태로 결합
    """
    t = (title or "").strip()
    d = (description or "").strip()

    if t and d:
        return f"{t} - {d}"
    return t or d  # 둘 중 하나라도 있으면 그 값 사용


def embed_texts(
    client: AzureOpenAI,
    texts: Sequence[str],
) -> List[List[float]]:
    """
    여러 텍스트에 대해 임베딩을 생성하고, 각 텍스트에 대한 벡터 리스트를 반환.

    - 빈 문자열/공백만 있는 텍스트는 호출 전 필터링해서 보내는 것을 권장.
    """
    if not texts:
        return []

    deployment = _get_embedding_deployment_name()

    response = client.embeddings.create(
        model=deployment,
        input=list(texts),
    )

    # response.data[i].embedding -> List[float]
    vectors: List[List[float]] = [d.embedding for d in response.data]
    if len(vectors) != len(texts):
        raise RuntimeError(
            f"임베딩 개수 불일치: 입력 {len(texts)}개, 결과 {len(vectors)}개"
        )

    return vectors


def refresh_anchor_embedding(
    db: Session,
    anchor_id: int,
    client: AzureOpenAI | None = None,
) -> bool:
    """
    특정 user_school_anchors.id에 대해 title/description을 읽어서
    Azure OpenAI 임베딩을 생성하고 anchor_embedding(numeric[]) 컬럼을 업데이트.

    반환값:
        True  -> 성공적으로 업데이트됨
        False -> anchor를 찾지 못했거나 텍스트가 비어있는 경우
    """
    row = db.execute(
        text(
            """
            SELECT id, title, description, is_deleted
            FROM user_school_anchors
            WHERE id = :anchor_id
            """
        ),
        {"anchor_id": anchor_id},
    ).mappings().first()

    if not row:
        return False

    if row.get("is_deleted"):
        # 삭제된 앵커는 스킵
        return False

    anchor_text = _build_anchor_text(row["title"], row["description"]).strip()
    if not anchor_text:
        # 텍스트가 없으면 임베딩 생성 불가
        return False

    close_client = False
    if client is None:
        client = _get_azure_embedding_client()
        close_client = True  # 현재는 AzureOpenAI에 별 close는 없지만, 향후를 대비한 플래그

    try:
        vectors = embed_texts(client, [anchor_text])
        embedding = vectors[0]
    finally:
        # 현재 AzureOpenAI는 별도 close 불필요
        if close_client:
            pass

    model_name = _get_embedding_deployment_name()

    # numeric[] 컬럼에 Python list[float]를 그대로 넣으면 psycopg2가 자동 변환
    db.execute(
        text(
            """
            UPDATE user_school_anchors
            SET anchor_embedding = :embedding,
                anchor_embedding_model = :model_name,
                anchor_embedding_at = NOW()
            WHERE id = :anchor_id
            """
        ),
        {
            "embedding": embedding,
            "model_name": model_name,
            "anchor_id": anchor_id,
        },
    )
    db.commit()
    return True


def rebuild_missing_anchor_embeddings(
    db: Session,
    batch_size: int = 100,
) -> Dict[str, int]:
    """
    anchor_embedding 이 비어있는 user_school_anchors 레코드들을 대상으로
    batch 단위로 임베딩을 생성/저장.

    대상 조건:
        - is_deleted = false
        - title IS NOT NULL
        - anchor_embedding IS NULL

    batch_size: 한 번에 불러와서 처리할 행 개수 (기본 100)

    반환값 예시:
        {
            "processed": 120,
            "succeeded": 118,
            "failed": 2,
        }
    """
    stats: Dict[str, int] = {
        "processed": 0,
        "succeeded": 0,
        "failed": 0,
    }

    client = _get_azure_embedding_client()
    deployment = _get_embedding_deployment_name()

    while True:
        rows = db.execute(
            text(
                """
                SELECT id, title, description
                FROM user_school_anchors
                WHERE is_deleted = false
                  AND title IS NOT NULL
                  AND anchor_embedding IS NULL
                ORDER BY id
                LIMIT :limit
                """
            ),
            {"limit": batch_size},
        ).mappings().all()

        if not rows:
            break  # 더 이상 처리할 대상 없음

        # 유효한 텍스트만 모아서 한 번에 임베딩 호출
        anchor_ids: List[int] = []
        texts: List[str] = []

        for row in rows:
            anchor_text = _build_anchor_text(row["title"], row["description"]).strip()
            if not anchor_text:
                # 비어있는 텍스트는 스킵
                stats["processed"] += 1
                stats["failed"] += 1
                continue

            anchor_ids.append(row["id"])
            texts.append(anchor_text)

        if not anchor_ids:
            # 이번 배치에 유효한 텍스트가 하나도 없으면 다음 루프로
            continue

        stats["processed"] += len(anchor_ids)

        # 임베딩 생성
        try:
            response = client.embeddings.create(
                model=deployment,
                input=texts,
            )
            vectors: List[List[float]] = [d.embedding for d in response.data]
            if len(vectors) != len(anchor_ids):
                raise RuntimeError(
                    f"임베딩 개수 불일치: anchor_ids={len(anchor_ids)}, vectors={len(vectors)}"
                )
        except Exception:
            # 이 배치 전체 실패로 처리
            stats["failed"] += len(anchor_ids)
            db.rollback()
            # 치명적 에러로 판단하고 루프 종료 (원하면 계속 진행하도록 변경 가능)
            break

        # DB 업데이트
        try:
            for anchor_id, embedding in zip(anchor_ids, vectors):
                try:
                    db.execute(
                        text(
                            """
                            UPDATE user_school_anchors
                            SET anchor_embedding = :embedding,
                                anchor_embedding_model = :model_name,
                                anchor_embedding_at = NOW()
                            WHERE id = :anchor_id
                            """
                        ),
                        {
                            "embedding": embedding,
                            "model_name": deployment,
                            "anchor_id": anchor_id,
                        },
                    )
                    stats["succeeded"] += 1
                except Exception:
                    stats["failed"] += 1
            db.commit()
        except Exception:
            # 커밋 단계에서 실패하면 해당 배치 전체를 실패로 처리
            db.rollback()
            stats["failed"] += len(anchor_ids)

    return stats
