# Evaluator Agent: 사용자 응답 평가
# 개인정보 노출 여부를 판별하고 JSON 형식으로 결과 반환
#
# ============================================================================
# TODO: 다른 담당자가 구현할 부분
# ============================================================================
# 
# 구현 요구사항:
# 1. 사용자의 응답에서 개인정보 노출 여부를 평가
# 2. 1차: 정규표현식으로 숫자 패턴 검사 (주민등록번호, 계좌번호, 전화번호 등)
# 3. 2차: LLM으로 문맥 검사 (감정적 약점 노출, 암묵적 동의 등)
# 4. with_structured_output()을 사용하여 JSON 응답 보장
#
# 반환해야 할 evaluation_result 형식:
# {
#     "is_danger": bool,        # 위험 여부
#     "reason": str,            # 판단 이유
#     "detected_info": list[str]  # 감지된 민감 정보 목록
# }
#
# 참고 코드 (langchain structured output):
# from pydantic import BaseModel
# class EvaluationOutput(BaseModel):
#     is_danger: bool
#     reason: str
#     detected_info: list[str]
#
# llm_with_structure = llm.with_structured_output(EvaluationOutput)
# ============================================================================

from typing import Literal
from langchain_core.messages import HumanMessage

from ..graph.state import VoiceGuardianState, EvaluationResult


def evaluate_node(state: VoiceGuardianState) -> dict:
    """
    Evaluator Agent 노드 (스켈레톤)
    
    사용자의 응답을 평가하여 개인정보 노출 여부를 판별합니다.
    
    Args:
        state: 현재 공유 상태
        
    Returns:
        업데이트할 상태 딕셔너리 (evaluation_result 포함)
        
    TODO: 실제 평가 로직 구현 필요
    - 정규표현식 검사 (주민번호, 계좌번호 패턴)
    - LLM 문맥 검사 (감정적 약점, 암묵적 동의)
    - with_structured_output() 활용
    """
    messages = state.get("messages", [])
    
    # 마지막 사용자 메시지 찾기
    user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break
    
    # ========================================
    # TODO: 여기에 실제 평가 로직 구현
    # ========================================
    # 
    # 예시 구현 흐름:
    # 1. regex_check = check_regex_patterns(user_message)
    # 2. if regex_check.detected:
    #        return danger_result(regex_check)
    # 3. llm_check = check_with_llm(user_message, messages)
    # 4. return llm_check
    #
    # ========================================
    
    # 임시 구현: 항상 안전으로 판정 (실제 구현 시 교체)
    evaluation_result: EvaluationResult = {
        "is_danger": False,
        "reason": "[스켈레톤] 실제 평가 로직 미구현 - 항상 안전 판정",
        "detected_info": [],
    }
    
    return {
        "evaluation_result": evaluation_result,
    }


def route_from_evaluator(state: VoiceGuardianState) -> Literal["roleplay", "guardian"]:
    """
    Evaluator에서 다음 노드로 라우팅
    
    - is_danger=True → guardian (위험 상황 개입)
    - is_danger=False → roleplay (정상 진행)
    
    Args:
        state: 현재 공유 상태
        
    Returns:
        다음 노드 이름
    """
    evaluation_result = state.get("evaluation_result")
    
    if evaluation_result and evaluation_result.get("is_danger", False):
        return "guardian"
    
    return "roleplay"
