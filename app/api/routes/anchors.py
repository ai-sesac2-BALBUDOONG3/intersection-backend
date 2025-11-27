# app/api/routes/anchors.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.anchor import AnchorCreate, AnchorRead
from app.services.embedding_service import refresh_anchor_embedding

router = APIRouter(prefix="/anchors", tags=["anchors"])


@router.post(
    "",
    response_model=AnchorRead,
    status_code=status.HTTP_201_CREATED,
    summary="대표 학교/기억 앵커 생성 + 임베딩 생성",
)
def create_anchor(
    payload: AnchorCreate,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> AnchorRead:
    """
    현재 로그인한 유저 기준으로 user_school_anchors에 레코드를 하나 생성하고,
    바로 Azure OpenAI(text-embedding-3-small)를 사용해 anchor_embedding 을 채운다.

    - DB 테이블: user_school_anchors
    - 임베딩 컬럼: anchor_embedding (numeric[])
    """
    if not payload.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="title은 반드시 1글자 이상이어야 합니다.",
        )

    # 1) 앵커 INSERT (anchor_embedding 은 NULL 상태로 먼저 생성)
    insert_sql = text(
        """
        INSERT INTO user_school_anchors (
            user_id,
            institution_id,
            title,
            description,
            time_start_year,
            time_end_year,
            region_city,
            region_district
        )
        VALUES (
            :user_id,
            :institution_id,
            :title,
            :description,
            :time_start_year,
            :time_end_year,
            :region_city,
            :region_district
        )
        RETURNING
            id,
            user_id,
            institution_id,
            title,
            description,
            time_start_year,
            time_end_year,
            region_city,
            region_district,
            anchor_embedding
        """
    )

    row = db.execute(
        insert_sql,
        {
            "user_id": current_user.id,
            "institution_id": payload.institution_id,
            "title": payload.title.strip(),
            "description": (payload.description or "").strip() or None,
            "time_start_year": payload.time_start_year,
            "time_end_year": payload.time_end_year,
            "region_city": (payload.region_city or "").strip() or None,
            "region_district": (payload.region_district or "").strip() or None,
        },
    ).mappings().first()

    db.commit()  # INSERT 확정 (임베딩 생성 전에 커밋)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="앵커 생성에 실패했습니다.",
        )

    anchor_id = row["id"]

    # 2) Azure OpenAI 임베딩 생성 & 저장
    #    - title + description 기반으로 anchor_embedding 채움
    embedding_ok = False
    try:
        embedding_ok = refresh_anchor_embedding(db=db, anchor_id=anchor_id)
    except Exception:
        # 임베딩 실패해도 앵커 생성 자체는 성공이므로 201은 그대로 반환
        embedding_ok = False

    return AnchorRead(
        id=anchor_id,
        institution_id=row["institution_id"],
        title=row["title"],
        description=row["description"],
        time_start_year=row["time_start_year"],
        time_end_year=row["time_end_year"],
        region_city=row["region_city"],
        region_district=row["region_district"],
        has_embedding=embedding_ok,
    )


@router.get(
    "/me",
    response_model=List[AnchorRead],
    summary="내 대표 앵커 목록 조회",
)
def list_my_anchors(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> List[AnchorRead]:
    """
    현재 로그인한 유저의 user_school_anchors 목록을 반환한다.
    - soft delete 된(is_deleted = true) 행은 제외
    """
    rows = db.execute(
        text(
            """
            SELECT
                id,
                institution_id,
                title,
                description,
                time_start_year,
                time_end_year,
                region_city,
                region_district,
                (anchor_embedding IS NOT NULL) AS has_embedding
            FROM user_school_anchors
            WHERE user_id = :user_id
              AND is_deleted = false
            ORDER BY created_at DESC
            """
        ),
        {"user_id": current_user.id},
    ).mappings().all()

    return [
        AnchorRead(
            id=row["id"],
            institution_id=row["institution_id"],
            title=row["title"],
            description=row["description"],
            time_start_year=row["time_start_year"],
            time_end_year=row["time_end_year"],
            region_city=row["region_city"],
            region_district=row["region_district"],
            has_embedding=bool(row["has_embedding"]),
        )
        for row in rows
    ]
