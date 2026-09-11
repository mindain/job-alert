"""
잡알리오(공공기관 채용정보 조회서비스) API 응답 구조 확인용.
.env 에  ALIO_API_KEY=인증키(포털에 보이는 그대로, %2B %3D 포함)  를 넣고 실행.
실행:  python probe_alio.py
결과:  data/alio_probe.json 에 응답 원문 저장 + 화면에 첫 항목 출력
"""
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")
KEY = os.getenv("ALIO_API_KEY")
if not KEY:
    sys.exit("오류: .env에 ALIO_API_KEY 가 필요합니다.")

# 포털 키는 이미 URL 인코딩돼 있어서 params 로 넘기면 이중 인코딩됨 → 주소에 직접 붙인다
URL = f"https://apis.data.go.kr/1051000/recruitment/list?serviceKey={KEY}&pageNo=1&numOfRows=20&resultType=json"
r = requests.get(URL, timeout=30)
print("status:", r.status_code)
print("content-type:", r.headers.get("content-type"))
out = BASE / "data" / "alio_probe.json"
out.write_text(r.text, encoding="utf-8")
print("saved:", out)
try:
    body = r.json()
    print("\n[최상위 키]", list(body.keys()) if isinstance(body, dict) else type(body))
    def first_item(o):
        if isinstance(o, list):
            return o[0] if o else None
        if isinstance(o, dict):
            for v in o.values():
                res = first_item(v)
                if isinstance(res, dict) and len(res) > 3:
                    return res
        return None
    item = first_item(body)
    print("\n[첫 항목 필드]")
    print(json.dumps(item, ensure_ascii=False, indent=2)[:3000])
except ValueError:
    print("\n[JSON 아님] 응답 앞부분:\n", r.text[:1500])
