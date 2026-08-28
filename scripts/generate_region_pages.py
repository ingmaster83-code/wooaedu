#!/usr/bin/env python3
"""region/{시도}/index.html 프론트매터 페이지 생성"""
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent
DATA = json.loads((ROOT / "_rawdata" / "facilities.json").read_text(encoding="utf-8"))

ICONS = {
    "서울": "🏙️", "경기": "🌆", "인천": "⚓", "강원": "🏔️", "충북": "📖",
    "충남": "🌊", "대전": "🏛️", "세종": "🌿", "전북": "🌾", "전남": "🐚",
    "광주": "🎨", "경북": "🍎", "경남": "🎋", "부산": "🌅", "대구": "🍑",
    "울산": "🏭", "제주": "🌺",
}

FULLNAME = {
    "서울": "서울특별시", "경기": "경기도", "인천": "인천광역시", "강원": "강원특별자치도",
    "충북": "충청북도", "충남": "충청남도", "대전": "대전광역시", "세종": "세종특별자치시",
    "전북": "전북특별자치도", "전남": "전라남도", "광주": "광주광역시", "경북": "경상북도",
    "경남": "경상남도", "부산": "부산광역시", "대구": "대구광역시", "울산": "울산광역시",
    "제주": "제주특별자치도",
}

counts = Counter(f["doShort"] for f in DATA)

for region in sorted(counts):
    full = FULLNAME.get(region, region)
    icon = ICONS.get(region, "🎓")
    cnt = counts[region]
    d = ROOT / "region" / region
    d.mkdir(parents=True, exist_ok=True)

    page_title = f"{full} 평생교육시설"
    title_h1 = f"{full} 평생교육시설 {cnt}개"
    subtitle = f"{full} 지역 평생교육원·문화센터·원격평생교육시설을 검색하세요."

    content = f"""---
layout: region
title: {page_title}
description: {full} 평생교육시설 정보. 교육청 등록 여부, 위치, 연락처, 학력인정 여부를 확인하세요.
do_name: {region}
title_h1: {title_h1}
subtitle: {subtitle}
---
"""
    (d / "index.html").write_text(content, encoding="utf-8")
    print(f"  {region} ({full}): {cnt}개")

print(f"\n완료: {len(counts)}개 지역 페이지 생성")
