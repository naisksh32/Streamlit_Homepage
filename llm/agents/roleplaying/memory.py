# Roleplaying Agent 메모리: 단기(최근 N턴) + 장기(요약)
# Supervisor가 유지·갱신하고 에이전트 호출 시 전달

import logging
from typing import Any

logger = logging.getLogger(__name__)

SHORT_TERM_MAX_TURNS = 10


def build_short_term(conversation_history: list[dict[str, str]], max_turns: int = SHORT_TERM_MAX_TURNS) -> list[dict[str, str]]:
    """대화 이력에서 최근 max_turns턴만 잘라 단기 메모리로 반환."""
    if not conversation_history:
        return []
    return conversation_history[-max_turns:]


def build_memory(
    conversation_history: list[dict[str, str]] | None = None,
    long_term_summary: str = "",
    max_short_term: int = SHORT_TERM_MAX_TURNS,
) -> dict[str, Any]:
    """
    Supervisor가 에이전트 호출 전에 쓸 메모리 객체를 만듭니다.

    Args:
        conversation_history: 지금까지의 전체 대화
        long_term_summary: 지금까지 시나리오/대화 요약 (장기 메모리)
        max_short_term: 단기 메모리에 넣을 최대 턴 수 (기본 10)

    Returns:
        { "short_term": [...], "long_term_summary": "..." }
    """
    history = conversation_history or []
    return {
        "short_term": build_short_term(history, max_short_term),
        "long_term_summary": (long_term_summary or "").strip(),
    }


def update_long_term_summary(
    short_term_turns: list[dict[str, str]],
    old_summary: str,
    *,
    anthropic_client: Any = None,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 256,
) -> str:
    """
    단기 메모리(최근 턴)와 기존 장기 요약을 바탕으로 새 장기 요약을 생성합니다.
    Supervisor가 턴 종료 후 또는 주기적으로 호출해 장기 메모리를 갱신할 때 사용.

    Args:
        short_term_turns: 최근 대화 턴 (예: 방금 추가된 1~2턴 또는 최근 10턴)
        old_summary: 기존 장기 요약 (없으면 "")
        anthropic_client: Anthropic 클라이언트. None이면 요약 없이 old_summary 그대로 반환.

    Returns:
        갱신된 장기 요약 문자열.
    """
    if not anthropic_client:
        return old_summary or ""

    dialogue = "\n".join(
        f"{'사기범' if t.get('role') == 'assistant' else '사용자'}: {t.get('content', '')}"
        for t in short_term_turns
    )
    if not dialogue.strip() or not any((t.get("content") or "").strip() for t in short_term_turns):
        return old_summary or ""

    prompt = f"""다음은 보이스피싱 예방 롤플레잉 훈련의 일부 대화입니다.
기존 시나리오 요약(장기 메모리):
{old_summary or '(없음)'}

최근 대화:
{dialogue}

위 최근 대화를 반영해, "지금까지의 시나리오·사기 수법·사용자 반응"을 2~4문장으로 요약해 주세요. 기존 요약이 있으면 자연스럽게 이어가고, 없으면 새로 작성하세요. 한국어로만 출력하고 설명은 붙이지 마세요."""

    try:
        msg = anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = ""
        for block in msg.content:
            if getattr(block, "type", None) == "text":
                text = (getattr(block, "text", None) or "").strip()
                break
        return text if text else old_summary
    except Exception as e:
        logger.warning("update_long_term_summary 실패, 기존 요약 유지: %s", e)
        return old_summary or ""
