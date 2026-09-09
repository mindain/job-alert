"""
전체 실행: 수집 → 적재 → 점검 → 정리 → 메일. 점검이 실패하면 거기서 멈춘다.
실행:  python run_all.py
"""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
STEPS = ["collect.py", "load.py", "check.py", "extract.py", "send_mail.py"]

for step in STEPS:
    print(f"\n===== {step} =====")
    r = subprocess.run([sys.executable, str(BASE / step)])
    if r.returncode != 0:
        print(f"[중단] {step} 실패 (종료 코드 {r.returncode})")
        sys.exit(r.returncode)
print("\n[완료] 전체 단계 통과")
