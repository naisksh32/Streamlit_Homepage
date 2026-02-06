# VoiceGuardian 공유 상태 정의
# 모든 에이전트가 공유하는 State 타입

from typing import TypedDict, Literal, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class EvaluationResult(TypedDict):
    """Evaluator Agent의 평가 결과"""
    is_danger: bool           # 위험 여부 (개인정보 노출 등)
    reason: str               # 판단 이유
    detected_info: list[str]  # 감지된 민감 정보 목록


class VoiceGuardianState(TypedDict):
    """
    VoiceGuardian 멀티 에이전트 시스템의 공유 상태
    
    Attributes:
        messages: 대화 이력 (LangGraph add_messages reducer 사용)
        current_phase: 현재 진행 단계
        evaluation_result: Evaluator Agent의 평가 결과
        scenario_topic: 현재 시나리오 주제 (예: "카드사 정보 유출", "정부 지원금")
        turn_count: 현재 대화 턴 수
        user_input: 사용자의 최신 입력
        master_instruction: Master Agent가 하위 에이전트에게 내리는 지시
        long_term_summary: 장기 메모리 (10턴 이상 대화 요약)
        needs_topic_selection: 시나리오 주제 선택이 필요한지 여부
    """
    messages: Annotated[list[BaseMessage], add_messages]
    current_phase: Literal["init", "topic_selection", "roleplay", "evaluate", "guardian", "end"]
    evaluation_result: EvaluationResult | None
    scenario_topic: str
    turn_count: int
    user_input: str
    master_instruction: str
    long_term_summary: str
    needs_topic_selection: bool
