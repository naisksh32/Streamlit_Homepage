# src/tools — 공용 도구

Roleplaying, Guardian 등 **여러 에이전트가 공통으로 사용하는 도구**를 py 파일로 관리하는 폴더입니다.

- **voice_phishing_rag.py**: 피해사례 RAG (보이스피싱·금융사기 뉴스 검색). RAG(ChromaDB 등)는 이 모듈 한 곳에만 연결하면 됨.
- 새 도구 추가 시 이 폴더에 모듈을 추가하고 `__init__.py`의 `__all__`에 노출하면 에이전트에서 `from src.tools import ...` 또는 `from ...tools.xxx import ...` 로 사용 가능.
