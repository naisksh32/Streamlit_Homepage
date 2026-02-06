# Roleplaying Agent: Supervisor(Master)가 호출하는 하위 에이전트
# Claude API + 공용 RAG 도구 + 메모리(단기 10턴 / 장기 요약)

import os
from typing import Any

from anthropic import Anthropic

from ...tools.voice_phishing_rag import (
    RAG_TOOL_DEFINITION,
    format_rag_result_for_llm,
    search_voice_phishing_cases,
)

from .memory import build_memory
from .prompts import ROLEPLAYING_SYSTEM_PROMPT, format_supervisor_instruction

# 환경변수 ANTHROPIC_API_KEY 사용 (없으면 에러)
def _get_client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
    return Anthropic(api_key=api_key)


def _execute_tool(name: str, arguments: dict[str, Any]) -> str:
    """도구 실행 후 Claude에 넘길 텍스트 반환. RAG는 공용 도구(voice_phishing_rag) 사용."""
    if name == "search_voice_phishing_cases":
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 3)
        results = search_voice_phishing_cases(query=query, top_k=top_k)
        return format_rag_result_for_llm(results)
    return "알 수 없는 도구입니다."


def run_roleplaying_agent(
    instruction: str,
    conversation_history: list[dict[str, str]] | None = None,
    memory: dict[str, Any] | None = None,
    scenario_topic: str | None = None,
    *,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 512,
) -> str:
    """
    Supervisor(Master Agent)가 호출하는 진입점.
    지시에 따라 보이스피싱 롤플레잉 대사 한 턴을 생성합니다.

    Args:
        instruction: Supervisor의 지시 (예: "뉴스 데이터를 참고하여 최근 유행하는 보이스피싱 사기상황 롤플레잉을 시작해")
        conversation_history: 지금까지의 대화 (memory 미사용 시 사용, 하위 호환)
        memory: { "short_term": 최근 10턴, "long_term_summary": 시나리오 요약 }. None이면 conversation_history로부터 생성
        scenario_topic: 선택. 시나리오 힌트 (예: "카드사 유출", "정부 지원금")
        model: Claude 모델명
        max_tokens: 최대 출력 토큰

    Returns:
        사기범 역할의 대사 한 턴 (문자열). 설명/접두사 없이 대사만 반환합니다.
    """
    if memory is not None:
        short_term = memory.get("short_term") or []
        long_term_summary = memory.get("long_term_summary") or ""
    else:
        history = conversation_history or []
        mem = build_memory(conversation_history=history, long_term_summary="")
        short_term = mem["short_term"]
        long_term_summary = mem["long_term_summary"]

    user_content = format_supervisor_instruction(
        instruction,
        short_term=short_term,
        long_term_summary=long_term_summary,
    )
    if scenario_topic:
        user_content = f"[시나리오 힌트: {scenario_topic}]\n\n" + user_content

    client = _get_client()
    tools = [RAG_TOOL_DEFINITION]
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_content}]
    max_tool_rounds = 5  # 도구 연속 호출 상한 (무한 루프 방지)

    for _ in range(max_tool_rounds):
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=ROLEPLAYING_SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        # tool_use가 없으면 텍스트 블록이 최종 대사
        has_tool_use = any(getattr(b, "type", None) == "tool_use" for b in response.content)
        if not has_tool_use:
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    return (getattr(block, "text", None) or "").strip()
            return ""

        # tool_use 처리 후 tool_result를 user 메시지로 보내 재요청
        tool_results: list[dict[str, Any]] = []
        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                tool_id = getattr(block, "id", "_placeholder_")
                name = getattr(block, "name", "")
                args = getattr(block, "input", {}) or {}
                content = _execute_tool(name, args)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": content,
                })

        messages = messages + [
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": tool_results},
        ]

    # max_tool_rounds 초과 시 마지막 응답에서 텍스트 추출 시도, 없으면 빈 문자열
    for block in response.content:
        if getattr(block, "type", None) == "text":
            return (getattr(block, "text", None) or "").strip()
    return ""
