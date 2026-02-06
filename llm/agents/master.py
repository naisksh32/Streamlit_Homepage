# Master Agent: 대화 흐름 총괄 및 하위 에이전트 지시
# LLM을 사용하여 상황 분석 및 자연어 지시 생성
#
# ============================================================================
# LangGraph 노드 vs 엣지 개념 설명
# ============================================================================
#
# [노드 (Node)] - master_node 함수
#   - 상태(state)를 받아서 업데이트된 상태를 반환
#   - 실제 작업 수행 (LLM 호출, 데이터 처리 등)
#   - 반환값이 기존 state에 merge됨
#
# [엣지 (Edge)] - route_from_master 함수  
#   - 상태(state)를 읽고 다음 노드 이름을 반환
#   - 상태를 수정하지 않음 (읽기 전용)
#   - 그래프의 흐름을 결정하는 라우팅 역할
#
# 실행 순서: 노드 실행 → 엣지로 다음 노드 결정 → 다음 노드 실행 → ...
# ============================================================================

from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from ..graph.state import VoiceGuardianState
from ..utils.llm import get_master_llm
from ..utils.memory import build_context_for_llm, get_short_term_messages


# Master Agent 시스템 프롬프트
MASTER_SYSTEM_PROMPT = """당신은 보이스피싱 예방 훈련 시스템의 **Master Agent**입니다.

## 역할
- 전체 훈련 흐름을 관리하고, 하위 에이전트(Roleplay, Evaluator, Guardian)에게 지시를 내립니다.
- 직접 사용자와 대화하지 않고, 하위 에이전트를 통해 소통합니다.
- 단, 시나리오 주제 선택 시에만 사용자에게 직접 질문합니다.

## 현재 상태
- 진행 단계: {current_phase}
- 시나리오 주제: {scenario_topic}
- 현재 턴: {turn_count}

## 대화 컨텍스트
{conversation_context}

## 작업
{task_description}

## 출력 형식
지시 내용만 간결하게 출력하세요. 설명이나 접두사 없이 지시문만 작성합니다.
"""


# 작업별 설명
TASK_DESCRIPTIONS = {
    "topic_selection": """사용자에게 훈련하고 싶은 보이스피싱 시나리오 유형을 물어보세요.
친절하고 자연스럽게 질문하세요. 예시 유형도 몇 가지 제시해주세요.
(예: 카드사 사칭, 정부기관 사칭, 대출 사기, 택배 사칭 등)""",
    
    "parse_topic": """사용자의 응답에서 원하는 시나리오 유형을 파악하세요.
파악한 시나리오 주제만 간결하게 출력하세요. (예: "검찰 사칭", "카드사 정보 유출")
만약 명확하지 않으면 "일반 보이스피싱"으로 설정하세요.""",
    
    "start_roleplay": """Roleplay Agent에게 시나리오 시작을 지시하세요.
뉴스 데이터를 참고하여 {scenario_topic} 시나리오로 롤플레이를 시작하라고 지시하세요.""",
    
    "continue_roleplay": """Roleplay Agent에게 대화 계속을 지시하세요.
사용자의 응답을 고려하여 자연스럽게 대화를 이어가라고 지시하세요.
사용자가 의심하면 더 설득력 있게, 거절하면 다른 방식으로 접근하라고 지시하세요.""",
    
    "after_guardian": """Guardian Agent의 교육이 끝났습니다.
Roleplay Agent에게 새로운 시나리오나 다른 상황으로 훈련을 계속하라고 지시하세요.""",
}


def master_node(state: VoiceGuardianState) -> dict:
    """
    Master Agent 노드 (Node)
    
    현재 상태를 분석하여:
    1. 다음 단계를 결정
    2. 하위 에이전트에게 전달할 지시를 LLM으로 생성
    
    Args:
        state: 현재 공유 상태
        
    Returns:
        업데이트할 상태 딕셔너리
    """
    current_phase = state.get("current_phase", "init")
    scenario_topic = state.get("scenario_topic", "")
    turn_count = state.get("turn_count", 0)
    user_input = state.get("user_input", "")
    needs_topic_selection = state.get("needs_topic_selection", False)
    messages = state.get("messages", [])
    long_term_summary = state.get("long_term_summary", "")
    
    # 대화 컨텍스트 구성
    short_term = get_short_term_messages(messages)
    conversation_context = build_context_for_llm(short_term, long_term_summary)
    
    # ========================================
    # 단계별 처리
    # ========================================
    
    # 1. 초기 상태: 시나리오 주제 확인
    if current_phase == "init":
        if scenario_topic:
            # 주제가 이미 있음 (CLI로 전달됨) → 롤플레이 시작
            return _generate_instruction(
                state, "start_roleplay",
                next_phase="roleplay",
                conversation_context=conversation_context,
            )
        else:
            # 주제 없음 → 사용자에게 질문
            return _generate_instruction(
                state, "topic_selection",
                next_phase="topic_selection",
                conversation_context=conversation_context,
            )
    
    # 2. 주제 선택 단계: 사용자 응답 파싱
    if current_phase == "topic_selection" and user_input:
        # 사용자 응답에서 주제 추출
        parsed_topic = _parse_topic_from_input(user_input, conversation_context)
        return {
            "scenario_topic": parsed_topic,
            "current_phase": "roleplay",
            "master_instruction": f"뉴스 데이터를 참고하여 '{parsed_topic}' 시나리오로 보이스피싱 롤플레이를 시작해. 사기범 역할로 첫 대사를 생성해.",
            "user_input": "",  # 입력 소비
        }
    
    # 3. Guardian 후 복귀
    if current_phase == "guardian":
        return _generate_instruction(
            state, "after_guardian",
            next_phase="roleplay",
            conversation_context=conversation_context,
        )
    
    # 4. 롤플레이 진행 중: 사용자 응답이 있으면 평가로
    if current_phase == "roleplay" and user_input:
        return {
            "current_phase": "evaluate",
            "master_instruction": "사용자의 응답을 평가해. 개인정보 노출 여부를 확인해.",
        }
    
    # 5. 평가 후 롤플레이 계속
    if current_phase == "evaluate":
        return _generate_instruction(
            state, "continue_roleplay",
            next_phase="roleplay",
            conversation_context=conversation_context,
        )
    
    # 기본: 현재 상태 유지
    return {}


def _generate_instruction(
    state: VoiceGuardianState,
    task_key: str,
    next_phase: str,
    conversation_context: str,
) -> dict:
    """LLM을 사용하여 하위 에이전트 지시 생성"""
    scenario_topic = state.get("scenario_topic", "")
    turn_count = state.get("turn_count", 0)
    current_phase = state.get("current_phase", "init")
    
    task_description = TASK_DESCRIPTIONS.get(task_key, "")
    if "{scenario_topic}" in task_description:
        task_description = task_description.format(scenario_topic=scenario_topic or "보이스피싱")
    
    prompt = MASTER_SYSTEM_PROMPT.format(
        current_phase=current_phase,
        scenario_topic=scenario_topic or "(미선택)",
        turn_count=turn_count,
        conversation_context=conversation_context or "(대화 시작)",
        task_description=task_description,
    )
    
    try:
        llm = get_master_llm()
        response = llm.invoke(prompt)
        instruction = response.content.strip()
    except Exception as e:
        # LLM 실패 시 기본 지시
        instruction = f"[기본 지시] {task_key} 단계를 진행해주세요."
    
    return {
        "current_phase": next_phase,
        "master_instruction": instruction,
    }


def _parse_topic_from_input(user_input: str, conversation_context: str) -> str:
    """사용자 입력에서 시나리오 주제 추출"""
    prompt = f"""사용자가 보이스피싱 훈련에서 원하는 시나리오 유형을 말했습니다.

사용자 입력: "{user_input}"

이 입력에서 시나리오 주제를 추출하세요.
예시: "검찰 사칭", "카드사 정보 유출", "대출 사기", "정부 지원금 사기" 등
명확하지 않으면 "일반 보이스피싱"으로 설정하세요.

주제만 간결하게 출력하세요:"""
    
    try:
        llm = get_master_llm()
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception:
        return "일반 보이스피싱"


def route_from_master(state: VoiceGuardianState) -> Literal["roleplay", "evaluate", "guardian", "topic_selection", "__end__"]:
    """
    Master에서 다음 노드로 라우팅 (Edge)
    
    ※ 이 함수는 상태를 수정하지 않고, 다음 노드 이름만 반환합니다.
    
    Args:
        state: 현재 공유 상태
        
    Returns:
        다음 노드 이름
    """
    current_phase = state.get("current_phase", "init")
    turn_count = state.get("turn_count", 0)
    
    # 최대 턴 수 도달 시 종료 (무한 루프 방지)
    MAX_TURNS = 20
    if turn_count >= MAX_TURNS:
        return "__end__"
    
    # 현재 phase에 따라 라우팅
    if current_phase == "topic_selection":
        return "topic_selection"
    elif current_phase == "roleplay":
        return "roleplay"
    elif current_phase == "evaluate":
        return "evaluate"
    elif current_phase == "guardian":
        return "guardian"
    
    # 기본: 롤플레이
    return "roleplay"
