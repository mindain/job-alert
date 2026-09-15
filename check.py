"""2단계 점검: 응답 정상 / 공고번호·URL 존재 / 마감일 형식·순서. 실패 시 종료 코드 1."""
import csv, json, re, sys
from datetime import date
from pathlib import Path
BASE = Path(__file__).parent
meta = json.loads((BASE / "meta.json").read_text(encoding="utf-8"))
rows = list(csv.DictReader(open(BASE / "raw.csv", encoding="utf-8-sig")))
def date_ok(r): return bool(re.fullmatch(r"\d{8}", r["end_date"] or "")) and r["end_date"] >= r["start_date"]
bad_date = sum(not date_ok(r) for r in rows)
checks = [
  ("API 응답 정상", all(c["resultCode"] == 200 for c in meta["calls"].values()), str({k: v["resultCode"] for k, v in meta["calls"].items()})),
  ("공고번호·원문 링크 있음", all(r["id"] and r["url"] for r in rows), f"{sum(not (r['id'] and r['url']) for r in rows)}건 결측"),
  ("마감일 형식·순서 정상", bad_date == 0, f"{bad_date}건 이상"),
]
lines = [f"[점검] {date.today()} · 대상 {len(rows)}건"] + [f"  {'PASS' if ok else 'FAIL'}  {n}  ({d})" for n, ok, d in checks]
ok_all = all(ok for _, ok, _ in checks)
lines.append("[결과] " + ("모두 통과" if ok_all else "실패 - 중단"))
(BASE / "logs").mkdir(exist_ok=True); (BASE / "logs" / f"check_{date.today()}.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines)); sys.exit(0 if ok_all else 1)
