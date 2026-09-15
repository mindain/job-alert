# job-alert · 공공기관 채용공고 자동 알림

매일 아침 8시, 어제 새로 올라온 공공기관 채용공고 중 조건(신입 가능 · 학력무관/대졸(4년))에 맞는 것을 받아,
Claude가 자격요건을 읽고 자격 미달은 걸러내고 나머지를 추천 / 그 외로 나눠 이메일로 보낸다.
메일의 [보관함에 넣기]를 누르면 그 공고가 접수 마감까지 매일 메일 하단에 따라온다.

## 흐름
collect_alio.py 수집(잡알리오 API, 채용구분별 2회 요청, 시작일이 어제인 것만)
→ check.py 점검(응답 정상 · 공고번호/URL 존재 · 마감일 형식, 실패 시 중단 + 실패 메일)
→ judge.py 판단(claude -p 에 자격요건·우대사항 + profile.txt 를 넘겨 자격 여부·추천 여부·이유)
→ send_mail.py 정리·발송(추천 / 그 외 / 자격 미달 기관명 + 보관함) · saved.py 보관함(Apps Script 웹앱 → Google Sheet)

## 실행
1. `.env`: ALIO_API_KEY, GMAIL_USER, GMAIL_APP_PASSWORD, MAIL_TO, SAVE_URL(웹앱 주소, `?id={id}`)
2. `pip install -r requirements.txt`, Claude Code 설치 + 로그인
3. `python run_all.py` · 자동 실행은 Windows 작업 스케줄러 → run_daily.bat (매일 08:00)

## 확인한 것
- 잡알리오 API: 학력 조건(acbgCondLst)은 OR, 채용구분(recrutSe)은 한 값만, 날짜 파라미터는 동작하지 않음(어제 지정 시 0건) → 스크립트에서 처리
- GitHub Actions(해외 IP)는 공공데이터포털이 차단 → 실패 알림 확인 후 로컬 스케줄러로 이전
