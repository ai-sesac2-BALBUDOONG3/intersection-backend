# path: seed_institutions.py
"""
기관(학교) 기본 데이터 시드 스크립트.

- 대상 DB: Azure Cosmos DB for PostgreSQL (Citus) - .env 설정 기반
- 역할:
    1) institutions 테이블의 기존 데이터를 모두 삭제
    2) SEED_INSTITUTIONS 에 정의된 학교/기관 데이터를 insert

⚠️ 주의
- 이 스크립트는 "개발/스테이징용 코드북" 역할을 전제로 합니다.
- 실행 시 institutions 테이블의 모든 데이터를 삭제하므로,
  운영 환경에서는 그대로 사용하지 말고 NEIS 연동 스크립트로 교체하거나
  DELETE 대신 UPSERT 방식으로 변경하는 것을 권장합니다.
"""

from __future__ import annotations

from typing import List, Dict

from sqlalchemy.orm import Session

from database import SessionLocal
from models import Institution


# ---------------------------------------------------------------------------
# 1. 시드 데이터 정의
#    - 실제 NEIS 연동 전까지 개발/테스트에서 사용할 최소 학교 목록
#    - 나중에 NEIS 연동 시, 이 구조를 CSV/NEIS API 기반으로 확장 가능
# ---------------------------------------------------------------------------

SEED_INSTITUTIONS: List[Dict[str, str]] = [
    # 서울 강동구 인근
    {
        "name": "서울강동초등학교",
        "region_city": "서울특별시",
        "region_district": "강동구",
        "address": "서울특별시 강동구 천호대로 123",
    },
    {
        "name": "서울둔촌초등학교",
        "region_city": "서울특별시",
        "region_district": "강동구",
        "address": "서울특별시 강동구 올림픽로 456",
    },
    {
        "name": "서울천호초등학교",
        "region_city": "서울특별시",
        "region_district": "강동구",
        "address": "서울특별시 강동구 천중로 78",
    },
    # 서울 송파/강남
    {
        "name": "서울잠실초등학교",
        "region_city": "서울특별시",
        "region_district": "송파구",
        "address": "서울특별시 송파구 올림픽로 15",
    },
    {
        "name": "서울잠신초등학교",
        "region_city": "서울특별시",
        "region_district": "송파구",
        "address": "서울특별시 송파구 백제고분로 210",
    },
    {
        "name": "서울대치초등학교",
        "region_city": "서울특별시",
        "region_district": "강남구",
        "address": "서울특별시 강남구 역삼로 321",
    },
    {
        "name": "서울역삼초등학교",
        "region_city": "서울특별시",
        "region_district": "강남구",
        "address": "서울특별시 강남구 테헤란로 98",
    },
    # 부산
    {
        "name": "부산남천초등학교",
        "region_city": "부산광역시",
        "region_district": "수영구",
        "address": "부산광역시 수영구 남천동로 12",
    },
    {
        "name": "부산해운대초등학교",
        "region_city": "부산광역시",
        "region_district": "해운대구",
        "address": "부산광역시 해운대구 해운대로 456",
    },
    {
        "name": "부산광안초등학교",
        "region_city": "부산광역시",
        "region_district": "수영구",
        "address": "부산광역시 수영구 광안해변로 78",
    },
]


# ---------------------------------------------------------------------------
# 2. 시드 로직
# ---------------------------------------------------------------------------


def reset_and_seed_institutions(db: Session) -> None:
    """
    institutions 테이블을 초기화하고 SEED_INSTITUTIONS 데이터로 재생성.

    - 1) 기존 데이터 전체 삭제
    - 2) SEED_INSTITUTIONS 를 기반으로 bulk insert
    """
    # 1) 기존 데이터 전체 삭제
    deleted = db.query(Institution).delete(synchronize_session=False)
    print(f"[seed_institutions] 기존 institutions 레코드 {deleted}건 삭제")

    # 2) 새 데이터 삽입
    #    - Institution 모델에 다른 NOT NULL 컬럼이 있더라도
    #      서버 DEFAULT 가 설정되어 있다면, 아래 4개 컬럼만 채워도 동작함
    db.bulk_insert_mappings(Institution, SEED_INSTITUTIONS)
    print(f"[seed_institutions] 새 institutions 레코드 {len(SEED_INSTITUTIONS)}건 삽입")

    db.commit()
    print("[seed_institutions] 커밋 완료")


def main() -> None:
    """
    스크립트 진입점.
    """
    db: Session | None = None
    try:
        db = SessionLocal()
        reset_and_seed_institutions(db)
    except Exception as e:
        # 문제가 생기면 롤백 후 예외 출력
        if db is not None:
            db.rollback()
        print("[seed_institutions] 오류 발생:", repr(e))
        raise
    finally:
        if db is not None:
            db.close()
        print("[seed_institutions] DB 세션 종료")


if __name__ == "__main__":
    main()
