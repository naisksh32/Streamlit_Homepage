# Roleplaying Agent

개발계획서 기준 **보이스피싱 예방 롤플레잉**을 담당하는 하위 에이전트입니다.  
**Supervisor(Master Agent)**가 지시를 내리면, 매일경제 뉴스 기반 사례를 참고해 사기범 역할의 대사 한 턴을 생성합니다.

## Supervisor 호출 방식

```python
from src.agents.roleplaying import run_roleplaying_agent, build_memory, update_long_term_summary

# 롤플레잉 시작 지시
reply = run_roleplaying_agent(
    instruction="뉴스 데이터를 참고하여 최근 유행하는 보이스피싱 사기상황 롤플레잉을 시작해",
)
print(reply)  # 사기범의 첫 마디

# 메모리 사용: 단기(최근 10턴) + 장기(시나리오 요약). Supervisor가 유지·갱신
memory = build_memory(conversation_history=전체대화, long_term_summary="지금까지 시나리오 요약")
reply = run_roleplaying_agent(
    instruction="정상적으로 진행해. 사용자 응답에 맞춰 사기범 대사를 이어가.",
    memory=memory,  # memory 사용 시 conversation_history 대신 전달
)
# 턴 종료 후 장기 요약 갱신 (Supervisor가 호출)
new_summary = update_long_term_summary(최근_턴들, old_summary, anthropic_client=client)
```

## 메모리 (단기 10턴 + 장기 요약)

- **단기**: 최근 10턴만 에이전트에 전달 (`build_short_term` / `build_memory`의 `short_term`).
- **장기**: 시나리오·대화 요약 문자열. Supervisor가 `update_long_term_summary(최근_턴, 기존_요약, anthropic_client)`로 주기적으로 갱신 후 다음 호출 시 `memory["long_term_summary"]`로 넘김.

## RAG 도구 (공용)

- **공용 도구**: `src/tools/voice_phishing_rag.py`의 `search_voice_phishing_cases`를 Roleplaying·Guardian 등이 동일하게 사용합니다. RAG(ChromaDB 등)는 **src/tools** 쪽 한 곳에만 연결하면 됩니다.
- 새 도구는 `src/tools/`에 py 파일로 추가해 에이전트에서 import하면 됩니다.

## 환경 변수

- `ANTHROPIC_API_KEY`: Claude API 키 (필수)

## 디렉터리 구조

```
src/agents/roleplaying/
├── __init__.py   # run_roleplaying_agent, build_memory, update_long_term_summary 등 export
├── agent.py      # Claude 호출 + 도구 루프 + 메모리 반영
├── memory.py    # 단기 10턴, 장기 요약 빌드/갱신
├── prompts.py   # ROLEPLAYING_SYSTEM_PROMPT, format_supervisor_instruction
├── tools.py     # src.tools re-export (하위 호환)
└── README.md
```

## 흐름도
```
[SUPERVISOR] ── "롤플레잉 시작해" ──► [ROLEPLAYING] ── 사기범 첫 마디 ──► [사용자]
      ▲                                                                   │
      │                                                                   │ 사용자 응답
      │                                                                   ▼
      └────── 사용자 응답 수신 ──── [Evaluator?] ──── "정상 진행, 대사 이어가" ──► [ROLEPLAYING]
                (개인정보 없음)            │
                                          │ 개인정보 있음
                                          ▼
                                    [Guardian] 개입·교육
```