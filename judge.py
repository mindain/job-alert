"""3단계 판단: 공고마다 자격요건·우대사항 + profile.txt 를 Claude(claude -p)에 넘겨 자격 여부·추천 여부·이유를 받는다. → judged.csv"""
import csv, json, subprocess, sys
from pathlib import Path
BASE = Path(__file__).parent
PROFILE = (BASE / "profile.txt").read_text(encoding="utf-8")
PROMPT = """다음은 공공기관 채용공고의 자격요건과 우대사항, 그리고 지원자 이력이다.
JSON 한 줄로만 답하라: {{"eligible": true/false, "recommend": true/false, "reason": "한 문장(40자 이내)"}}
- eligible: 지원자가 자격요건을 충족하는가. 졸업자 한정·자격증 소지 필수·석사 이상 등 명시적 제한에 걸리면 false. 명시가 없으면 true.
- recommend: eligible일 때 이력의 추천 기준에 맞는가.
- reason: 판단 근거. 불가면 무엇에 걸렸는지, 추천이면 어떤 점이 맞는지.

[지원자 이력]
{profile}

[공고] {company} · {title}
직무분류: {ncs} / 고용형태: {job_type} / 학력조건: {education}
[자격요건]
{qualification}
[우대사항]
{preference}
"""
def ask(r):
    p = PROMPT.format(profile=PROFILE, **{k: (r[k] or "없음")[:1500] for k in ["company","title","ncs","job_type","education","qualification","preference"]})
    res = subprocess.run("claude -p \"입력으로 주는 공고와 이력을 읽고 지시대로 JSON 한 줄만 출력하라\"", input=p, shell=True,
                         capture_output=True, text=True, encoding="utf-8", timeout=180)
    out = (res.stdout or "").strip()
    if not out: print("  ! claude 응답 없음:", (res.stderr or "")[:200])
    try:
        j = json.loads(out[out.index("{"):out.rindex("}")+1])
        return bool(j.get("eligible")), bool(j.get("recommend")), str(j.get("reason", ""))[:80]
    except Exception:
        print("  ! 응답 원문:", out[:300].replace("\n", " | "), "| stderr:", (res.stderr or "")[:200])
        return True, False, "판단 실패(응답 해석 불가)"
rows = list(csv.DictReader(open(BASE / "raw.csv", encoding="utf-8-sig")))
for i, r in enumerate(rows, 1):
    r["eligible"], r["recommend"], r["reason"] = ask(r)
    print(f"  {i}/{len(rows)} {r['company'][:12]} → {'자격O' if r['eligible'] else '자격X'} {'추천' if r['recommend'] else '그외'} · {r['reason']}")
with open(BASE / "judged.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["id"]); w.writeheader(); w.writerows(rows)
print(f"[판단] {len(rows)}건 → judged.csv")
