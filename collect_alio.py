"""
2단계: 수집 (잡알리오 - 공공기관 채용정보 조회서비스)
최신 공고를 받아 조건(서울, 신입 지원 가능, 진행 중)에 맞는 것만 data/raw_YYYY-MM-DD.csv 로 저장한다.
자격요건·우대사항 본문이 API에 포함돼 있어 따로 긁을 필요가 없다.
실행:  python collect_alio.py
.env:  ALIO_API_KEY=인증키 (포털에 보이는 그대로)
"""
import csv
import json
import os
import sys
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── 조건 (여기만 고치면 됨) ──────────────────────────────────
REGIONS = ["서울"]          # workRgnNmLst 에 이 말이 들어가면 통과. [] 이면 전국
NEW_GRAD_ONLY = True        # 신입 지원 가능(신입 / 신입+경력)만
PAGES = 3                   # 최신순으로 몇 페이지(100건씩) 볼지. 하루 1회면 2~3이면 충분
# ─────────────────────────────────────────────────────────────

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")
KEY = os.getenv("ALIO_API_KEY")
if not KEY:
    sys.exit("오류: .env 파일에 ALIO_API_KEY 가 없습니다.")

LIST = "https://apis.data.go.kr/1051000/recruitment/list"
FIELDS = ["id", "source", "company", "title", "location", "job_type", "job_mid", "job_code", "experience",
          "exp_min", "education", "keyword", "posting_date", "expiration_date", "url",
          "자격요건원문", "우대사항원문"]


def ymd(s):
    return f"{s[:4]}-{s[4:6]}-{s[6:]}" if s and len(s) == 8 else s or ""


def fetch_page(page):
    url = f"{LIST}?serviceKey={KEY}&pageNo={page}&numOfRows=100&resultType=json"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    body = r.json()
    if body.get("resultCode") != 200:
        sys.exit(f"API 오류: {body.get('resultCode')} {body.get('resultMsg')}")
    return body


def to_row(j):
    return {
        "id": f"alio-{j['recrutPblntSn']}",
        "source": "잡알리오",
        "company": j.get("instNm", ""),
        "title": j.get("recrutPbancTtl", ""),
        "location": j.get("workRgnNmLst", ""),
        "job_type": j.get("hireTypeNmLst", ""),
        "job_mid": j.get("ncsCdNmLst", ""),
        "job_code": "",
        "experience": j.get("recrutSeNm", ""),
        "exp_min": "0" if "신입" in (j.get("recrutSeNm") or "") else "",
        "education": j.get("acbgCondNmLst", ""),
        "keyword": (j.get("prefCn") or "")[:200],
        "posting_date": ymd(j.get("pbancBgngYmd")),
        "expiration_date": ymd(j.get("pbancEndYmd")),
        "url": j.get("srcUrl", ""),
        "자격요건원문": (j.get("aplyQlfcCn") or "").replace("\r", ""),
        "우대사항원문": (j.get("prefCondCn") or "").replace("\r", ""),
    }


def keep(j):
    if j.get("ongoingYn") != "Y":
        return False
    if REGIONS and not any(r in (j.get("workRgnNmLst") or "") for r in REGIONS):
        return False
    if NEW_GRAD_ONLY and "신입" not in (j.get("recrutSeNm") or "") and "무관" not in (j.get("recrutSeNm") or ""):
        return False
    return True


def main():
    fetched, rows, api_total = 0, [], None
    for p in range(1, PAGES + 1):
        body = fetch_page(p)
        api_total = int(body.get("totalCount", 0))
        items = body.get("result") or []
        fetched += len(items)
        rows += [to_row(j) for j in items if keep(j)]
        if len(items) < 100:
            break

    out = BASE / "data" / f"raw_{date.today()}.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    (BASE / "data" / f"meta_{date.today()}.json").write_text(json.dumps({
        "date": str(date.today()), "source": "잡알리오", "api_total": api_total,
        "fetched": fetched, "expected_fetched": min(api_total or 0, PAGES * 100), "saved": len(rows),
        "filter": {"regions": REGIONS, "new_grad_only": NEW_GRAD_ONLY}}, ensure_ascii=False), encoding="utf-8")

    print(f"[수집] 잡알리오 최신 {fetched}건 확인 (전체 {api_total}건) · 조건: 서울={REGIONS} 신입={NEW_GRAD_ONLY} 진행중")
    print(f"[저장] 조건 통과 {len(rows)}건 → {out.name}")


if __name__ == "__main__":
    main()
