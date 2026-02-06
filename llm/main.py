# VoiceGuardian 실행 진입점
# LangGraph 기반 보이스피싱 예방 훈련 시스템
#
# 사용법:
#   python -m src.main                      # 대화형 시나리오 선택
#   python -m src.main --topic 검찰사칭      # 특정 시나리오로 바로 시작
#   python -m src.main --demo               # 구조 확인 (API 키 불필요)

import os
import argparse
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

from .graph.workflow import app, get_initial_state, run_single_turn
from .graph.state import VoiceGuardianState


def print_message(msg, prefix: str = ""):
    """메시지 출력"""
    role = "🎭 사기범" if msg.type == "ai" else "👤 사용자"
    if prefix:
        role = prefix
    print(f"{role}: {msg.content}")
    print()


def run_interactive_session(scenario_topic: str = ""):
    """
    대화형 세션을 실행합니다.
    
    Args:
        scenario_topic: 시나리오 주제 (빈 문자열이면 대화형 선택)
    """
    print("=" * 60)
    print("🛡️  VoiceGuardian - 보이스피싱 예방 훈련")
    print("=" * 60)
    
    if scenario_topic:
        print(f"📋 시나리오: {scenario_topic}")
    else:
        print("📋 시나리오: 대화형 선택")
    
    print("💡 'quit' 또는 'q'를 입력하면 종료합니다.")
    print("=" * 60)
    print()
    
    # 초기 상태 생성 및 첫 턴 실행
    state = get_initial_state(scenario_topic=scenario_topic)
    state = run_single_turn(state)
    
    # 첫 메시지 출력
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        # topic_selection이면 시스템 질문으로 표시
        if state.get("current_phase") == "init" or not scenario_topic:
            print_message(last_msg, prefix="🤖 시스템")
        else:
            print_message(last_msg)
    
    # 대화 루프
    while True:
        try:
            user_input = input("👤 응답: ").strip()
            
            if user_input.lower() in ["quit", "q", "종료"]:
                print("\n훈련을 종료합니다. 수고하셨습니다! 🎉")
                break
            
            if not user_input:
                print("응답을 입력해주세요.")
                continue
            
            # 턴 실행
            state = run_single_turn(state, user_input=user_input)
            
            # 새 메시지 출력
            messages = state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                if last_msg.type == "ai":
                    # Guardian 메시지인지 확인 (교육 메시지)
                    if "⚠️" in last_msg.content or "위험" in last_msg.content:
                        print_message(last_msg, prefix="🛡️ 가디언")
                    else:
                        print_message(last_msg)
            
            # 시나리오 주제가 설정되었으면 표시
            current_topic = state.get("scenario_topic", "")
            if current_topic and not scenario_topic:
                print(f"[📋 시나리오 설정됨: {current_topic}]\n")
                scenario_topic = current_topic  # 이후 반복에서 다시 표시 안 함
            
            # 턴 수 확인
            turn_count = state.get("turn_count", 0)
            if turn_count >= 20:
                print("\n✅ 20턴 완료! 훈련이 종료되었습니다.")
                break
                
        except KeyboardInterrupt:
            print("\n\n훈련을 중단합니다.")
            break


def run_demo():
    """
    데모 실행 (API 키 없이 구조 확인용)
    """
    print("=" * 60)
    print("🧪 VoiceGuardian 구조 데모")
    print("=" * 60)
    
    # 초기 상태 출력
    state = get_initial_state(scenario_topic="정부 지원금 사기")
    print("\n📦 초기 상태:")
    print(f"  - current_phase: {state['current_phase']}")
    print(f"  - scenario_topic: {state['scenario_topic']}")
    print(f"  - turn_count: {state['turn_count']}")
    print(f"  - needs_topic_selection: {state['needs_topic_selection']}")
    
    print("\n📊 워크플로우 구조:")
    print("""
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
    """)
    
    print("🔧 노드 설명:")
    print("  - master: 대화 흐름 총괄 및 하위 에이전트 지시 (LLM 사용)")
    print("  - topic_selection: 시나리오 주제 선택 (선택적)")
    print("  - roleplay: 보이스피싱범 역할 대사 생성")
    print("  - evaluate: 사용자 응답 평가 (스켈레톤)")
    print("  - guardian: 위험 상황 교육 (스켈레톤)")
    
    print("\n📝 사용법:")
    print("  python -m src.main                    # 대화형 시나리오 선택")
    print("  python -m src.main --topic 검찰사칭    # 특정 시나리오로 시작")
    print("  python -m src.main --demo             # 이 데모 화면")
    
    print("\n✅ LangGraph 워크플로우가 정상적으로 구성되었습니다!")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="VoiceGuardian - 보이스피싱 예방 훈련 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python -m src.main                      대화형으로 시나리오 선택
  python -m src.main --topic 카드사사칭    '카드사 사칭' 시나리오로 시작
  python -m src.main --topic 정부지원금    '정부 지원금 사기' 시나리오로 시작
  python -m src.main --demo               구조 확인 (API 키 불필요)

지원하는 시나리오 예시:
  - 카드사사칭, 카드사정보유출
  - 검찰사칭, 경찰사칭, 정부기관사칭
  - 대출사기
  - 정부지원금, 정부지원금사기
  - 택배사칭
        """
    )
    
    parser.add_argument(
        "--topic", "-t",
        type=str,
        default="",
        help="시나리오 주제 (예: 검찰사칭, 대출사기, 정부지원금)"
    )
    
    parser.add_argument(
        "--demo",
        action="store_true",
        help="구조 확인 데모 실행 (API 키 불필요)"
    )
    
    args = parser.parse_args()
    
    # 데모 모드
    if args.demo:
        run_demo()
        return
    
    # API 키 확인
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 API 키를 설정하거나 --demo 옵션으로 구조만 확인하세요.")
        print("\n   예: python -m src.main --demo")
        print()
        run_demo()
        return
    
    # 시나리오 주제 정규화
    topic = args.topic.strip()
    
    # 대화형 세션 실행
    run_interactive_session(scenario_topic=topic)


if __name__ == "__main__":
    main()
