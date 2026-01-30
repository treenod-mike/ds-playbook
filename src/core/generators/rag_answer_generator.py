#!/usr/bin/env python3
"""
RAG 답변 생성 모듈 (Answer Generation with Evidence)

GraphRAG의 마지막 단계로, 검색된 청크와 그래프 관계를 기반으로
근거 기반 답변을 생성합니다.

핵심 기능:
1. Context Formatter: 검색 결과를 구조화된 XML 형식으로 포맷팅
2. Evidence-based Generation: LLM이 원본 청크를 근거로 답변 생성
3. Citation System: 각 답변에 출처 표기
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """검색 결과 데이터 구조"""
    chunk_id: Any  # UUID or int
    doc_id: Any  # TEXT or int
    doc_title: str
    content: str
    similarity: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GraphRelation:
    """그래프 관계 데이터 구조"""
    source: str
    predicate: str
    target: str
    confidence: float
    evidence: Optional[str] = None


class RAGContextFormatter:
    """검색 결과를 LLM 프롬프트용 구조화된 컨텍스트로 변환"""

    @staticmethod
    def format_vector_search_results(results: List[SearchResult]) -> str:
        """
        Vector Search 결과를 XML 구조로 포맷팅

        Args:
            results: 검색된 청크 목록

        Returns:
            XML 형식의 컨텍스트 문자열
        """
        if not results:
            return "<VectorSearchResults>\n  <Empty>검색 결과가 없습니다.</Empty>\n</VectorSearchResults>"

        context_parts = ["<VectorSearchResults>"]

        for idx, result in enumerate(results, 1):
            context_parts.append(f"""
  <Chunk id="chunk_{result.chunk_id}" rank="{idx}">
    <Source>
      <DocumentID>{result.doc_id}</DocumentID>
      <DocumentTitle>{result.doc_title}</DocumentTitle>
      <ChunkID>{result.chunk_id}</ChunkID>
    </Source>
    <Similarity>{result.similarity:.3f}</Similarity>
    <Content>
{result.content}
    </Content>
  </Chunk>""")

        context_parts.append("</VectorSearchResults>")
        return "\n".join(context_parts)

    @staticmethod
    def format_graph_relations(relations: List[GraphRelation], center_term: str) -> str:
        """
        Graph Traversal 결과를 XML 구조로 포맷팅

        Args:
            relations: 그래프 관계 목록
            center_term: 중심 용어

        Returns:
            XML 형식의 관계 그래프 문자열
        """
        if not relations:
            return f"<GraphRelations center=\"{center_term}\">\n  <Empty>관련 관계가 없습니다.</Empty>\n</GraphRelations>"

        context_parts = [f'<GraphRelations center="{center_term}">']

        for idx, rel in enumerate(relations, 1):
            evidence_xml = f"\n    <Evidence>{rel.evidence}</Evidence>" if rel.evidence else ""
            context_parts.append(f"""
  <Relation id="rel_{idx}">
    <Source>{rel.source}</Source>
    <Predicate>{rel.predicate}</Predicate>
    <Target>{rel.target}</Target>
    <Confidence>{rel.confidence:.2f}</Confidence>{evidence_xml}
  </Relation>""")

        context_parts.append("</GraphRelations>")
        return "\n".join(context_parts)

    @staticmethod
    def format_ontology_rules(rules: List[Dict[str, str]]) -> str:
        """
        온톨로지 룰을 XML 구조로 포맷팅

        Args:
            rules: 온톨로지 룰 목록

        Returns:
            XML 형식의 온톨로지 룰 문자열
        """
        if not rules:
            return "<OntologyRules>\n  <Empty>온톨로지 룰이 없습니다.</Empty>\n</OntologyRules>"

        context_parts = ["<OntologyRules>"]

        for idx, rule in enumerate(rules, 1):
            context_parts.append(f"""
  <Rule id="rule_{idx}">
    <Pattern>{rule['subject_type']} --[{rule['predicate']}]--> {rule['object_type']}</Pattern>
    <Description>{rule['description']}</Description>
  </Rule>""")

        context_parts.append("</OntologyRules>")
        return "\n".join(context_parts)

    @classmethod
    def build_full_context(
        cls,
        query: str,
        vector_results: List[SearchResult],
        graph_relations: List[GraphRelation],
        ontology_rules: List[Dict[str, str]],
        center_term: Optional[str] = None
    ) -> str:
        """
        전체 컨텍스트를 구조화된 형식으로 생성

        Args:
            query: 사용자 질문
            vector_results: Vector Search 결과
            graph_relations: Graph Traversal 결과
            ontology_rules: 온톨로지 룰
            center_term: 그래프 중심 용어

        Returns:
            완전한 XML 컨텍스트
        """
        context_parts = [
            f"<Context>",
            f"  <Query>{query}</Query>",
            "",
            cls.format_vector_search_results(vector_results),
            "",
            cls.format_graph_relations(graph_relations, center_term or "N/A"),
            "",
            cls.format_ontology_rules(ontology_rules),
            "</Context>"
        ]

        return "\n".join(context_parts)


class RAGAnswerGenerator:
    """근거 기반 답변 생성기 (Evidence-based Answer Generator)"""

    SYSTEM_PROMPT = """당신은 PokoPoko 게임의 **비즈니스 인텔리전스 분석가**입니다.

## 역할 (Role)
- 게임 기획 문서와 지식 그래프를 기반으로 정확하고 논리적인 분석 제공
- 비즈니스 의사결정에 필요한 인사이트 도출
- 데이터 기반의 객관적 답변 작성

## 제약 사항 (Constraints)

### 1. 근거 기반 답변 (Evidence-based)
- **반드시** 제공된 `<Context>` 내의 정보만 사용하십시오
- 외부 지식이나 추측을 사용하지 마십시오
- 컨텍스트에 없는 정보는 "현재 문서에서는 확인할 수 없습니다"라고 명시하십시오

### 2. 출처 표기 (Citation)
- 답변의 **각 주장**마다 반드시 근거를 표기하십시오
- 형식: `[Source: 문서제목]` 또는 `[Chunk: chunk_ID]`
- 예시: "동적 난이도 시스템은 유저 실력에 맞춰 조절됩니다. [Source: 155레벨 기획서]"

### 3. 인용 우선순위
1. **Vector Search 결과**: 직접적인 텍스트 증거 (최우선)
2. **Graph Relations**: 관계 기반 추론 (보조)
3. **Ontology Rules**: 패턴 기반 해석 (참고)

### 4. 관계 해석 규칙
- Graph Relations의 predicate는 온톨로지 룰과 매칭하여 의미 해석
- Confidence가 0.8 이상인 관계 우선 사용
- Evidence 필드가 있으면 함께 인용

## 답변 형식 (Format)

### 1. 구조
```markdown
## [질문 주제]

### 핵심 답변
[2-3문장으로 핵심 내용 요약, 각 문장마다 출처 표기]

### 상세 분석
[벡터 검색 결과 기반 상세 설명]
- 포인트 1 [Source: ...]
- 포인트 2 [Source: ...]

### 관계 분석 (선택적)
[그래프 관계가 있을 경우만 추가]
- 관계 1: A --[predicate]--> B [Confidence: 0.95]
- 관계 2: B --[predicate]--> C [Confidence: 0.90]

### 비즈니스 인사이트
[분석 결과의 실무 활용 방안]
```

### 2. 톤 (Tone)
- 전문적이고 객관적
- 명확하고 간결
- 단정적 표현 (확실한 근거가 있을 때)
- 조건부 표현 (추론이 필요할 때: "~로 추정됩니다", "~일 가능성이 있습니다")

### 3. 예시

**좋은 답변 ✅**
> 동적 난이도 시스템은 유저의 실력 수준에 맞춰 자동으로 조절됩니다. [Source: 155레벨 기획서] 이 시스템은 좌절감과 지루함을 최소화하여(relieves) 지속적인 몰입(Flow) 상태를 유지시킵니다. [Graph: 동적 난이도 --relieves--> 좌절, Confidence: 0.90]

**나쁜 답변 ❌**
> 동적 난이도 시스템은 일반적으로 게임에서 많이 사용됩니다. 유저 경험을 개선하는 것으로 알려져 있습니다.
> (문제점: 외부 지식 사용, 출처 미표기, 추상적 표현)

## 특수 케이스 처리

### 1. 컨텍스트 부족
```markdown
## 답변 불가

현재 제공된 문서에서는 "[질문 주제]"에 대한 충분한 정보를 찾을 수 없습니다.

**검색된 내용**:
- [관련성 있는 부분적 정보 요약]

**추가 검색 제안**:
- "[추천 검색어 1]"
- "[추천 검색어 2]"
```

### 2. 모순된 정보
```markdown
문서 간 불일치가 발견되었습니다:
- 문서 A: [내용] [Source: ...]
- 문서 B: [상반된 내용] [Source: ...]

→ 최신 문서 기준으로 "[결론]"이 유효합니다. [Source: ...]
```

### 3. 추론이 필요한 경우
```markdown
직접적인 기술은 없으나, 다음 관계로부터 추론 가능합니다:
1. A --[predicate]--> B [Confidence: 0.95] [Source: ...]
2. B --[predicate]--> C [Confidence: 0.90] [Source: ...]

→ 따라서 "A는 C에 간접적으로 영향을 미칠 가능성이 있습니다."
```

## 중요 원칙

1. **No Hallucination**: 컨텍스트에 없는 정보는 절대 생성하지 마십시오
2. **Always Cite**: 모든 사실적 진술에는 출처를 표기하십시오
3. **Be Honest**: 모르면 모른다고 명확히 말하십시오
4. **Prioritize Evidence**: 벡터 검색 결과 > 그래프 관계 > 온톨로지 룰 순으로 우선순위
5. **Business Focus**: 실무 활용 가능한 인사이트 도출
"""

    def __init__(self, openai_client):
        """
        초기화

        Args:
            openai_client: OpenAI 클라이언트 인스턴스
        """
        self.openai_client = openai_client
        self.formatter = RAGContextFormatter()

    def generate_answer(
        self,
        query: str,
        vector_results: List[SearchResult],
        graph_relations: List[GraphRelation],
        ontology_rules: List[Dict[str, str]],
        center_term: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        근거 기반 답변 생성

        Args:
            query: 사용자 질문
            vector_results: Vector Search 결과
            graph_relations: Graph Traversal 결과
            ontology_rules: 온톨로지 룰
            center_term: 그래프 중심 용어
            model: 사용할 LLM 모델
            temperature: 생성 다양성 (낮을수록 보수적)

        Returns:
            답변 결과 딕셔너리
        """
        # 1. 컨텍스트 구조화
        context = self.formatter.build_full_context(
            query=query,
            vector_results=vector_results,
            graph_relations=graph_relations,
            ontology_rules=ontology_rules,
            center_term=center_term
        )

        logger.info(f"Generated context with {len(vector_results)} chunks, {len(graph_relations)} relations")

        # 2. LLM 호출
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"{context}\n\n## User Question\n{query}"}
        ]

        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=2048
            )

            answer = response.choices[0].message.content
            usage = response.usage

            logger.info(f"Answer generated. Tokens: {usage.total_tokens}")

            return {
                "success": True,
                "answer": answer,
                "context": context,
                "metadata": {
                    "model": model,
                    "temperature": temperature,
                    "tokens_used": usage.total_tokens,
                    "num_chunks": len(vector_results),
                    "num_relations": len(graph_relations),
                    "num_rules": len(ontology_rules)
                }
            }

        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": context
            }

    def generate_answer_streaming(
        self,
        query: str,
        vector_results: List[SearchResult],
        graph_relations: List[GraphRelation],
        ontology_rules: List[Dict[str, str]],
        center_term: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.3
    ):
        """
        스트리밍 방식으로 답변 생성 (실시간 출력용)

        Args:
            query: 사용자 질문
            vector_results: Vector Search 결과
            graph_relations: Graph Traversal 결과
            ontology_rules: 온톨로지 룰
            center_term: 그래프 중심 용어
            model: 사용할 LLM 모델
            temperature: 생성 다양성

        Yields:
            답변 토큰 스트림
        """
        # 컨텍스트 구조화
        context = self.formatter.build_full_context(
            query=query,
            vector_results=vector_results,
            graph_relations=graph_relations,
            ontology_rules=ontology_rules,
            center_term=center_term
        )

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"{context}\n\n## User Question\n{query}"}
        ]

        try:
            stream = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=2048,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            yield f"\n\n[오류 발생: {str(e)}]"


# ============================================================
# 사용 예시
# ============================================================

if __name__ == "__main__":
    from openai import OpenAI
    import os

    # OpenAI 클라이언트 초기화
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 답변 생성기 초기화
    generator = RAGAnswerGenerator(client)

    # 예시 데이터
    query = "동적 난이도 시스템이 유저 경험에 어떤 영향을 주나요?"

    vector_results = [
        SearchResult(
            chunk_id=123,
            doc_id=5,
            doc_title="155레벨 기획서",
            content="동적 난이도 시스템은 유저의 실력 수준에 맞춰 자동으로 난이도를 조절합니다. 이를 통해 너무 어렵거나 쉬운 경험을 방지하여 지속적인 몰입 상태를 유지시킵니다.",
            similarity=0.92
        ),
        SearchResult(
            chunk_id=456,
            doc_id=8,
            doc_title="UX 개선 방안",
            content="적절한 난이도 밸런스는 유저의 좌절감을 줄이고 성취감을 높여 리텐션 향상에 기여합니다.",
            similarity=0.85
        )
    ]

    graph_relations = [
        GraphRelation(
            source="동적 난이도",
            predicate="balances",
            target="유저 실력",
            confidence=0.95,
            evidence="유저 실력에 맞춘"
        ),
        GraphRelation(
            source="동적 난이도",
            predicate="relieves",
            target="좌절감",
            confidence=0.90,
            evidence="좌절감을 줄이고"
        ),
        GraphRelation(
            source="동적 난이도",
            predicate="maintains",
            target="몰입",
            confidence=0.95,
            evidence="지속적인 몰입 상태를 유지"
        )
    ]

    ontology_rules = [
        {
            "subject_type": "mechanic",
            "predicate": "balances",
            "object_type": "condition",
            "description": "메카닉이 조건/상태 균형 맞춤"
        },
        {
            "subject_type": "mechanic",
            "predicate": "relieves",
            "object_type": "ux_factor",
            "description": "메카닉이 부정적 경험 완화"
        }
    ]

    # 답변 생성
    result = generator.generate_answer(
        query=query,
        vector_results=vector_results,
        graph_relations=graph_relations,
        ontology_rules=ontology_rules,
        center_term="동적 난이도"
    )

    if result["success"]:
        print("="*70)
        print("생성된 답변:")
        print("="*70)
        print(result["answer"])
        print("\n" + "="*70)
        print("메타데이터:")
        print(f"  - 사용 토큰: {result['metadata']['tokens_used']}")
        print(f"  - 청크 수: {result['metadata']['num_chunks']}")
        print(f"  - 관계 수: {result['metadata']['num_relations']}")
    else:
        print(f"오류: {result['error']}")
