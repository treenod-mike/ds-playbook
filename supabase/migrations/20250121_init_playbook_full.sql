-- ============================================================
-- Playbook Nexus - Full Schema Migration
-- Version: v1.4 (2025-01-21)
-- Description: Complete rebuild with 5-table architecture + Reinforcement Learning
-- Changelog:
--   v1.0 (2025-01-21): Initial schema with 10 game logic rules
--   v1.1 (2025-01-21): Added 20 Business Intelligence rules
--   v1.2 (2025-01-21): Added 7 User Segmentation rules (NRU/CBU/STU)
--   v1.3 (2025-01-21): Added 5 Marketing Funnel rules (마케팅 및 유입)
--   v1.4 (2025-01-21): Added Reinforcement Learning columns (occurrence_count, last_verified_at)
-- ============================================================

-- [1. 초기화] 기존 테이블 삭제 (의존성 역순)
-- 경고: 모든 데이터가 삭제됩니다.
DROP TABLE IF EXISTS playbook_semantic_relations CASCADE;
DROP TABLE IF EXISTS playbook_ontology_rules CASCADE;
DROP TABLE IF EXISTS playbook_semantic_terms CASCADE;
DROP TABLE IF EXISTS playbook_chunks CASCADE;
DROP TABLE IF EXISTS playbook_documents CASCADE;

-- [2. 확장 기능 활성화]
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- [3. Tier 1: Raw Data & Vectors]
-- ============================================================

-- 3.1. playbook_documents - 문서 원본 정보 (Library)
CREATE TABLE playbook_documents (
    id TEXT PRIMARY KEY,                        -- Confluence Page ID
    title TEXT NOT NULL,                        -- 문서 제목
    space TEXT,                                 -- Confluence Space Key
    url TEXT,                                   -- 문서 URL
    content_length INTEGER,                     -- 원본 길이
    last_updated TIMESTAMP WITH TIME ZONE,      -- 마지막 수정일
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_playbook_docs_space ON playbook_documents(space);
CREATE INDEX idx_playbook_docs_updated ON playbook_documents(last_updated);

COMMENT ON TABLE playbook_documents IS 'Confluence 문서 메타데이터 저장';
COMMENT ON COLUMN playbook_documents.id IS 'Confluence Page ID (외부 시스템 키)';

-- 3.2. playbook_chunks - 텍스트 청크 + 임베딩 (Pages)
CREATE TABLE playbook_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id TEXT NOT NULL REFERENCES playbook_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,               -- 문서 내 순서
    content TEXT NOT NULL,                      -- 실제 텍스트 내용
    metadata JSONB DEFAULT '{}',                -- {doc_type, title, section 등}
    embedding VECTOR(1536),                     -- OpenAI 임베딩 (1536차원)
    char_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(doc_id, chunk_index)                 -- 문서 내 인덱스 중복 방지
);

CREATE INDEX idx_playbook_chunks_doc ON playbook_chunks(doc_id);
CREATE INDEX idx_playbook_chunks_meta ON playbook_chunks USING GIN(metadata);

COMMENT ON TABLE playbook_chunks IS '문서를 청크로 분할하여 임베딩과 함께 저장';
COMMENT ON COLUMN playbook_chunks.embedding IS 'OpenAI text-embedding-3-small (1536차원)';

-- 벡터 인덱스는 데이터 1000건 이상일 때 생성 권장
-- CREATE INDEX idx_playbook_chunks_vec ON playbook_chunks
--   USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================
-- [4. Tier 2: Ontology Components (Knowledge Graph)]
-- ============================================================

-- 4.1. playbook_semantic_terms - 시멘틱 텀 (Nodes/Dictionary) - "벽돌"
CREATE TABLE playbook_semantic_terms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id TEXT NOT NULL REFERENCES playbook_documents(id) ON DELETE CASCADE,
    term TEXT NOT NULL,                         -- 용어 (예: 더블폭탄, Docker)
    category TEXT NOT NULL,                     -- 카테고리 (예: GameObject, Technology)
    definition TEXT,                            -- 한 줄 정의
    confidence FLOAT DEFAULT 0.0,               -- 추출 신뢰도 (0.0-1.0)
    frequency INTEGER DEFAULT 1,                -- 문서 내 출현 빈도

    -- [핵심] 1단계 LLM 추출 결과를 JSON으로 저장
    -- 용도: 백업, 빠른 조회, 온톨로지 빌더의 입력 소스
    -- 예시: [{"target": "블록", "type": "clears", "confidence": 0.95}]
    raw_relations JSONB DEFAULT '[]',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 한 문서 안에서 같은 용어 중복 방지
    UNIQUE(doc_id, term)
);

CREATE INDEX idx_playbook_terms_term ON playbook_semantic_terms(term);
CREATE INDEX idx_playbook_terms_category ON playbook_semantic_terms(category);
CREATE INDEX idx_playbook_terms_doc ON playbook_semantic_terms(doc_id);
CREATE INDEX idx_playbook_terms_raw_rel ON playbook_semantic_terms USING GIN(raw_relations);

COMMENT ON TABLE playbook_semantic_terms IS '문서에서 추출한 시멘틱 용어 (지식 그래프의 노드)';
COMMENT ON COLUMN playbook_semantic_terms.raw_relations IS '1단계 추출된 관계 정보 (JSONB 배열)';

-- 4.2. playbook_ontology_rules - 온톨로지 규칙 (Schema/Constitution) - "법전"
-- AI가 엉뚱한 관계를 맺지 못하게 하는 제약 조건
CREATE TABLE playbook_ontology_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_type TEXT NOT NULL,                 -- 주어 타입 (예: Mechanic)
    predicate TEXT NOT NULL,                    -- 서술어 (예: triggers)
    object_type TEXT NOT NULL,                  -- 목적어 타입 (예: GameObject)
    description TEXT,                           -- 규칙 설명
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(subject_type, predicate, object_type) -- 중복 규칙 방지
);

CREATE INDEX idx_playbook_rules_predicate ON playbook_ontology_rules(predicate);
CREATE INDEX idx_playbook_rules_subject ON playbook_ontology_rules(subject_type);
CREATE INDEX idx_playbook_rules_object ON playbook_ontology_rules(object_type);

COMMENT ON TABLE playbook_ontology_rules IS '유효한 관계 규칙 정의 (온톨로지 스키마)';
COMMENT ON COLUMN playbook_ontology_rules.subject_type IS '주어 카테고리 (예: Mechanic, GameObject)';

-- 4.3. playbook_semantic_relations - 시멘틱 관계 (Edges/Graph) - "연결선"
-- 실제 지식 그래프가 저장되는 핵심 테이블
CREATE TABLE playbook_semantic_relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    source_term_id UUID NOT NULL REFERENCES playbook_semantic_terms(id) ON DELETE CASCADE,
    target_term_id UUID NOT NULL REFERENCES playbook_semantic_terms(id) ON DELETE CASCADE,

    predicate TEXT NOT NULL,                    -- triggers, consumes, clears 등

    confidence FLOAT DEFAULT 1.0,               -- 관계 신뢰도 (0.0-1.0)
    evidence_chunk_id UUID REFERENCES playbook_chunks(id), -- 근거가 된 청크
    evidence TEXT,                              -- 관계의 근거 텍스트

    -- Reinforcement Learning 컬럼 (v1.4)
    occurrence_count INT DEFAULT 1,             -- 관계가 관찰된 횟수
    last_verified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- 마지막 검증 시각

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 같은 관계 중복 방지 (source -> predicate -> target)
    UNIQUE(source_term_id, target_term_id, predicate)
);

CREATE INDEX idx_playbook_rel_source ON playbook_semantic_relations(source_term_id);
CREATE INDEX idx_playbook_rel_target ON playbook_semantic_relations(target_term_id);
CREATE INDEX idx_playbook_rel_predicate ON playbook_semantic_relations(predicate);
CREATE INDEX idx_playbook_rel_source_pred ON playbook_semantic_relations(source_term_id, predicate);
CREATE INDEX idx_playbook_rel_target_pred ON playbook_semantic_relations(target_term_id, predicate);

COMMENT ON TABLE playbook_semantic_relations IS '지식 그래프 엣지 (용어 간 관계)';
COMMENT ON COLUMN playbook_semantic_relations.evidence_chunk_id IS '관계의 근거가 된 텍스트 청크';
COMMENT ON COLUMN playbook_semantic_relations.evidence IS 'LLM이 추출한 관계의 근거 텍스트';
COMMENT ON COLUMN playbook_semantic_relations.occurrence_count IS '관계가 여러 문서에서 관찰된 횟수 (reinforcement learning)';
COMMENT ON COLUMN playbook_semantic_relations.last_verified_at IS '관계가 마지막으로 검증/관찰된 시각';

-- ============================================================
-- [5. Seed Data: Ontology Rules]
-- ============================================================

-- 5.1. Game Logic Rules (v1.0 - 10 rules)
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
-- [메카닉 & 상호작용]
('mechanic', 'triggers', 'gameobject', '행동이 객체를 생성함 (예: 4매치 -> 폭탄)'),
('gameobject', 'clears', 'gameobject', '아이템이 장애물을 제거함 (예: 폭탄 -> 바위)'),
('gameobject', 'counters', 'gameobject', '특정 아이템이 특정 장애물에 효과적임'),
('gameobject', 'synergizes_with', 'gameobject', '아이템 간의 조합 효과'),

-- [경제 시스템]
('mechanic', 'consumes', 'resource', '행동 시 비용 소모 (예: 이어하기 -> 다이아)'),
('content', 'rewards', 'resource', '보상 획득 (예: 클리어 -> 체리)'),
('content', 'consumes', 'resource', '입장 비용 (예: 스테이지 -> 클로버)'),
('content', 'requires', 'condition', '클리어 조건 또는 해금 조건'),

-- [구조 계층]
('content', 'contains', 'content', '상위 컨텐츠가 하위를 포함 (예: 챕터 -> 스테이지)'),
('content', 'unlocks', 'content', '진행에 따른 해금');

-- 5.2. Business Intelligence Rules (v1.1 - 20 rules)
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
-- [가치와 인과 (Value & Causality)]
('mechanic', 'increases', 'metric', '시스템이 지표를 상승시킴 (예: 버프 -> 승률 상승)'),
('mechanic', 'decreases', 'metric', '시스템이 지표를 하락시킴 (예: 난이도 하향 -> 이탈률 감소)'),
('issue', 'causes', 'metric', '버그나 문제가 지표에 악영향을 줌 (예: 서버다운 -> 매출 하락)'),
('content', 'generates', 'metric', '컨텐츠가 지표(매출 등)를 발생시킴'),
('metric', 'correlated_with', 'metric', '지표 간의 상관관계 (예: DAU <-> 매출)'),

-- [상점과 판매 (Commerce)]
('system', 'sells', 'product', '상점이 상품을 판매함'),
('product', 'contains', 'resource', '상품의 구성품'),
('product', 'costs', 'resource', '상품의 가격'),
('event', 'promotes', 'product', '이벤트가 상품 판매를 촉진함'),

-- [경제 흐름 (Economy Flow)]
('system', 'drains', 'resource', '시스템이 재화를 대량으로 소모시킴 (Sink)'),
('resource', 'bottlenecks', 'progression', '재화 부족이 진행을 막음 (구매 유도점)'),
('condition', 'triggers', 'purchase', '부족/상태가 구매를 유발함'),

-- [난이도와 행동 (Difficulty)]
('content', 'has_condition', 'condition', '컨텐츠의 상태 (예: 어려움, 쉬움)'),
('condition', 'accelerates', 'resourceconsumption', '상태가 소모를 가속화함'),
('resourceconsumption', 'causes', 'churn', '과도한 소모가 이탈을 유발'),
('condition', 'induces', 'sentiment', '난이도가 감정을 유발 (도전욕구 vs 좌절)'),

-- [참여와 성과 (Participation)]
('action', 'targets', 'content', '행동의 대상 (이벤트 참여)'),
('action', 'boosts', 'metric', '행동이 지표를 폭발적으로 상승시킴'),
('action', 'guarantees', 'resource', '행동 시 확정 보상 지급'),
('condition', 'prevents', 'resource', '조건 미달로 보상 획득 실패');

-- 5.3. User Segmentation Rules (v1.2 - 7 rules)
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
-- [타겟팅 및 정의]
('action', 'targets', 'usersegment', '행동/이벤트가 특정 유저층을 타겟함 (예: 이벤트 -> NRU)'),
('condition', 'defines', 'usersegment', '유저 세그먼트를 나누는 기준 (예: 7일내 가입 -> NRU)'),

-- [세그먼트의 영향력 (Impact)]
('usersegment', 'generates', 'metric', '특정 유저층이 지표를 발생시킴 (예: STU -> 매출)'),
('usersegment', 'prefers', 'content', '특정 유저층이 선호하는 컨텐츠'),
('usersegment', 'performs', 'action', '특정 유저층이 주로 하는 행동'),

-- [세그먼트별 경험 (Experience)]
('condition', 'blocks', 'usersegment', '특정 조건이 유저층의 진행을 막음 (예: 난이도 -> NRU 이탈)'),
('system', 'supports', 'usersegment', '시스템이 특정 유저층을 지원함 (예: 튜토리얼 -> NRU)')
ON CONFLICT DO NOTHING;

-- 5.4. Marketing Funnel Rules (v1.3 - 5 rules)
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
-- [마케팅 활동 (Marketing Action)]
('marketing', 'utilizes', 'event', '마케팅이 특정 이벤트를 소재로 활용함 (예: TV CF -> 콜라보)'),
('marketing', 'promotes', 'content', '마케팅이 특정 컨텐츠를 홍보함 (예: 사전예약 -> 신규 챕터)'),

-- [유입 성과 (Acquisition)]
('marketing', 'acquires', 'usersegment', '마케팅이 특정 유저층을 획득함 (예: UA광고 -> NRU)'),
('marketing', 'boosts', 'metric', '마케팅이 유입 지표를 급증시킴 (예: 바이럴 -> 인스톨)'),

-- [퍼널 전환 (Funnel Conversion)]
('metric', 'converts_to', 'usersegment', '지표가 실제 유저로 전환됨 (예: 인스톨 -> NRU/진입)')
ON CONFLICT DO NOTHING;

-- ============================================================
-- [6. 유틸리티 뷰 및 함수]
-- ============================================================

-- 6.1. 지식 그래프 조회용 뷰 (용어명으로 관계 표현)
CREATE OR REPLACE VIEW playbook_knowledge_graph AS
SELECT
    source.term AS source_term,
    source.category AS source_category,
    rel.predicate,
    target.term AS target_term,
    target.category AS target_category,
    rel.confidence,
    rel.evidence_chunk_id,
    rel.evidence,
    source.doc_id
FROM playbook_semantic_relations rel
JOIN playbook_semantic_terms source ON rel.source_term_id = source.id
JOIN playbook_semantic_terms target ON rel.target_term_id = target.id;

COMMENT ON VIEW playbook_knowledge_graph IS '지식 그래프를 읽기 쉬운 형태로 표현한 뷰';

-- 6.2. 용어 검색 함수 (동의어 포함)
CREATE OR REPLACE FUNCTION search_terms(search_query TEXT)
RETURNS TABLE (
    term TEXT,
    category TEXT,
    definition TEXT,
    doc_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.term,
        t.category,
        t.definition,
        COUNT(DISTINCT t.doc_id) AS doc_count
    FROM playbook_semantic_terms t
    WHERE t.term ILIKE '%' || search_query || '%'
    GROUP BY t.term, t.category, t.definition
    ORDER BY doc_count DESC, t.term;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- [7. 통계 정보]
-- ============================================================

-- 테이블별 레코드 수 확인
DO $$
BEGIN
    RAISE NOTICE '==================================================';
    RAISE NOTICE 'Playbook Nexus Schema Migration Complete (v1.4)';
    RAISE NOTICE '==================================================';
    RAISE NOTICE 'Created Tables:';
    RAISE NOTICE '  ✓ playbook_documents (Tier 1)';
    RAISE NOTICE '  ✓ playbook_chunks (Tier 1)';
    RAISE NOTICE '  ✓ playbook_semantic_terms (Tier 2)';
    RAISE NOTICE '  ✓ playbook_ontology_rules (Tier 2)';
    RAISE NOTICE '  ✓ playbook_semantic_relations (Tier 2 + RL)';
    RAISE NOTICE '';
    RAISE NOTICE 'Seed Data:';
    RAISE NOTICE '  ✓ 10 Game Logic Rules (v1.0)';
    RAISE NOTICE '  ✓ 20 Business Intelligence Rules (v1.1)';
    RAISE NOTICE '  ✓ 7 User Segmentation Rules (v1.2)';
    RAISE NOTICE '  ✓ 5 Marketing Funnel Rules (v1.3)';
    RAISE NOTICE '  ✓ Total: 42 ontology rules';
    RAISE NOTICE '';
    RAISE NOTICE 'Features:';
    RAISE NOTICE '  ✓ Reinforcement Learning (v1.4)';
    RAISE NOTICE '    - occurrence_count: Tracks observation frequency';
    RAISE NOTICE '    - last_verified_at: Tracks last verification time';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Run Full Pipeline: python3 run_full_pipeline.py --full';
    RAISE NOTICE '     (Runs Phase 1 + Phase 2 automatically)';
    RAISE NOTICE '==================================================';
END $$;
