"""
5단계 (2/2): 이메일 발송
오늘 새로 쌓인 공고를 항목별 표로 만들어 Gmail로 보낸다.
실행:  python send_mail.py            (오늘 새 공고 메일)
       python send_mail.py --fail     (파이프라인 실패 알림, 6단계에서 사용)
.env:  GMAIL_USER=보내는 지메일, GMAIL_APP_PASSWORD=앱 비밀번호(16자리), MAIL_TO=받는 주소
"""
import csv
import os
import smtplib
import sys
from datetime import date
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")
USER, PW, TO = os.getenv("GMAIL_USER"), os.getenv("GMAIL_APP_PASSWORD"), os.getenv("MAIL_TO")
COLS = ["company", "title", "신입가능", "학력요건", "졸업예정가능", "요구스킬", "고용형태", "expiration_date", "url"]
HEAD = ["회사", "공고", "신입", "학력", "졸업예정", "요구스킬", "고용형태", "마감", "링크"]


def send(subject, html):
    if not (USER and PW and TO):
        sys.exit("오류: .env에 GMAIL_USER, GMAIL_APP_PASSWORD, MAIL_TO 가 필요합니다.")
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"], msg["From"], msg["To"] = subject, USER, TO
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(USER, PW)
        s.sendmail(USER, [TO], msg.as_string())
    print(f"[메일] 발송 완료: {subject}")


def build_html(rows):
    if not rows:
        return "<p>오늘 새로 뜬 공고가 없습니다.</p>"
    th = "".join(f"<th style='border:1px solid #ccc;padding:4px'>{h}</th>" for h in HEAD)
    trs = []
    for r in rows:
        tds = []
        for c in COLS:
            v = r.get(c, "")
            if c == "url":
                v = f"<a href='{v}'>보기</a>"
            tds.append(f"<td style='border:1px solid #ccc;padding:4px'>{v}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f"<p>오늘 새 공고 {len(rows)}건</p><table style='border-collapse:collapse;font-size:13px'><tr>{th}</tr>{''.join(trs)}</table>"


def main():
    today = str(date.today())
    if "--fail" in sys.argv:
        log = BASE / "logs" / f"check_{today}.txt"
        body = log.read_text(encoding="utf-8") if log.exists() else "점검 로그 없음 (수집 단계에서 실패했을 수 있음)"
        send(f"[job-alert] {today} 실행 실패", f"<pre>{body}</pre>")
        return
    with open(BASE / "data" / "jobs_master.csv", encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f) if r.get("collected_at") == today]
    send(f"[job-alert] {today} 데이터 분석 신입 공고 {len(rows)}건", build_html(rows))


if __name__ == "__main__":
    main()
