"""구글 캘린더 등록. 최초 1회: credentials.json(구글 클라우드 OAuth 데스크톱 앱)을 폴더에 두고 실행하면 브라우저 승인 → token.json 저장."""
from pathlib import Path
from datetime import datetime, timedelta
BASE = Path(__file__).parent
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
def service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    tok = BASE / "token.json"
    creds = Credentials.from_authorized_user_file(tok, SCOPES) if tok.exists() else None
    if not creds or not creds.valid:
        creds = InstalledAppFlow.from_client_secrets_file(BASE / "credentials.json", SCOPES).run_local_server(port=0)
        tok.write_text(creds.to_json(), encoding="utf-8")
    return build("calendar", "v3", credentials=creds)
def add(item, what, ymd):
    end = (datetime.strptime(ymd, "%Y%m%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    body = {"summary": f"[{item['company']}] {what}", "description": f"{item.get('title','')}\n{item.get('url','')}",
            "start": {"date": f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"}, "end": {"date": end}}
    service().events().insert(calendarId="primary", body=body).execute()
    print(f"[캘린더] {body['summary']} {ymd}")
