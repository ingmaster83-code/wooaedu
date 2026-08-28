#!/usr/bin/env python3
"""
fetch_courses.py - 전국평생학습강좌표준데이터 수집

주의: 이 사이트는 '강좌 검색' 서비스가 아니다(국가평생학습포털 '늘배움'이 이미
이 데이터로 16만 개 규모의 공식 강좌검색 서비스를 운영 중이라 정면 경쟁을 피함).
여기서는 지역 페이지에 "이 지역 평생학습 강좌 N개 모집 중" 같은 보조 정보를
보여주기 위한 용도로만 사용한다 (시군구별 집계 + 상위 몇 개 미리보기).

사용법:
  python scripts/fetch_courses.py
"""
import sys, json, time
from pathlib import Path
import requests

sys.stdout.reconfigure(encoding="utf-8")

PUBLIC_DATA_PK = "15013110"
SVC_TABLE = "tn_pubr_public_lftm_lrn_lctre_svc"
COLUMNS = [
    "LCTRE_NM", "INSTRCTR_NM", "EDC_START_DAY", "EDC_END_DAY",
    "EDC_START_TIME", "EDC_COLSE_TIME", "LCTRE_CO", "EDC_TRGET_TYPE",
    "EDC_MTH_TYPE", "OPER_DAY", "EDC_PLACE", "PSNCPA", "LCTRE_COST",
    "EDC_RDNMADR", "OPER_INSTITUTION_NM", "OPER_PHONE_NUMBER",
    "RCEPT_START_DATE", "RCEPT_END_DATE", "RCEPT_MTH_TYPE",
    "SLCTN_MTH_TYPE", "HOMEPAGE_URL", "REFERENCE_DATE",
]
OUT_FILE = Path(__file__).parent.parent / "_rawdata" / "courses_raw.json"
PER_PAGE = 10000


def fetch_page(page: int) -> list:
    params = [("publicDataPk", PUBLIC_DATA_PK)]
    params += [("colNmList", c) for c in COLUMNS]
    params += [
        ("totalCount", "999999"),
        ("svcTableNm", SVC_TABLE),
        ("perPage", str(PER_PAGE)),
        ("page", str(page)),
    ]
    resp = requests.get(
        "https://www.data.go.kr/download/standard.json",
        params=params, timeout=60,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        return []
    return data


def main():
    print("=== 전국평생학습강좌표준데이터 수집 시작 (지역 집계용) ===")
    all_items = []
    page = 1
    while True:
        items = fetch_page(page)
        if not items:
            break
        all_items.extend(items)
        print(f"  페이지 {page}: {len(items)}개 (누적 {len(all_items)})")
        if len(items) < PER_PAGE:
            break
        page += 1
        time.sleep(0.3)

    if not all_items:
        raise SystemExit("수집된 데이터가 없습니다.")

    if OUT_FILE.exists():
        existing = json.loads(OUT_FILE.read_text(encoding="utf-8"))
        if len(all_items) < len(existing) * 0.5:
            raise SystemExit(
                f"수집 건수({len(all_items)}건)가 기존 데이터({len(existing)}건)의 절반 미만입니다. "
                "오류로 판단하여 저장을 중단합니다."
            )

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(all_items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n완료: {OUT_FILE}")
    print(f"  총 {len(all_items)}개 강좌 저장")


if __name__ == "__main__":
    main()
