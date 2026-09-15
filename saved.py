"""보관함: 시트(웹앱이 적은 공고번호 목록)를 읽어 공고를 saved.json에 보관. 마감일이 지나면 자동으로 빠짐."""
import csv, io, json, os, requests
from datetime import date, datetime
from pathlib import Path
from dotenv import load_dotenv
BASE = Path(__file__).parent; load_dotenv(BASE / ".env")
STORE = BASE / "saved.json"

def load_store():
    return json.loads(STORE.read_text(encoding="utf-8")) if STORE.exists() else {}

def sync(jobs_by_id):
    """시트의 공고번호를 보관함에 추가(공고 정보는 오늘 메일 목록에서 가져옴). 마감 지난 것은 제거."""
    store = load_store()
    url = os.getenv("SHEET_CSV_URL")
    if url:
        try:
            r = requests.get(url, timeout=30); r.raise_for_status()
            ids = [(row[1] if len(row) > 1 else "").strip() for row in list(csv.reader(io.StringIO(r.text)))[1:]]
            ids = [i for i in ids if i]
            unknown = [i for i in ids if i not in store and i not in jobs_by_id]
            print(f"[보관함] 시트 번호 {len(ids)}개, 기존 {sum(i in store for i in ids)}개, 새로 추가 {sum(i in jobs_by_id and i not in store for i in ids)}개" + (f", 정보 없음 {unknown}" if unknown else ""))
            for jid in ids:
                if jid not in store and jid in jobs_by_id:
                    j = jobs_by_id[jid]
                    store[jid] = {k: j.get(k, "") for k in ("id", "company", "title", "ncs", "job_type", "education", "end_date", "url", "reason")}
        except Exception as e:
            print("[보관함] 시트 읽기 실패:", str(e)[:100])
    today = date.today().strftime("%Y%m%d")
    store = {k: v for k, v in store.items() if not v.get("end_date") or v["end_date"] >= today}
    STORE.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    return store

def fmt(s): return f"{s[4:6].lstrip('0')}/{s[6:].lstrip('0')}" if len(s) == 8 else s
def dday(ymd):
    try: return (datetime.strptime(ymd, "%Y%m%d").date() - date.today()).days
    except Exception: return None
