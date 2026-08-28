#!/usr/bin/env python3
"""
process_data.py - 원본 데이터를 Jekyll 페이지 생성용 JSON으로 가공

입력: _rawdata/facilities_raw.json, _rawdata/courses_raw.json
출력: _rawdata/facilities.json (시설 목록), _rawdata/region_courses.json (지역별 강좌 집계)

사용법:
  python scripts/process_data.py
"""
import json, re, hashlib, sys
from pathlib import Path
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
FAC_RAW = ROOT / "_rawdata" / "facilities_raw.json"
COURSE_RAW = ROOT / "_rawdata" / "courses_raw.json"
FAC_OUT = ROOT / "_rawdata" / "facilities.json"
# region_courses.json은 Jekyll 빌드 시 정적 파일로 그대로 복사되어야 프론트엔드에서
# fetch('/region_courses.json')로 읽을 수 있음 - _rawdata/는 _config.yml에서
# exclude 처리되므로 루트에 직접 출력
REGION_COURSE_OUT = ROOT / "region_courses.json"

DO_MAP = {
    "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
    "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
    "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
    "강원특별자치도": "강원", "강원도": "강원",
    "충청북도": "충북", "충청남도": "충남",
    "전북특별자치도": "전북", "전라북도": "전북", "전라남도": "전남",
    "경상북도": "경북", "경상남도": "경남", "제주특별자치도": "제주",
}

REMOTE_TYPES = {"원격평생교육시설", "원격대학형태"}
OPEN_STATUS = "개원"
# 등록상태명이 빈 값인 레코드가 822건 있음(서울 524/부산 238 전체/세종 33 등).
# 특히 부산은 전체 238건이 전부 공백이라 "개원만" 필터링하면 부산 전체가 통째로
# 빠짐 - 명시적으로 폐원/휴원인 것만 제외하고 공백은 "상태 확인 필요"로 별도 표시.
EXCLUDED_STATUS = {"폐원", "휴원"}


def make_slug(name: str, addr: str, reg_ymd: str, ftype: str) -> str:
    slug = re.sub(r"[^\w가-힣\s-]", "", name).strip()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    # ftype 포함: 같은 회사가 오프라인+원격 두 유형으로 동시 등록된 케이스가
    # 실제로 존재함(이름/주소/등록일 셋 다 동일, 유형만 다름) - 2026-08-28 확인
    h = hashlib.md5(f"{name}|{addr}|{reg_ymd}|{ftype}".encode("utf-8")).hexdigest()[:6]
    return f"{slug}-{h}" if slug else h


def extract_sigungu(addr: str) -> str:
    if not addr:
        return ""
    for p in addr.split()[1:3]:
        if p.endswith(("시", "군", "구")):
            return p
    return ""


def process_facilities():
    raw = json.loads(FAC_RAW.read_text(encoding="utf-8"))
    items = []
    for d in raw:
        status = (d.get("REG_STTS_SE_NM") or "").strip()
        if status in EXCLUDED_STATUS:
            continue
        name = (d.get("FLCT_NM") or "").strip()
        if not name:
            continue
        addr = (d.get("LCTN_ROAD_NM_ADDR") or "").strip() or (d.get("LCTN_LOTNO_ADDR") or "").strip()
        do_full = (d.get("CTPV_NM") or "").strip()
        do_short = DO_MAP.get(do_full, do_full)
        sigungu = (d.get("SGG_NM") or "").strip() or extract_sigungu(addr)
        ftype = (d.get("FLCT_SE_NM") or "").strip()
        reg_ymd = (d.get("REG_YMD") or "").strip()

        items.append({
            # 필드명 주의: "name"은 Jekyll Page의 내장 속성(출력 파일명, 예: "index.html")과
            # 충돌해 템플릿에서 page.name이 시설명 대신 "index.html"을 반환하는 버그가
            # 실제로 발생함(2026-08-28 확인) - 반드시 "orgName" 등 다른 키를 사용할 것
            "orgName": name,
            "type": ftype,
            "isRemote": ftype in REMOTE_TYPES,
            "status": status,  # "개원" 또는 "" (상태 확인 필요)
            "doShort": do_short,
            "doFull": do_full,
            "sigungu": sigungu,
            "addr": addr,
            "founder": (d.get("FNDR_NM") or "").strip(),
            "tel": (d.get("TELNO") or "").strip(),
            "regDate": reg_ymd,
            "eduOffice": (d.get("ED_NM") or "").strip(),
            "acbgYn": (d.get("ACBG_RECOGN_YN") or "").strip(),
            "acbgYr": (d.get("ACBG_RECOGN_YR") or "").strip(),
            "homepage": (d.get("HMPG_ADDR") or "").strip(),
            "crtrYmd": (d.get("CRTR_YMD") or "").strip(),
            "slug": make_slug(name, addr, reg_ymd, ftype),
        })

    # 슬러그 충돌 안전장치: 이름+주소+등록일+유형이 전부 같은 완전 중복 레코드가
    # 있으면 뒤에 순번을 붙여 URL이 겹쳐 페이지가 서로 덮어써지는 것을 방지
    seen = Counter()
    for it in items:
        base = it["slug"]
        seen[base] += 1
        if seen[base] > 1:
            it["slug"] = f"{base}-{seen[base]}"

    FAC_OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"시설 {len(items)}개 저장 → {FAC_OUT}")

    do_counts = Counter(i["doShort"] for i in items)
    print("\n지역별 수:")
    for do, cnt in sorted(do_counts.items(), key=lambda x: -x[1]):
        print(f"  {do}: {cnt}개")

    type_counts = Counter(i["type"] for i in items)
    print("\n유형별 수:")
    for t, cnt in type_counts.most_common():
        print(f"  {t}: {cnt}개")


def process_region_courses():
    """시도+시군구별 강좌 집계 — 개별 시설과 매칭하지 않고 지역 페이지 보조정보로만 사용.
    (전국평생교육시설정보와 전국평생학습강좌정보는 운영주체 등록 체계가 달라
    기관명 매칭 시도 결과 1% 미만만 일치 — 2026-08-28 확인, 매칭 포기)
    주의: "중구"/"서구"/"동구" 등 시군구명은 여러 시도에 중복되므로 반드시
    시도로 먼저 묶은 뒤 시군구로 묶어야 함(시도 없이 시군구만 키로 쓰면
    다른 지역 강좌가 섞여 나옴)."""
    raw = json.loads(COURSE_RAW.read_text(encoding="utf-8"))
    by_do = defaultdict(lambda: defaultdict(list))
    for c in raw:
        addr = (c.get("EDC_RDNMADR") or "").strip()
        if not addr:
            continue
        do_raw = addr.split()[0]
        do_short = DO_MAP.get(do_raw)
        if do_short is None:
            # 주소 표기 오류(오타 등)로 알려진 17개 시도명과 매칭 안 되는 소수 레코드는
            # 보조 정보용 데이터라 정합성을 위해 건너뜀 (예: "전북특별차치도" 오타)
            continue
        sgg = extract_sigungu(addr)
        if not sgg:
            continue
        name = (c.get("LCTRE_NM") or "").strip()
        if not name:
            continue
        by_do[do_short][sgg].append({
            "name": name,
            "org": (c.get("OPER_INSTITUTION_NM") or "").strip(),
            "start": (c.get("EDC_START_DAY") or "").strip(),
            "end": (c.get("EDC_END_DAY") or "").strip(),
            "place": (c.get("EDC_PLACE") or "").strip(),
            "cost": (c.get("LCTRE_COST") or "").strip(),
        })

    # 시군구별 최대 8개만 미리보기로 저장 (전체 강좌 검색 UI를 만드는 게 아니라
    # 지역 페이지의 보조 섹션용 데이터이므로 용량을 제한)
    out = {}
    total_sgg = 0
    for do_short, sgg_map in by_do.items():
        out[do_short] = {}
        for sgg, v in sgg_map.items():
            out[do_short][sgg] = {"count": len(v), "sample": v[:8]}
            total_sgg += 1

    REGION_COURSE_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n지역별 강좌 집계 {len(out)}개 시도 / {total_sgg}개 시군구 저장 → {REGION_COURSE_OUT}")


if __name__ == "__main__":
    process_facilities()
    process_region_courses()
