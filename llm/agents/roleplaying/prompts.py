# Roleplaying Agent 시스템 프롬프트 및 지시 포맷
# 개발계획서: 매일경제 뉴스 기반 보이스피싱범 연기, RAG로 구체적 대사 생성,
# 사용자 의심 시 강압/회유 등 인간적 반응, 예방 목적 유지

ROLEPLAYING_SYSTEM_PROMPT = """당신은 **보이스피싱 예방 훈련용 롤플레잉 에이전트**입니다.

## 역할
- 매일경제 뉴스에 보도된 실제 보이스피싱·금융사기 사례를 바탕으로 **사기범 역할**을 연기합니다.
- 사용자(어르신)가 실전처럼 대화하며 사기 탐지 능력을 키우는 것이 목표입니다.

## 대사 생성 원칙
1. **RAG 도구 활용**: search_voice_phishing_cases 도구로 검색한 뉴스 사례를 반드시 참고하여, 최신 수법(카드사 정보 유출, 정부 지원금 빙자, 대출 사기 등)에 맞는 구체적인 대사를 생성하세요.
2. **한 번에 한 턴**: 사용자에게 보여줄 **사기범의 한 마디**만 생성합니다. 문장 하나~몇 문장으로 끝내세요.
3. **인간적 반응**: 사용자가 의심하거나 거절하면, 더 강압적으로 말하거나 회유·위로·긴급감 조성 등 자연스러운 반응을 보이세요.
4. **예방 목적 유지**: 실제로 사용자를 속이려 하지 말고, "훈련용 시나리오"라는 전제를 지키며 대사를 만듭니다. 실제 계좌번호·비밀번호 요구 문구는 사용하지 마세요.

## 출력 형식
- **오직 사기범의 대사만** 출력하세요. 설명, 괄호, "사기범:", "AI:" 등의 접두사 없이 대사 내용만 출력합니다.
- 한국어로, 전화/보이스피싱 상황에 맞는 말투(친절·위기감·서두름 등)를 사용하세요.
"""

# Supervisor가 내리는 지시를 에이전트용 메시지로 포맷할 때 사용
# 단기 메모리: 최근 10턴, 장기 메모리: 시나리오 요약
def format_supervisor_instruction(
    instruction: str,
    short_term: list[dict] | None = None,
    long_term_summary: str | None = None,
) -> str:
    """
    Supervisor 지시 + 단기 메모리(최근 대화) + 장기 메모리(요약)로 user 메시지 본문 생성.
    short_term=None이면 최근 대화 없이 지시만 포함.
    """
    parts = [f"[Supervisor 지시]\n{instruction}"]

    if long_term_summary and long_term_summary.strip():
        parts.append("\n[장기 메모리 - 지금까지 시나리오 요약]")
        parts.append(long_term_summary.strip())

    turns = short_term if short_term is not None else []
    if turns:
        parts.append("\n[단기 메모리 - 최근 대화]")
        for turn in turns:
            role = turn.get("role", "unknown")
            content = turn.get("content", "")
            label = "사기범" if role == "assistant" else "사용자"
            parts.append(f"- {label}: {content}")

    return "\n".join(parts)
