# Topic Selection Node: 시나리오 주제 선택
# Master Agent가 생성한 질문을 사용자에게 전달

from langchain_core.messages import AIMessage

from ..graph.state import VoiceGuardianState


def topic_selection_node(state: VoiceGuardianState) -> dict:
    """
    시나리오 주제 선택 노드
    
    Master Agent가 생성한 질문을 메시지로 추가합니다.
    (사용자가 응답하면 Master가 파싱하여 scenario_topic 설정)
    
    Args:
        state: 현재 공유 상태
        
    Returns:
        업데이트할 상태 딕셔너리
    """
    master_instruction = state.get("master_instruction", "")
    
    # Master의 지시가 곧 사용자에게 보여줄 질문
    if not master_instruction:
        master_instruction = "안녕하세요! 어떤 보이스피싱 유형에 대해 훈련하고 싶으신가요? (예: 카드사 사칭, 검찰 사칭, 대출 사기 등)"
    
    return {
        "messages": [AIMessage(content=master_instruction)],
        "needs_topic_selection": False,  # 질문 완료
    }
