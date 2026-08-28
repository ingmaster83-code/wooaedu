#!/usr/bin/env python3
"""
fetch_facilities.py - 전국평생교육시설정보표준데이터 수집

data.go.kr의 legacy openAPI(api.data.go.kr)는 GitHub Actions 러너 IP에서 403이 나는
사례가 반복 확인되어(다른 wooahouse 사이트들 참고), 인증키가 필요없는 표준데이터셋
직접다운로드 엔드포인트(www.data.go.kr/download/standard.json)를 사용한다.

사용법:
  python scripts/fetch_facilities.py
"""
import sys, json, time
from pathlib import Path
import requests

sys.stdout.reconfigure(encoding="utf-8")

PUBLIC_DATA_PK = "15107727"
SVC_TABLE = "tn_pubr_public_lftm_lrn_fclty_svc"
COLUMNS = [
    "FLCT_SE_NM", "FLCT_NM", "CTPV_ED_CD", "CTPV_ED_NM", "ED_CD", "ED_NM",
    "CTPV_CD", "CTPV_NM", "SGG_CD", "SGG_NM", "LCTN_ROAD_NM_ADDR",
    "LCTN_LOTNO_ADDR", "FNDR_NM", "TELNO", "REG_YMD", "REG_STTS_SE_NM",
    "ACBG_RECOGN_YN", "ACBG_RECOGN_YR", "HMPG_ADDR", "CRTR_YMD",
]
OUT_FILE = Path(__file__).parent.parent / "_rawdata" / "facilities_raw.json"
PER_PAGE = 10000


def fetch_page(page: int) -> list:
    params = [("publicDataPk", PUBLIC_DATA_PK)]
    params += [("colNmList", c) for c in COLUMNS]
    params += [
        ("totalCount", "99999"),
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
        # 오류 응답(예: totalCount 불일치)은 dict로 옴
        return []
    return data


def main():
    print("=== 전국평생교육시설정보표준데이터 수집 시작 ===")
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
        raise SystemExit("수집된 데이터가 없습니다. URL/파라미터를 확인하세요.")

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
    print(f"  총 {len(all_items)}개 시설 저장")


if __name__ == "__main__":
    main()
