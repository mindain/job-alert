"""1단계 수집: 잡알리오 API에 조건을 붙여 요청(채용구분별 2회), 시작일이 어제인 공고만 raw.csv로 저장."""
import csv, json, os, sys
from datetime import date, timedelta
from pathlib import Path
import requests
from dotenv import load_dotenv

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")
KEY = os.getenv("ALIO_API_KEY") or sys.exit("오류: .env에 ALIO_API_KEY 없음")
LIST = "https://apis.data.go.kr/1051000/recruitment/list"
FIELDS = ["id", "company", "title", "ncs", "job_type", "location", "career", "education",
          "qualification", "preference", "start_date", "end_date", "url"]

def fetch(recrut_se):
    rows, page = [], 1
    while True:
        url = (f"{LIST}?serviceKey={KEY}&resultType=json&numOfRows=100&pageNo={page}"
               f"&ongoingYn=Y&acbgCondLst=R7010,R7050&recrutSe={recrut_se}")
        body = requests.get(url, timeout=30).json()
        if body.get("resultCode") != 200:
            sys.exit(f"API 오류: {body.get('resultCode')} {body.get('resultMsg')}")
        items = body.get("result") or []
        rows += items
        if page * 100 >= int(body.get("totalCount", 0)) or not items:
            return rows, body
        page += 1

def to_row(j):
    return {"id": str(j["recrutPblntSn"]), "company": j.get("instNm", ""), "title": (j.get("recrutPbancTtl") or "").strip(),
            "ncs": j.get("ncsCdNmLst", ""), "job_type": j.get("hireTypeNmLst", ""), "location": j.get("workRgnNmLst", ""),
            "career": j.get("recrutSeNm", ""), "education": j.get("acbgCondNmLst", ""),
            "qualification": (j.get("aplyQlfcCn") or "").replace("\r", ""), "preference": (j.get("prefCondCn") or "").replace("\r", ""),
            "start_date": j.get("pbancBgngYmd", ""), "end_date": j.get("pbancEndYmd", ""), "url": j.get("srcUrl", "")}

def main():
    target = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
    if len(sys.argv) > 1: target = sys.argv[1]          # 시험용: python collect_alio.py 20260910
    seen, rows, meta = set(), [], {}
    for se in ("R2010", "R2030"):
        items, body = fetch(se)
        meta[se] = {"resultCode": body.get("resultCode"), "totalCount": body.get("totalCount"), "fetched": len(items)}
        for j in items:
            if str(j["recrutPblntSn"]) in seen: continue
            seen.add(str(j["recrutPblntSn"]))
            if j.get("pbancBgngYmd") == target: rows.append(to_row(j))
    with open(BASE / "raw.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    (BASE / "meta.json").write_text(json.dumps({"target": target, "calls": meta, "saved": len(rows)}, ensure_ascii=False), encoding="utf-8")
    print(f"[수집] 시작일 {target} · 신입/신입+경력 · 학력무관/대졸(4년): {len(rows)}건 → raw.csv")

if __name__ == "__main__": main()
