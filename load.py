"""
3단계: 적재 (멱등성)
오늘 raw CSV를 누적 표(data/jobs_master.csv)에 합친다.
같은 공고 번호(id)는 두 번 넣지 않으므로, 하루에 몇 번 돌려도 결과가 같다.
실행:  python load.py
"""
import csv
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent
MASTER = BASE / "data" / "jobs_master.csv"


def read_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "data" / f"raw_{date.today()}.csv"
    if not src.exists():
        sys.exit(f"오류: {src} 가 없습니다. collect.py를 먼저 실행하세요.")
    new_rows = read_csv(src)

    master = read_csv(MASTER) if MASTER.exists() else []
    known = {r["id"] for r in master}
    before = len(master)

    added = 0
    for r in new_rows:
        if r["id"] in known:
            continue
        r["collected_at"] = str(date.today())
        master.append(r)
        known.add(r["id"])
        added += 1

    fields = list(new_rows[0].keys()) + ["collected_at"] if new_rows else (list(master[0].keys()) if master else ["id"])
    if master:
        fields = list(master[0].keys())
        if "collected_at" not in fields:
            fields.append("collected_at")
    with open(MASTER, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(master)

    print(f"[적재] 오늘 raw {len(new_rows)}건 중 새 공고 {added}건 추가 (중복 {len(new_rows)-added}건 건너뜀)")
    print(f"[적재] 누적 {before} → {len(master)}건  ({MASTER.name})")


if __name__ == "__main__":
    main()
