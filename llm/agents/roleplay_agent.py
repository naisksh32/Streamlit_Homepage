# Roleplaying Agent: 보이스피싱범 역할 연기
# Master Agent의 지시를 받아 매일경제 뉴스 기반 사기범 대사 생성

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..graph.state import VoiceGuardianState
from ..utils.llm import get_roleplay_llm
from ..utils.memory import get_short_term_messages, update_memory, build_context_for_llm
from ..tools.voice_phishing_rag import search_voice_phishing_cases, format_rag_result_for_llm


# 시스템 프롬프트
ROLEPLAYING_SYSTEM_PROMPT = """당신은 **보이스피싱 예방 훈련용 롤플레잉 에이전트**입니다.

## 역할
- 매일경제 뉴스에 보도된 실제 보이스피싱·금융사기 사례를 바탕으로 **사기범 역할**을 연기합니다.
- 사용자(어르신)가 실전처럼 대화하며 사기 탐지 능력을 키우는 것이 목표입니다.

## Master Agent 지시
{master_instruction}

## 대사 생성 원칙
1. **RAG 참고**: 제공된 뉴스 사례를 참고하여, 최신 수법(카드사 정보 유출, 정부 지원금 빙자, 대출 사기 등)에 맞는 구체적인 대사를 생성하세요.
2. **한 번에 한 턴**: 사용자에게 보여줄 **사기범의 한 마디**만 생성합니다. 문장 하나~몇 문장으로 끝내세요.
3. **인간적 반응**: 사용자가 의심하거나 거절하면, 더 강압적으로 말하거나 회유·위로·긴급감 조성 등 자연스러운 반응을 보이세요.
4. **예방 목적 유지**: 실제로 사용자를 속이려 하지 말고, "훈련용 시나리오"라는 전제를 지키며 대사를 만듭니다. 실제 계좌번호·비밀번호 요구 문구는 사용하지 마세요.

## 시나리오 정보
- 주제: {scenario_topic}
- 현재 턴: {turn_count}

## 참고 뉴스 사례
{news_context}

## 대화 컨텍스트
{conversation_context}

## 출력 형식
- **오직 사기범의 대사만** 출력하세요. 설명, 괄호, "사기범:", "AI:" 등의 접두사 없이 대사 내용만 출력합니다.
- 한국어로, 전화/보이스피싱 상황에 맞는 말투(친절·위기감·서두름 등)를 사용하세요.
"""


def _get_news_context(scenario_topic: str) -> str:
    """RAG로 관련 뉴스 사례 검색"""
    if not scenario_topic:
        scenario_topic = "보이스피싱 최신 수법"
    
    results = search_voice_phishing_cases(query=scenario_topic, top_k=3)
    return format_rag_result_for_llm(results)


def roleplay_node(state: VoiceGuardianState) -> dict:
    """
    Roleplaying Agent 노드
    
    Master Agent의 지시를 받아 보이스피싱범 역할의 대사를 생성합니다.
    
    Args:
        state: 현재 공유 상태
        
    Returns:
        업데이트할 상태 딕셔너리 (messages, turn_count, long_term_summary 등)
    """
    scenario_topic = state.get("scenario_topic", "일반 보이스피싱")
    messages = state.get("messages", [])
    turn_count = state.get("turn_count", 0)
    user_input = state.get("user_input", "")
    master_instruction = state.get("master_instruction", "롤플레이를 진행해주세요.")
    long_term_summary = state.get("long_term_summary", "")
    
    # 사용자 입력이 있으면 메시지에 추가
    if user_input:
        messages = list(messages) + [HumanMessage(content=user_input)]
    
    # 메모리 업데이트 (5턴마다 요약)
    short_term_messages, new_summary = update_memory(
        messages=messages,
        turn_count=turn_count,
        existing_summary=long_term_summary,
    )
    
    # 뉴스 컨텍스트 가져오기
    news_context = _get_news_context(scenario_topic)
    
    # 대화 컨텍스트 구성
    conversation_context = build_context_for_llm(short_term_messages, new_summary)
    
    # 프롬프트 구성
    system_prompt = ROLEPLAYING_SYSTEM_PROMPT.format(
        master_instruction=master_instruction,
        scenario_topic=scenario_topic,
        turn_count=turn_count,
        news_context=news_context,
        conversation_context=conversation_context,
    )
    
    # LLM 호출 (Anthropic API는 최소 1개의 user message 필요)
    llm = get_roleplay_llm()
    
    # 첫 턴이면 시작 트리거 메시지 추가
    if not user_input and turn_count == 0:
        trigger_message = HumanMessage(content="시나리오를 시작해주세요.")
    elif user_input:
        trigger_message = HumanMessage(content=user_input)
    else:
        trigger_message = HumanMessage(content="대화를 계속해주세요.")
    
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        trigger_message
    ])
    
    # 새 메시지 구성
    new_messages = []
    if user_input:
        new_messages.append(HumanMessage(content=user_input))
    new_messages.append(AIMessage(content=response.content.strip()))
    
    return {
        "messages": new_messages,
        "turn_count": turn_count + 1,
        "current_phase": "evaluate",  # 다음은 평가 단계
        "user_input": "",  # 입력 소비 완료
        "long_term_summary": new_summary,
    }
