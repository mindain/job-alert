"""4단계 정리·발송: 추천 / 그 외 / 자격 미달(기관명) + 보관함(마감까지 매일 표시). --fail 이면 실패 알림."""
import csv, os, smtplib, sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from dotenv import load_dotenv
import saved
BASE = Path(__file__).parent; load_dotenv(BASE / ".env")
USER, PW, TO = os.getenv("GMAIL_USER"), os.getenv("GMAIL_APP_PASSWORD"), os.getenv("MAIL_TO")
SAVE = os.getenv("SAVE_URL", "")

def link(jid):
    return f' <a href="{SAVE.replace("{id}", jid)}">[보관함에 넣기]</a>' if SAVE else ""

def send(subject, html, files=()):
    if not (USER and PW and TO): sys.exit("오류: .env에 GMAIL_USER, GMAIL_APP_PASSWORD, MAIL_TO 필요")
    m = MIMEMultipart(); m["Subject"], m["From"], m["To"] = subject, USER, TO
    m.attach(MIMEText(html, "html", "utf-8"))
    for content, name in files:
        part = MIMEBase("text", "calendar", method="PUBLISH", name=name); part.set_payload(content.encode("utf-8"))
        encoders.encode_base64(part); part.add_header("Content-Disposition", "attachment", filename=name); m.attach(part)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s: s.login(USER, PW); s.sendmail(USER, [TO], m.as_string())
    print(f"[메일] 발송: {subject} (첨부 {len(files)})")

def d(s): return saved.fmt(s)
def line(r):
    return (f'<p style="margin:10px 0"><b>{r["company"]}</b> · {r["title"]}<br>'
            f'<span style="color:#555;font-size:13px">{r["ncs"]} · {r["job_type"]} · {r["education"]} · 마감 {d(r["end_date"])} · '
            f'<a href="{r["url"]}">[원문]</a>{link(r["id"])}</span><br>'
            f'<span style="color:#b85450">▸ {r["reason"]}</span></p>')

def main():
    today = date.today()
    if "--fail" in sys.argv:
        log = BASE / "logs" / f"check_{today}.txt"
        send(f"[job-alert] {today} 실행 실패", f"<pre>{log.read_text(encoding='utf-8') if log.exists() else '점검 로그 없음'}</pre>"); return
    rows = list(csv.DictReader(open(BASE / "judged.csv", encoding="utf-8-sig")))
    ok = [r for r in rows if r["eligible"] == "True"]; rec = [r for r in ok if r["recommend"] == "True"]; etc = [r for r in ok if r["recommend"] != "True"]
    out = [r for r in rows if r["eligible"] != "True"]
    body = [f'<p>어제 새로 올라온 신입 가능 · 학력무관/대졸(4년) 공고 {len(rows)}건 중 자격 미달 {len(out)}건을 뺀 {len(ok)}건입니다. '
            f'<span style="color:#777;font-size:12px">(지역·경력·학력 조건은 API 요청에서 적용)</span></p>']
    body.append(f"<h3>추천 ({len(rec)})</h3>" + ("".join(line(r) for r in rec) or "<p>없음</p>"))
    body.append(f"<h3>그 외 ({len(etc)})</h3>" + ("".join(line(r) for r in etc) or "<p>없음</p>"))
    if out: body.append(f'<p style="color:#777;font-size:13px"><b>자격 미달 제외 ({len(out)})</b> ' + " · ".join(f'{r["company"]}({r["reason"]})' for r in out) + "</p>")
    # 보관함: 오늘 목록 + 이전에 보관된 공고(saved.json)에서 번호를 찾음
    jobs = {r["id"]: r for r in rows}; jobs.update({k: v for k, v in saved.load_store().items()})
    store = saved.sync(jobs)
    active = sorted(store.values(), key=lambda v: v.get("end_date") or "9")
    files = []
    if active:
        body.append(f"<hr><h3>보관함 ({len(active)})</h3>")
        for v in active:
            d0 = saved.dday(v.get("end_date", ""))
            body.append(f'<p style="margin:8px 0"><b>{v["company"]}</b> · {v["title"]}<br>'
                        f'<span style="color:#555;font-size:13px">{v.get("ncs","")} · {v.get("job_type","")} · {v.get("education","")} · '
                        f'접수 마감 {saved.fmt(v.get("end_date",""))}{f" (D-{d0})" if d0 is not None else ""} · <a href="{v["url"]}">[원문]</a></span></p>')
    send(f"[job-alert] {today.month}/{today.day} 공공기관 신입 공고 · 추천 {len(rec)} · 그 외 {len(etc)} · 미달 {len(out)} · 보관함 {len(active)}", "\n".join(body), files)

if __name__ == "__main__": main()
