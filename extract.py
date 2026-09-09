"""
5단계 (1/2): 항목 정리
누적 표의 각 공고에 정리 항목을 붙여 data/jobs_master.csv 를 갱신하고
data/jobs_master.xlsx 로도 내보낸다.
항목: 신입가능 · 학력요건 · 졸업예정가능(추정) · 요구스킬 · 고용형태
(본문 없이 API가 준 칸과 제목·키워드만으로 규칙 정리. 추정 항목은 30건 손 대조로 정확도 확인할 것)
실행:  python extract.py
"""
import csv
import re
from pathlib import Path

BASE = Path(__file__).parent
MASTER = BASE / "data" / "jobs_master.csv"
XLSX = BASE / "data" / "jobs_master.xlsx"

SKILLS = ["SQL", "Python", "R", "Tableau", "Power BI", "Excel", "Amplitude", "GA4", "Google Analytics",
          "BigQuery", "Spark", "Hadoop", "Looker", "Redash", "Airflow", "통계", "머신러닝", "A/B"]
NEW_COLS = ["신입가능", "학력요건", "졸업예정가능", "요구스킬", "고용형태"]


def enrich(r):
    text = f"{r.get('title','')} {r.get('keyword','')}"
    exp = r.get("experience", "")
    r["신입가능"] = "Y" if ("신입" in exp or r.get("exp_min") in ("0", "")) else "N"
    edu = r.get("education", "")
    r["학력요건"] = edu
    # 신입 공고는 '대졸 이상'이어도 졸업예정자가 통상 지원 가능하므로 기본 Y.
    # 제목·키워드에 기졸업자 한정 표현이 있을 때만 N. (본문이 없어 확정은 불가 → 손 대조 대상)
    r["졸업예정가능"] = "N" if re.search(r"기졸업|졸업자만|졸업자에 한", text) else "Y"
    found = [s for s in SKILLS if re.search(re.escape(s), text, re.IGNORECASE)]
    r["요구스킬"] = ", ".join(found)
    r["고용형태"] = r.get("job_type", "")
    return r


def main():
    with open(MASTER, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    rows = [enrich(r) for r in rows]
    fields = [k for k in rows[0].keys() if k not in NEW_COLS] + NEW_COLS if rows else ["id"] + NEW_COLS
    with open(MASTER, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    try:
        import openpyxl
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "jobs"
        ws.append(fields)
        for r in rows:
            ws.append([r.get(k, "") for k in fields])
        wb.save(XLSX)
        print(f"[정리] {len(rows)}건 항목 정리 → {MASTER.name}, {XLSX.name}")
    except ImportError:
        print(f"[정리] {len(rows)}건 항목 정리 → {MASTER.name} (openpyxl 없음: xlsx 생략)")


if __name__ == "__main__":
    main()
