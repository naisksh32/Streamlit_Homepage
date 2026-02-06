# LLM 설정 유틸리티
# 에이전트별 ChatAnthropic 인스턴스 관리 (싱글톤 패턴)

import os
from langchain_anthropic import ChatAnthropic
import streamlit as st
from dotenv import load_dotenv


# ============================================================================
# 전역 LLM 인스턴스 (싱글톤)
# - 인스턴스 생성은 Python 객체 생성일 뿐, API 호출 비용 없음
# - 실제 비용은 invoke() 호출 시에만 발생
# ============================================================================

_master_llm: ChatAnthropic | None = None
_roleplay_llm: ChatAnthropic | None = None
_evaluation_llm: ChatAnthropic | None = None
_guardian_llm: ChatAnthropic | None = None
_summary_llm: ChatAnthropic | None = None


def _check_api_key() -> str:
    """API 키 확인"""
    load_dotenv()
    try:
        api_key = st.secrets["general"]["ANTHROPIC_API_KEY"] # [general] 섹션 아래에 뒀을 경우
    # 만약 섹션 없이 바로 API_KEY = "..." 라고 썼다면 st.secrets["API_KEY"] 로 접근
    except FileNotFoundError:
        print("Secrets 파일을 찾을 수 없습니다.")
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다. "
            ".env 파일에 설정하거나 환경변수로 지정해주세요."
        )
    return api_key


def get_master_llm() -> ChatAnthropic:
    """
    Master Agent용 LLM
    - 상황 분석 및 하위 에이전트 지시 생성
    - temperature=0.3 (일관된 판단 + 약간의 유연성)
    """
    global _master_llm
    if _master_llm is None:
        _master_llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0.3,
            max_tokens=512,
            api_key=_check_api_key(),
        )
    return _master_llm


def get_roleplay_llm() -> ChatAnthropic:
    """
    Roleplaying Agent용 LLM
    - 보이스피싱범 역할 대사 생성
    - temperature=0.8 (자연스럽고 다양한 대화)
    """
    global _roleplay_llm
    if _roleplay_llm is None:
        _roleplay_llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0.8,
            max_tokens=512,
            api_key=_check_api_key(),
        )
    return _roleplay_llm


def get_evaluation_llm() -> ChatAnthropic:
    """
    Evaluator Agent용 LLM
    - 사용자 응답 평가 (개인정보 노출 여부)
    - temperature=0.0 (일관된 판단, deterministic)
    """
    global _evaluation_llm
    if _evaluation_llm is None:
        _evaluation_llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0.0,
            max_tokens=512,
            api_key=_check_api_key(),
        )
    return _evaluation_llm


def get_guardian_llm() -> ChatAnthropic:
    """
    Guardian Agent용 LLM
    - 위험 상황 교육 메시지 생성
    - temperature=0.5 (신뢰성 있는 교육 + 자연스러운 표현)
    """
    global _guardian_llm
    if _guardian_llm is None:
        _guardian_llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0.5,
            max_tokens=1024,  # 교육 메시지는 더 길 수 있음
            api_key=_check_api_key(),
        )
    return _guardian_llm


def get_summary_llm() -> ChatAnthropic:
    """
    메모리 요약용 LLM
    - 대화 내용 요약
    - temperature=0.0 (일관된 요약)
    """
    global _summary_llm
    if _summary_llm is None:
        _summary_llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0.0,
            max_tokens=512,
            api_key=_check_api_key(),
        )
    return _summary_llm


# ============================================================================
# 하위 호환용 함수 (기존 코드 지원)
# ============================================================================

def get_llm(
    model: str = "claude-sonnet-4-20250514",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    **kwargs
) -> ChatAnthropic:
    """
    범용 LLM 인스턴스 생성 (싱글톤 아님, 매번 새로 생성)
    특별한 설정이 필요할 때 사용
    """
    return ChatAnthropic(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=_check_api_key(),
        **kwargs
    )


def get_llm_for_evaluation(**kwargs) -> ChatAnthropic:
    """하위 호환: get_evaluation_llm() 사용 권장"""
    return get_evaluation_llm()


def get_llm_for_roleplay(**kwargs) -> ChatAnthropic:
    """하위 호환: get_roleplay_llm() 사용 권장"""
    return get_roleplay_llm()
