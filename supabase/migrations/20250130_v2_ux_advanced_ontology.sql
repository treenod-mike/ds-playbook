-- ============================================================
-- Playbook Nexus - Complete Schema Migration v2.0
-- Version: v2.0 (2025-01-30)
-- Description: UX & Advanced Business Logic Update
--
-- 주요 변경사항:
--   v1.0 (2025-01-21): Initial schema with game logic (10 rules)
--   v1.1 (2025-01-21): Business Intelligence rules (20 rules)
--   v1.2 (2025-01-21): User Segmentation rules (7 rules)
--   v1.3 (2025-01-21): Marketing Funnel rules (5 rules)
--   v1.4 (2025-01-21): Reinforcement Learning columns
--   v2.0 (2025-01-30): UX & Advanced Business Logic (34 new rules)
--     - 카테고리 확장: 7개 → 11개 (Currency_Hard/Soft, Marketing, UX_Factor, Metric)
--     - 관계 타입 확장: 13개 → 22개
--     - Advanced Business Logic: accelerates, converts_to, optimizes, diversifies, impacts
--     - UX & Psychology: balances, induces, relieves, maintains
--     - 온톨로지 룰: 82개 → 116개
-- ============================================================

-- [1. 초기화] 기존 테이블 삭제 (의존성 역순)
-- ⚠️ 경고: 모든 데이터가 삭제됩니다.
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

-- 4.1. playbook_semantic_terms - 시멘틱 텀 (Nodes/Dictionary)
CREATE TABLE playbook_semantic_terms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id TEXT NOT NULL REFERENCES playbook_documents(id) ON DELETE CASCADE,
    term TEXT NOT NULL,                         -- 용어 (예: 더블폭탄, 동적 난이도)

    -- [v2.0 UPDATE] 카테고리 확장: 7개 → 11개
    -- GameObject, Currency_Hard, Currency_Soft, Mechanic, Content, Condition,
    -- Segment, Marketing, UX_Factor, Metric
    category TEXT NOT NULL,

    definition TEXT,                            -- 한 줄 정의
    confidence FLOAT DEFAULT 0.0,               -- 추출 신뢰도 (0.0-1.0)
    frequency INTEGER DEFAULT 1,                -- 문서 내 출현 빈도

    -- [핵심] Phase 1 LLM 추출 결과를 JSON으로 저장
    -- [v2.0 UPDATE] raw_relations에 confidence >= 0.7 관계만 저장 (최대 10개)
    -- 예시: [{"target": "블록", "type": "clears", "confidence": 0.95, "desc": "폭발로 제거"}]
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
COMMENT ON COLUMN playbook_semantic_terms.category IS '11개 카테고리: GameObject, Currency_Hard, Currency_Soft, Mechanic, Content, Condition, Segment, Marketing, UX_Factor, Metric';
COMMENT ON COLUMN playbook_semantic_terms.raw_relations IS 'Phase 1 추출 관계 (confidence >= 0.7, max 10개)';

-- 4.2. playbook_ontology_rules - 온톨로지 규칙 (Schema/Constitution)
-- [v2.0 UPDATE] 82개 → 116개 룰로 확장
CREATE TABLE playbook_ontology_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_type TEXT NOT NULL,                 -- 주어 타입 (예: mechanic, ux_factor)
    predicate TEXT NOT NULL,                    -- 서술어 (예: triggers, balances, optimizes)
    object_type TEXT NOT NULL,                  -- 목적어 타입 (예: gameobject, metric)
    description TEXT,                           -- 규칙 설명
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(subject_type, predicate, object_type) -- 중복 규칙 방지
);

CREATE INDEX idx_playbook_rules_predicate ON playbook_ontology_rules(predicate);
CREATE INDEX idx_playbook_rules_subject ON playbook_ontology_rules(subject_type);
CREATE INDEX idx_playbook_rules_object ON playbook_ontology_rules(object_type);

COMMENT ON TABLE playbook_ontology_rules IS '유효한 관계 규칙 정의 (온톨로지 스키마) - v2.0: 116개 룰';
COMMENT ON COLUMN playbook_ontology_rules.predicate IS 'v2.0: 22개 predicate 지원 (Core:9 + LiveOps:4 + Advanced:5 + UX:4)';

-- 4.3. playbook_semantic_relations - 시멘틱 관계 (Edges/Graph)
-- Phase 2에서 온톨로지 룰 검증 후 저장되는 최종 관계
CREATE TABLE playbook_semantic_relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    source_term_id UUID NOT NULL REFERENCES playbook_semantic_terms(id) ON DELETE CASCADE,
    target_term_id UUID NOT NULL REFERENCES playbook_semantic_terms(id) ON DELETE CASCADE,

    -- [v2.0 UPDATE] 22개 predicate 지원
    -- Core Gameplay (9): triggers, consumes, clears, counters, rewards, requires, contains, unlocks, synergizes_with
    -- LiveOps & Business (4): boosts, drains, promotes, targets
    -- Advanced Business (5): accelerates, converts_to, optimizes, diversifies, impacts
    -- UX & Psychology (4): balances, induces, relieves, maintains
    predicate TEXT NOT NULL,

    confidence FLOAT DEFAULT 1.0,               -- 관계 신뢰도 (0.0-1.0)
    evidence_chunk_id UUID REFERENCES playbook_chunks(id), -- 근거가 된 청크
    evidence TEXT,                              -- 관계의 근거 텍스트

    -- Reinforcement Learning 컬럼
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

COMMENT ON TABLE playbook_semantic_relations IS 'Phase 2 검증된 최종 지식 그래프 엣지';
COMMENT ON COLUMN playbook_semantic_relations.predicate IS 'v2.0: 22개 관계 타입 지원 (Core 9 + LiveOps 4 + Advanced 5 + UX 4)';
COMMENT ON COLUMN playbook_semantic_relations.evidence IS 'LLM이 추출한 관계의 근거 텍스트';
COMMENT ON COLUMN playbook_semantic_relations.occurrence_count IS '관계가 여러 문서에서 관찰된 횟수 (reinforcement learning)';

-- ============================================================
-- [5. Seed Data: Ontology Rules v2.0]
-- ============================================================

-- 5.1. Core Gameplay Rules (10 rules)
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
('content', 'unlocks', 'content', '진행에 따른 해금')
ON CONFLICT DO NOTHING;

-- 5.2. Business Intelligence Rules (20 rules)
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
-- [가치와 인과]
('mechanic', 'increases', 'metric', '시스템이 지표를 상승시킴 (예: 버프 -> 승률)'),
('mechanic', 'decreases', 'metric', '시스템이 지표를 하락시킴 (예: 난이도 하향 -> 이탈률)'),
('system', 'causes', 'metric', '문제가 지표에 악영향 (예: 서버다운 -> 매출 하락)'),
('content', 'generates', 'metric', '컨텐츠가 지표를 발생시킴 (예: 이벤트 -> 매출)'),
('metric', 'correlated_with', 'metric', '지표 간 상관관계 (예: DAU <-> 매출)'),

-- [상점과 판매]
('system', 'sells', 'content', '상점이 상품을 판매함 (예: 다이아 상점 -> 패키지)'),
('content', 'contains', 'resource', '상품의 구성품'),
('content', 'costs', 'resource', '상품의 가격'),
('content', 'promotes', 'content', '이벤트가 상품 판매 촉진 (예: 할인 -> 패키지)'),

-- [경제 흐름]
('system', 'drains', 'resource', '시스템이 재화를 대량 소모 (예: 고난이도 -> 클로버)'),
('resource', 'bottlenecks', 'content', '재화 부족이 진행을 막음'),
('condition', 'triggers', 'mechanic', '조건이 행동을 유발함'),

-- [난이도와 행동]
('content', 'has_condition', 'condition', '컨텐츠의 상태 (예: 어려움, 쉬움)'),
('condition', 'accelerates', 'resource', '상태가 소모를 가속화함 (예: 고난이도 -> 클로버 소모)'),
('resource', 'causes', 'metric', '과도한 소모가 이탈 유발'),
('condition', 'induces', 'ux_factor', '난이도가 감정 유발 (예: 고난이도 -> 좌절감)'),

-- [참여와 성과]
('mechanic', 'targets', 'content', '행동의 대상'),
('mechanic', 'boosts', 'metric', '행동이 지표를 폭발적 상승 (예: 이벤트 참여 -> 인게이지먼트)'),
('mechanic', 'guarantees', 'resource', '행동 시 확정 보상 (예: 출석 7일 -> 다이아)'),
('condition', 'prevents', 'resource', '조건 미달로 보상 실패 (예: 낮은 점수 -> 별 3개 미달)')
ON CONFLICT DO NOTHING;

-- 5.3. User Segmentation Rules (7 rules)
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
-- [타겟팅 및 정의]
('content', 'targets', 'segment', '컨텐츠가 특정 유저층 타겟 (예: 웰컴 패키지 -> 신규 유저)'),
('condition', 'defines', 'segment', '유저 세그먼트 기준 (예: 7일내 가입 -> NRU)'),

-- [세그먼트의 영향력]
('segment', 'generates', 'metric', '특정 유저층이 지표 발생 (예: STU -> 매출)'),
('segment', 'prefers', 'content', '특정 유저층이 선호하는 컨텐츠'),
('segment', 'performs', 'mechanic', '특정 유저층이 주로 하는 행동'),

-- [세그먼트별 경험]
('condition', 'blocks', 'segment', '조건이 유저층 진행 막음 (예: 난이도 -> NRU 이탈)'),
('system', 'supports', 'segment', '시스템이 특정 유저층 지원 (예: 튜토리얼 -> NRU)')
ON CONFLICT DO NOTHING;

-- 5.4. Marketing Funnel Rules (5 rules)
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
-- [마케팅 활동]
('marketing', 'utilizes', 'content', '마케팅이 이벤트를 소재로 활용 (예: TV CF -> 콜라보)'),
('marketing', 'promotes', 'content', '마케팅이 컨텐츠 홍보 (예: 사전예약 -> 신규 챕터)'),

-- [유입 성과]
('marketing', 'acquires', 'segment', '마케팅이 유저층 획득 (예: UA광고 -> NRU)'),
('marketing', 'boosts', 'metric', '마케팅이 유입 지표 급증 (예: 바이럴 -> 인스톨)'),

-- [퍼널 전환]
('metric', 'converts_to', 'segment', '지표가 실제 유저로 전환 (예: 인스톨 -> NRU)')
ON CONFLICT DO NOTHING;

-- ============================================================
-- 5.5. [v2.0 NEW] LiveOps & Business Rules (17 rules)
-- ============================================================
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
-- [boosts 관계 - 이벤트/시스템 → 지표/행동]
('content', 'boosts', 'system', '이벤트가 시스템 지표를 강화함 (예: 턴릴레이 -> DAU)'),
('content', 'boosts', 'mechanic', '컨텐츠가 게임 메카닉 사용 증가 (예: 이벤트 -> 플레이 빈도)'),
('mechanic', 'boosts', 'mechanic', '메카닉이 다른 메카닉 사용 촉진'),
('system', 'boosts', 'mechanic', '시스템이 특정 행동 강화'),

-- [drains 관계 - 컨텐츠 → 재화 싱크]
('content', 'drains', 'resource', '컨텐츠가 재화를 대량 소모 (예: 계속하기 -> 다이아)'),
('mechanic', 'drains', 'resource', '메카닉이 재화 소모'),
('gameobject', 'drains', 'resource', '게임 오브젝트가 재화 소모'),

-- [promotes 관계 - 상황 → 구매 촉진]
('mechanic', 'promotes', 'content', '메카닉이 컨텐츠 구매 촉진 (예: 난이도 -> 계속하기)'),
('condition', 'promotes', 'content', '조건이 컨텐츠 구매 촉진'),
('condition', 'promotes', 'mechanic', '조건이 메카닉 사용 촉진'),
('gameobject', 'promotes', 'content', '게임 오브젝트가 컨텐츠 구매 촉진'),

-- [targets 관계 - 상품/이벤트 → 유저 세그먼트]
('content', 'targets', 'system', '컨텐츠가 특정 유저 세그먼트 대상'),
('mechanic', 'targets', 'system', '메카닉이 특정 유저 세그먼트 대상'),
('mechanic', 'targets', 'segment', '메카닉이 특정 유저 세그먼트 대상'),

-- [Segment 역관계]
('segment', 'requires', 'content', '유저 세그먼트가 특정 컨텐츠 대상')
ON CONFLICT DO NOTHING;

-- ============================================================
-- 5.6. [v2.0 NEW] UX & Psychology Rules (16 rules)
-- ============================================================
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
-- [balances 관계 - 시스템 ↔ 요소 균형]
('mechanic', 'balances', 'condition', '메카닉이 조건/상태 균형 맞춤 (예: 동적 난이도 -> 유저 실력)'),
('system', 'balances', 'condition', '시스템이 조건/상태 균형 맞춤 (예: 매칭 시스템 -> 팀 밸런스)'),
('mechanic', 'balances', 'mechanic', '메카닉이 다른 메카닉과 균형 맞춤 (예: 난이도 조절 -> 보상)'),
('content', 'balances', 'condition', '컨텐츠가 조건의 균형 맞춤 (예: 튜토리얼 -> 난이도)'),

-- [induces 관계 - 조건 → 심리/행동]
('condition', 'induces', 'ux_factor', '조건이 UX 요소/감정 유발 (예: 고난이도 -> 좌절감)'),
('mechanic', 'induces', 'ux_factor', '메카닉이 UX 요소/감정 유발 (예: 연속 성공 -> 성취감)'),
('content', 'induces', 'ux_factor', '컨텐츠가 UX 요소/감정 유발 (예: 보스전 -> 긴장감)'),
('gameobject', 'induces', 'ux_factor', '게임 오브젝트가 감정 유발 (예: 캐릭터 -> 애착)'),

-- [relieves 관계 - 아이템/시스템 → 부정적 경험 완화]
('gameobject', 'relieves', 'ux_factor', '아이템이 부정적 경험 완화 (예: 힌트 아이템 -> 막힘)'),
('mechanic', 'relieves', 'ux_factor', '메카닉이 부정적 경험 완화 (예: 셔플 -> 막힘)'),
('content', 'relieves', 'ux_factor', '컨텐츠가 부정적 경험 완화 (예: 보상 지급 -> 박탈감)'),
('system', 'relieves', 'ux_factor', '시스템이 부정적 경험 완화 (예: 난이도 하향 -> 좌절감)'),

-- [maintains 관계 - 시스템 → 긍정적 상태 유지]
('mechanic', 'maintains', 'ux_factor', '메카닉이 긍정적 상태 유지 (예: 적절한 난이도 -> 몰입)'),
('content', 'maintains', 'ux_factor', '컨텐츠가 긍정적 상태 유지 (예: 보상 구조 -> 동기부여)'),
('system', 'maintains', 'ux_factor', '시스템이 긍정적 상태 유지 (예: 피드백 -> 성취감)'),
('gameobject', 'maintains', 'ux_factor', '게임 오브젝트가 긍정적 상태 유지')
ON CONFLICT DO NOTHING;

-- ============================================================
-- 5.7. [v2.0 NEW] Advanced Business Logic Rules (18 rules)
-- ============================================================
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
-- [optimizes 관계 - 시스템 → 지표/경험 최적화]
('system', 'optimizes', 'metric', '시스템이 지표 최적화 (예: 개인화 알고리즘 -> 매출)'),
('mechanic', 'optimizes', 'metric', '메카닉이 지표 최적화 (예: 튜토리얼 -> 리텐션)'),
('content', 'optimizes', 'metric', '컨텐츠가 지표 최적화 (예: 추천 시스템 -> 전환율)'),
('system', 'optimizes', 'ux_factor', '시스템이 경험 최적화 (예: 동적 가격 -> 만족도)'),
('mechanic', 'optimizes', 'condition', '메카닉이 조건 최적화 (예: 개인화 -> 난이도 밸런스)'),

-- [diversifies 관계 - 시스템 → 경험/패턴 다양화]
('system', 'diversifies', 'ux_factor', '시스템이 경험 다양화 (예: AB테스트 -> 유저 경험)'),
('mechanic', 'diversifies', 'ux_factor', '메카닉이 경험 다양화 (예: 랜덤 보상 -> 경험)'),
('content', 'diversifies', 'content', '컨텐츠가 다른 컨텐츠 다양화 (예: 개인화 이벤트 -> 콘텐츠)'),
('system', 'diversifies', 'content', '시스템이 컨텐츠 다양화 (예: AB테스트 -> 상점 UI)'),
('mechanic', 'diversifies', 'condition', '메카닉이 조건 다양화 (예: 동적 난이도 -> 스테이지 체감)'),

-- [impacts 관계 - 변경 → 행동/지표, 중립적 인과관계]
('system', 'impacts', 'ux_factor', '시스템이 경험에 영향 (예: UI 변경 -> 조작감)'),
('content', 'impacts', 'metric', '컨텐츠가 지표에 영향 (예: 신규 콘텐츠 -> 유저 행동)'),
('mechanic', 'impacts', 'metric', '메카닉이 지표에 영향 (예: 밸런스 패치 -> 메타 게임)'),
('system', 'impacts', 'metric', '시스템이 지표에 영향 (예: 소셜 기능 -> 상호작용)'),
('content', 'impacts', 'ux_factor', '컨텐츠가 경험에 영향 (예: 이벤트 -> 플레이 패턴)'),

-- [UX_Factor 역관계 - 결과로서의 심리 상태]
('ux_factor', 'boosts', 'metric', 'UX 요소가 지표 증폭 (예: 몰입 -> 리텐션)'),
('ux_factor', 'causes', 'metric', 'UX 요소가 지표에 부정적 영향 (예: 좌절감 -> 이탈률)'),
('ux_factor', 'promotes', 'content', 'UX 요소가 구매 촉진 (예: 막힘 -> 힌트 아이템 구매)')
ON CONFLICT DO NOTHING;

-- ============================================================
-- [6. 유틸리티 뷰 및 함수]
-- ============================================================

-- 6.1. 지식 그래프 조회용 뷰 (용어명으로 관계 표현)
CREATE OR REPLACE VIEW playbook_knowledge_graph AS
SELECT
    r.id,
    s.term as source_term,
    s.category as source_category,
    r.predicate,
    t.term as target_term,
    t.category as target_category,
    r.confidence,
    r.evidence,
    r.occurrence_count,
    r.last_verified_at,
    s.doc_id as source_doc_id,
    t.doc_id as target_doc_id
FROM playbook_semantic_relations r
JOIN playbook_semantic_terms s ON r.source_term_id = s.id
JOIN playbook_semantic_terms t ON r.target_term_id = t.id;

COMMENT ON VIEW playbook_knowledge_graph IS '지식 그래프 조회용 뷰 (용어명으로 관계 표현)';

-- 6.2. 용어별 관계 통계 함수
CREATE OR REPLACE FUNCTION get_term_relation_stats(term_name TEXT)
RETURNS TABLE (
    predicate TEXT,
    as_source BIGINT,
    as_target BIGINT,
    total BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.predicate,
        COUNT(*) FILTER (WHERE s.term = term_name) as as_source,
        COUNT(*) FILTER (WHERE t.term = term_name) as as_target,
        COUNT(*) as total
    FROM playbook_semantic_relations r
    JOIN playbook_semantic_terms s ON r.source_term_id = s.id
    JOIN playbook_semantic_terms t ON r.target_term_id = t.id
    WHERE s.term = term_name OR t.term = term_name
    GROUP BY r.predicate
    ORDER BY total DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_term_relation_stats IS '특정 용어의 관계 통계 조회 (predicate별 source/target 카운트)';

-- 6.3. 카테고리별 용어 수 통계 뷰
CREATE OR REPLACE VIEW playbook_category_stats AS
SELECT
    category,
    COUNT(*) as term_count,
    AVG(confidence) as avg_confidence,
    COUNT(DISTINCT doc_id) as doc_count
FROM playbook_semantic_terms
GROUP BY category
ORDER BY term_count DESC;

COMMENT ON VIEW playbook_category_stats IS 'v2.0: 11개 카테고리별 용어 통계 (GameObject, Currency_Hard, Currency_Soft, Mechanic, Content, Condition, Segment, Marketing, UX_Factor, Metric, system)';

-- 6.4. Predicate별 관계 수 통계 뷰
CREATE OR REPLACE VIEW playbook_predicate_stats AS
SELECT
    predicate,
    COUNT(*) as relation_count,
    AVG(confidence) as avg_confidence,
    AVG(occurrence_count) as avg_occurrence
FROM playbook_semantic_relations
GROUP BY predicate
ORDER BY relation_count DESC;

COMMENT ON VIEW playbook_predicate_stats IS 'v2.0: 22개 predicate별 관계 통계 (Core 9 + LiveOps 4 + Advanced 5 + UX 4)';

-- ============================================================
-- [7. 완료 메시지]
-- ============================================================

DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Playbook Nexus v2.0 Migration Complete!';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Schema Version: v2.0 (2025-01-30)';
    RAISE NOTICE 'Total Ontology Rules: 116 (82 -> 116, +34 new rules)';
    RAISE NOTICE '';
    RAISE NOTICE 'New Features:';
    RAISE NOTICE '  - Categories: 7 -> 11 (Currency_Hard/Soft, Marketing, UX_Factor, Metric)';
    RAISE NOTICE '  - Predicates: 13 -> 22';
    RAISE NOTICE '  - Advanced Business Logic: accelerates, converts_to, optimizes, diversifies, impacts';
    RAISE NOTICE '  - UX & Psychology: balances, induces, relieves, maintains';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Run Phase 1: bash run_phase1_test.sh';
    RAISE NOTICE '  2. Run Phase 2: python3 run_phase2_only.py';
    RAISE NOTICE '  3. Verify: python3 scripts/diagnose_relations.py';
    RAISE NOTICE '============================================================';
END $$;
