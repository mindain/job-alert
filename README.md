# job-alert

공공기관(잡알리오)·민간(사람인) 채용공고 중 서울·신입 지원 가능 공고를 매일 아침 8시에 자동 수집해, 신입 가능 여부·학력 요건·요구 스킬 등 항목별로 정리한 표를 이메일로 보내고 누적 저장하는 파이프라인.

## 흐름
collect_alio.py (공공데이터포털 잡알리오 API 수집: 공공기관 채용공시, 자격요건·우대사항 본문 포함) 또는 collect.py (사람인 API, 승인 후) → load.py (공고 번호 기준 중복 없이 누적) → check.py (원본 대조·결측·중복·마감 점검, 실패 시 중단) → extract.py (항목 정리 + xlsx) → send_mail.py (Gmail 발송)

## 로컬 실행
1. `.env.example`을 `.env`로 복사해 값 채우기
2. `pip install -r requirements.txt`
3. `python run_all.py`

## 자동 실행
`.github/workflows/daily.yml` 이 매일 08:00(KST)에 실행. 저장소 Secrets에 `.env`와 같은 4개 값을 등록해야 한다. 실패하면 `send_mail.py --fail` 로 점검 로그가 메일로 온다.

## 검증
- 매 실행 `logs/check_날짜.txt` 에 점검 결과가 남는다.
- `졸업예정가능` 항목은 규칙 추정이므로 30건을 손으로 대조해 정확도를 기록한다.
