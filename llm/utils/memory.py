# 메모리 관리 유틸리티
# 단기 메모리 (최근 10턴) + 장기 메모리 (5턴마다 요약)

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from .llm import get_summary_llm


# 설정값
SHORT_TERM_MAX_TURNS = 10  # 단기 메모리 최대 턴 수
SUMMARY_INTERVAL = 5       # 요약 주기 (5턴마다)


def get_short_term_messages(
    messages: list[BaseMessage],
    max_turns: int = SHORT_TERM_MAX_TURNS
) -> list[BaseMessage]:
    """
    단기 메모리: 최근 N턴의 메시지만 반환
    
    Args:
        messages: 전체 메시지 목록
        max_turns: 최대 턴 수 (기본 10)
        
    Returns:
        최근 max_turns * 2개의 메시지 (user + assistant = 1턴)
    """
    max_messages = max_turns * 2
    if len(messages) <= max_messages:
        return messages
    return messages[-max_messages:]


def should_summarize(turn_count: int) -> bool:
    """
    요약이 필요한지 확인
    
    5턴, 10턴, 15턴... 등 SUMMARY_INTERVAL 배수일 때 요약
    단, 첫 5턴은 요약 불필요 (단기 메모리로 충분)
    
    Args:
        turn_count: 현재 턴 수
        
    Returns:
        요약 필요 여부
    """
    return turn_count > 0 and turn_count % SUMMARY_INTERVAL == 0 and turn_count > SUMMARY_INTERVAL


def summarize_messages(
    messages: list[BaseMessage],
    existing_summary: str = ""
) -> str:
    """
    메시지들을 요약하여 장기 메모리 생성
    
    Args:
        messages: 요약할 메시지 목록
        existing_summary: 기존 장기 요약 (있으면 이어서 요약)
        
    Returns:
        새로운 장기 요약
    """
    if not messages:
        return existing_summary
    
    # 메시지를 텍스트로 변환
    dialogue_lines = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            dialogue_lines.append(f"사용자: {msg.content}")
        elif isinstance(msg, AIMessage):
            dialogue_lines.append(f"사기범: {msg.content}")
    
    dialogue_text = "\n".join(dialogue_lines)
    
    if not dialogue_text.strip():
        return existing_summary
    
    # 요약 프롬프트
    prompt = f"""다음은 보이스피싱 예방 훈련 롤플레이의 대화 내용입니다.

{f"기존 요약:{chr(10)}{existing_summary}{chr(10)}{chr(10)}" if existing_summary else ""}최근 대화:
{dialogue_text}

위 내용을 바탕으로 "지금까지의 시나리오 진행 상황, 사기범의 수법, 사용자의 대응"을 2~4문장으로 요약해주세요.
기존 요약이 있으면 자연스럽게 이어가고, 핵심 정보만 간결하게 정리하세요.
한국어로만 출력하고 설명은 붙이지 마세요."""
    
    try:
        llm = get_summary_llm()
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        # 요약 실패 시 기존 요약 유지
        print(f"[경고] 메모리 요약 실패: {e}")
        return existing_summary


def update_memory(
    messages: list[BaseMessage],
    turn_count: int,
    existing_summary: str = ""
) -> tuple[list[BaseMessage], str]:
    """
    메모리 업데이트: 단기 메모리 정리 + 필요시 장기 메모리 요약
    
    동작 방식:
    - 턴 1~10: 단기 메모리에 전체 보관 (요약 없음)
    - 턴 11 (=10+1): 1~5턴 요약 → 장기 메모리, 6~11턴은 단기 메모리
    - 턴 16: 기존 장기 + 6~10턴 요약, 11~16턴은 단기 메모리
    - ...
    
    Args:
        messages: 전체 메시지 목록
        turn_count: 현재 턴 수
        existing_summary: 기존 장기 요약
        
    Returns:
        (단기 메모리용 메시지, 새 장기 요약)
    """
    # 요약 필요 여부 확인
    if should_summarize(turn_count):
        # 요약할 메시지: 오래된 메시지들 (단기 메모리 범위 밖)
        short_term = get_short_term_messages(messages)
        messages_to_summarize = messages[:-len(short_term)] if len(messages) > len(short_term) else []
        
        if messages_to_summarize:
            new_summary = summarize_messages(messages_to_summarize, existing_summary)
            return short_term, new_summary
    
    # 요약 불필요: 단기 메모리만 정리
    short_term = get_short_term_messages(messages)
    return short_term, existing_summary


def build_context_for_llm(
    short_term_messages: list[BaseMessage],
    long_term_summary: str = ""
) -> str:
    """
    LLM에 전달할 컨텍스트 구성
    
    Args:
        short_term_messages: 단기 메모리 메시지
        long_term_summary: 장기 메모리 요약
        
    Returns:
        컨텍스트 문자열
    """
    parts = []
    
    if long_term_summary:
        parts.append(f"[이전 대화 요약]\n{long_term_summary}")
    
    if short_term_messages:
        dialogue_lines = []
        for msg in short_term_messages:
            if isinstance(msg, HumanMessage):
                dialogue_lines.append(f"사용자: {msg.content}")
            elif isinstance(msg, AIMessage):
                dialogue_lines.append(f"사기범: {msg.content}")
        
        if dialogue_lines:
            parts.append(f"[최근 대화]\n" + "\n".join(dialogue_lines))
    
    return "\n\n".join(parts) if parts else "(대화 시작)"
