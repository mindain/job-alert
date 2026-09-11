"""
4단계: 자동 점검
데이터가 깨졌으면 스스로 알아채고 멈춘다(종료 코드 1). 결과는 logs/ 에 남긴다.
실행:  python check.py
점검 항목
  1. API 응답 총건수 == raw 저장 건수         (원본과 대조)
  2. 필수 칸(id·회사·제목·URL) 비어 있지 않음
  3. 누적 표에 공고 번호 중복 없음
  4. 마감일이 오늘보다 전인 공고가 오늘 raw에 없음
"""
import csv
import json
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent
LOGS = BASE / "logs"
LOGS.mkdir(exist_ok=True)


def read_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    today = str(date.today())
    raw_p, meta_p, master_p = BASE / "data" / f"raw_{today}.csv", BASE / "data" / f"meta_{today}.json", BASE / "data" / "jobs_master.csv"
    for p in (raw_p, meta_p, master_p):
        if not p.exists():
            sys.exit(f"오류: {p.name} 가 없습니다. collect.py → load.py 순서로 먼저 실행하세요.")
    raw, meta, master = read_csv(raw_p), json.loads(meta_p.read_text(encoding="utf-8")), read_csv(master_p)

    results = []
    # 1. 원본과 대조
    if "fetched" in meta:   # 잡알리오: 요청한 만큼 받았는지 + 저장 건수가 meta와 같은지
        ok = meta["fetched"] == meta["expected_fetched"] and meta["saved"] == len(raw)
        results.append(("API 응답 건수 == 요청 건수, 저장 건수 == 파일 행 수", ok,
                        f"fetched={meta['fetched']}/{meta['expected_fetched']} saved={meta['saved']} rows={len(raw)}"))
    else:                    # 사람인: API total == 저장 건수
        results.append(("API 총건수 == 저장 건수", meta["api_total"] == len(raw), f"api={meta['api_total']} saved={len(raw)}"))
    # 2. 필수 칸
    missing = [r["id"] for r in raw if not all(r.get(k) for k in ("id", "company", "title", "url"))]
    results.append(("필수 칸 결측 없음", not missing, f"결측 {len(missing)}건 {missing[:5]}"))
    # 3. 중복
    ids = [r["id"] for r in master]
    dup = len(ids) - len(set(ids))
    results.append(("누적 표 중복 없음", dup == 0, f"중복 {dup}건"))
    # 4. 마감 지난 공고
    expired = [r["id"] for r in raw if r.get("expiration_date") and r["expiration_date"] < today]
    results.append(("마감 지난 공고 없음", not expired, f"만료 {len(expired)}건 {expired[:5]}"))

    lines = [f"[점검] {today}"]
    ok_all = True
    for name, ok, detail in results:
        ok_all &= ok
        lines.append(f"  {'PASS' if ok else 'FAIL'}  {name}  ({detail})")
    lines.append(f"[결과] {'모두 통과' if ok_all else '실패 - 파이프라인 중단'}")
    text = "\n".join(lines)
    print(text)
    (LOGS / f"check_{today}.txt").write_text(text, encoding="utf-8")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
