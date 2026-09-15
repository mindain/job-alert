"""수집 → 점검 → 판단 → 발송. 점검 실패 시 멈추고 실패 알림."""
import subprocess, sys
from pathlib import Path
BASE = Path(__file__).parent
for step in ["collect_alio.py", "check.py", "judge.py", "send_mail.py"]:
    print(f"\n===== {step} =====")
    if subprocess.run([sys.executable, str(BASE / step)]).returncode != 0:
        print(f"[중단] {step} 실패"); subprocess.run([sys.executable, str(BASE / "send_mail.py"), "--fail"]); sys.exit(1)
print("\n[완료]")
