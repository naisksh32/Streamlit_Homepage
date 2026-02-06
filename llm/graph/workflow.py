# VoiceGuardian LangGraph 워크플로우
# 멀티 에이전트 시스템의 StateGraph 정의

from langgraph.graph import StateGraph, END

from .state import VoiceGuardianState
from ..agents.master import master_node, route_from_master
from ..agents.roleplay_agent import roleplay_node
from ..agents.evaluator import evaluate_node, route_from_evaluator
from ..agents.guardian import guardian_node
from ..agents.topic_selection import topic_selection_node


def create_workflow() -> StateGraph:
    """
    VoiceGuardian 워크플로우를 생성합니다.
    
    워크플로우 흐름:
    
    ```
                        ┌─────────────────────────────────────┐
                        │                                     │
                        v                                     │
    [START] ──> [master] ──> [topic_selection] ──> (user) ──>─┘
                   │                                    
                   │ (topic 있음)                       
                   v                                    
              [roleplay] ──> [evaluate] ──┬──> [roleplay] (safe)
                   ^                      │
                   │                      v
                   └──── [guardian] <─────┘ (danger)
    ```
    
    1. master: 현재 상태 분석 및 하위 에이전트 지시 생성
    2. topic_selection: 시나리오 주제 선택 (선택적)
    3. roleplay: 보이스피싱범 역할 대사 생성
    4. evaluate: 사용자 응답 평가 (개인정보 노출 여부)
    5. guardian: 위험 상황 시 교육 메시지 제공
    
    Returns:
        컴파일되지 않은 StateGraph 인스턴스
    """
    # StateGraph 생성
    workflow = StateGraph(VoiceGuardianState)
    
    # 노드 추가
    workflow.add_node("master", master_node)
    workflow.add_node("topic_selection", topic_selection_node)
    workflow.add_node("roleplay", roleplay_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("guardian", guardian_node)
    
    # 진입점 설정
    workflow.set_entry_point("master")
    
    # Master에서 조건부 라우팅
    workflow.add_conditional_edges(
        "master",
        route_from_master,
        {
            "topic_selection": "topic_selection",
            "roleplay": "roleplay",
            "evaluate": "evaluate",
            "guardian": "guardian",
            "__end__": END,
        }
    )
    
    # Topic Selection → END (사용자 입력 대기)
    workflow.add_edge("topic_selection", END)
    
    # Roleplay → END (사용자 입력 대기)
    workflow.add_edge("roleplay", END)
    
    # Evaluate에서 조건부 라우팅 (safe/danger)
    workflow.add_conditional_edges(
        "evaluate",
        route_from_evaluator,
        {
            "roleplay": "roleplay",
            "guardian": "guardian",
        }
    )
    
    # Guardian → END (사용자 입력 대기)
    workflow.add_edge("guardian", END)
    
    return workflow


def compile_workflow():
    """
    워크플로우를 컴파일하여 실행 가능한 앱을 반환합니다.
    
    Returns:
        컴파일된 LangGraph 앱
    """
    workflow = create_workflow()
    return workflow.compile()


# 기본 컴파일된 앱 (import 시 바로 사용 가능)
app = compile_workflow()


def get_initial_state(
    scenario_topic: str = "",
    user_input: str = ""
) -> VoiceGuardianState:
    """
    초기 상태를 생성합니다.
    
    Args:
        scenario_topic: 시나리오 주제 (빈 문자열이면 대화형 선택)
        user_input: 초기 사용자 입력 (선택)
        
    Returns:
        초기 VoiceGuardianState
    """
    return {
        "messages": [],
        "current_phase": "init",
        "evaluation_result": None,
        "scenario_topic": scenario_topic,
        "turn_count": 0,
        "user_input": user_input,
        "master_instruction": "",
        "long_term_summary": "",
        "needs_topic_selection": not bool(scenario_topic),
    }


def run_single_turn(
    state: VoiceGuardianState,
    user_input: str = ""
) -> VoiceGuardianState:
    """
    단일 턴을 실행합니다.
    
    사용자 입력이 있으면 state에 추가하고 워크플로우를 실행합니다.
    
    Args:
        state: 현재 상태
        user_input: 사용자 입력
        
    Returns:
        업데이트된 상태
    """
    if user_input:
        state = {**state, "user_input": user_input}
    
    result = app.invoke(state)
    return result
