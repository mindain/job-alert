"""
채용공고 수집 스크립트 (PART 4 - 2단계)
사람인 채용정보 API에서 조건에 맞는 공고를 받아 CSV로 저장한다.

실행:  python collect.py            (어제~오늘 등록 공고)
       python collect.py 2026-09-01 (특정 날짜 이후 등록 공고)
결과:  data/raw_YYYY-MM-DD.csv
키:    같은 폴더의 .env 파일에 SARAMIN_ACCESS_KEY=발급받은키
"""
import csv
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── 검색 조건 (여기만 고치면 됨) ─────────────────────────────
KEYWORDS = "데이터 분석"      # 사람인 검색창에 넣는 말과 같음
LOC_MCD = "101000"           # 근무지: 101000 = 서울 전체
SORT = "pd"                  # 최신 등록순
COUNT = 110                  # 페이지당 최대 건수(API 상한)
# ─────────────────────────────────────────────────────────────

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")
KEY = os.getenv("SARAMIN_ACCESS_KEY")
if not KEY:
    sys.exit("오류: .env 파일에 SARAMIN_ACCESS_KEY가 없습니다.")

API = "https://oapi.saramin.co.kr/job-search"
FIELDS = ["id", "company", "title", "location", "job_type", "job_mid", "job_code", "experience",
          "exp_min", "education", "keyword", "posting_date", "expiration_date", "url"]


def fetch(published_min: str) -> tuple[list[dict], int]:
    """published_min 이후 등록된 공고를 전부 받아 (행 목록, API가 알려준 총건수) 반환"""
    rows, start, total = [], 0, None
    while True:
        params = {
            "access-key": KEY,
            "keywords": KEYWORDS,
            "loc_mcd": LOC_MCD,
            "published_min": published_min,
            "sort": SORT,
            "start": start,
            "count": COUNT,
            "fields": "posting-date,expiration-date",
        }
        r = requests.get(API, params=params, headers={"Accept": "application/json"}, timeout=30)
        r.raise_for_status()
        body = r.json()
        if "jobs" not in body:  # 오류 응답 {"code":..,"message":..}
            sys.exit(f"API 오류: {body}")
        jobs = body["jobs"]
        total = int(jobs["total"])
        for j in jobs["job"]:
            p = j["position"]
            rows.append({
                "id": j["id"],
                "company": j["company"]["detail"]["name"],
                "title": p["title"],
                "location": p["location"]["name"],
                "job_type": p["job-type"]["name"],
                "job_mid": p["job-mid-code"]["name"],
                "job_code": p["job-code"]["name"],
                "experience": p["experience-level"]["name"],
                "exp_min": p["experience-level"]["min"],
                "education": p["required-education-level"]["name"],
                "keyword": j.get("keyword", ""),
                "posting_date": j.get("posting-date", "")[:10],
                "expiration_date": j.get("expiration-date", "")[:10],
                "url": j["url"],
            })
        start += 1
        if len(rows) >= total or not jobs["job"]:
            break
    return rows, total


def main():
    published_min = sys.argv[1] if len(sys.argv) > 1 else str(date.today() - timedelta(days=1))
    rows, total = fetch(published_min)

    out = BASE / "data" / f"raw_{date.today()}.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    # 4단계(check.py)가 대조할 수 있게 API가 말한 총건수를 기록
    import json
    (BASE / "data" / f"meta_{date.today()}.json").write_text(
        json.dumps({"date": str(date.today()), "published_min": published_min,
                    "api_total": total, "saved": len(rows)}, ensure_ascii=False), encoding="utf-8")

    print(f"[수집] {published_min} 이후 등록 · 조건: '{KEYWORDS}' / 서울")
    print(f"[대조] API total={total}  저장={len(rows)}  →  {'일치' if total == len(rows) else '불일치!'}")
    print(f"[저장] {out}")


if __name__ == "__main__":
    main()
