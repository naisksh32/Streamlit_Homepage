# 공용 RAG 도구: 보이스피싱·금융사기 뉴스 사례 검색
# Roleplaying, Guardian 등 여러 에이전트가 동일 도구 사용. RAG는 여기 한 곳에만 연결.

from typing import Any


def search_voice_phishing_cases(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """
    매일경제 뉴스 기반 보이스피싱·금융사기 사례를 검색합니다.
    Roleplaying(대사 생성), Guardian(위험 설명) 등에서 공통 사용.

    Args:
        query: 검색할 키워드/상황 설명 (예: "카드사 개인정보 유출", "정부 지원금")
        top_k: 반환할 문서 개수 (기본 3)

    Returns:
        list[dict]: 각 항목은 { "headline", "snippet", "source", "date" } 등
    """
    # TODO: ChromaDB 등 벡터 DB에서 query로 검색 후 top_k개 반환
    # RAG 연동 시 이 함수 내부만 구현하면 Roleplaying·Guardian 모두 자동 반영
    _ = query, top_k
    return [
        {
            "headline": "[RAG 미구축] 검색 결과는 데이터 수집·벡터 DB 구축 후 연동됩니다.",
            "snippet": "보이스피싱, 스미싱, 투자 사기 등 매일경제 뉴스 기반 사례가 여기에 채워집니다.",
            "source": "ChromaDB (예정)",
            "date": None,
        }
    ]


def format_rag_result_for_llm(results: list[dict[str, Any]]) -> str:
    """RAG 검색 결과를 LLM에 넘길 텍스트로 포맷. 에이전트 공통 사용."""
    if not results:
        return "검색 결과가 없습니다."
    return "\n\n".join(
        f"[{i+1}] {r.get('headline','')}\n{r.get('snippet','')}"
        for i, r in enumerate(results)
    )


# Anthropic tools 형식. Roleplaying/Guardian 등에서 동일 스키마 사용
RAG_TOOL_DEFINITION = {
    "name": "search_voice_phishing_cases",
    "description": "매일경제 뉴스에 보도된 보이스피싱·금융사기 사례를 검색합니다. 대사/설명 생성 전에 이 도구로 최신 수법을 참고하세요.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "검색 키워드 또는 상황 설명 (예: 카드사 개인정보 유출, 정부 지원금 사기)",
            },
            "top_k": {
                "type": "integer",
                "description": "가져올 문서 개수",
                "default": 3,
            },
        },
        "required": ["query"],
    },
}
