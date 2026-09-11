"""
주간 시장 리포트 (뉴스레터)
누적 표(data/jobs_master.csv)로 최근 7일 공고를 집계해 HTML 뉴스레터를 만들고
data/weekly_YYYY-MM-DD.html 로 저장한다. --send 를 붙이면 메일로도 보낸다.
집계: 공고 수, 신입 비율, 학력 요건 분포, 요구 스킬 빈도, 고용형태 분포, 산업(job_mid) 상위
실행:  python weekly_report.py          (파일만)
       python weekly_report.py --send   (파일 + 메일)
"""
import csv
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).parent
MASTER = BASE / "data" / "jobs_master.csv"


def pct(n, d):
    return f"{(100*n/d):.0f}%" if d else "-"


def table(counter, total, title, top=8):
    rows = "".join(f"<tr><td>{k or '(없음)'}</td><td align='right'>{v}</td><td align='right'>{pct(v,total)}</td></tr>"
                   for k, v in counter.most_common(top))
    return f"<h3>{title}</h3><table border='1' cellpadding='4' style='border-collapse:collapse;font-size:13px'>{rows}</table>"


def build(rows, since, today):
    n = len(rows)
    new_grad = sum(r.get("신입가능") == "Y" for r in rows)
    edu, skill, jtype, mid = Counter(), Counter(), Counter(), Counter()
    for r in rows:
        edu[r.get("학력요건", "")] += 1
        jtype[r.get("고용형태", "")] += 1
        mid[r.get("job_mid", "")] += 1
        for s in filter(None, (x.strip() for x in r.get("요구스킬", "").split(","))):
            skill[s] += 1
    html = [f"<h2>공공기관 채용 주간 리포트 (서울·신입 가능) ({since} ~ {today})</h2>",
            f"<p>이번 주 새 공고 <b>{n}건</b> · 신입 지원 가능 <b>{new_grad}건 ({pct(new_grad, n)})</b></p>"]
    if n:
        html += [table(skill, n, "요구 스킬 언급 빈도 (공고 수 기준)"),
                 table(edu, n, "학력 요건 분포"),
                 table(jtype, n, "고용형태 분포"),
                 table(mid, n, "직무 분류 상위")]
        top = sorted(rows, key=lambda r: r.get("expiration_date", ""))[:10]
        li = "".join(f"<li>{r['company']} · <a href='{r['url']}'>{r['title']}</a> (마감 {r.get('expiration_date','')})</li>" for r in top)
        html.append(f"<h3>마감 임박 10건</h3><ul>{li}</ul>")
    else:
        html.append("<p>이번 주 수집된 공고가 없습니다.</p>")
    return "\n".join(html)


def main():
    if not MASTER.exists():
        sys.exit("오류: jobs_master.csv 가 없습니다.")
    today = date.today()
    since = today - timedelta(days=7)
    with open(MASTER, encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f) if r.get("collected_at", "") >= str(since)]
    html = build(rows, since, today)
    out = BASE / "data" / f"weekly_{today}.html"
    out.write_text(html, encoding="utf-8")
    print(f"[주간] 최근 7일 {len(rows)}건 집계 → {out.name}")
    if "--send" in sys.argv:
        from send_mail import send
        send(f"[job-alert] 주간 채용 시장 리포트 {today}", html)


if __name__ == "__main__":
    main()
