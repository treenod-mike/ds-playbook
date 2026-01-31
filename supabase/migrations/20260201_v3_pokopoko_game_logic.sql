-- ============================================================
-- Playbook Nexus - Schema Migration v3.0
-- Version: v3.0 (2026-02-01)
-- Description: 포코포코 게임 로직 온톨로지 확장
--
-- 주요 변경사항:
--   v3.0 (2026-02-01): 포코포코 게임 로직 확장 (29 new rules)
--     - Phase 2 로그 분석 기반 누락 규칙 추가
--     - REWARDS 관계 14개 (보상 시스템)
--     - CONTAINS 관계 2개 (포함 관계)
--     - REQUIRES 관계 11개 (필요 조건)
--     - CONSUMES 관계 2개 (소비)
--     - SYNERGIZES_WITH 관계 1개 (시너지)
--     - 온톨로지 룰: 116개 → 145개
-- ============================================================

-- REWARDS (14개)
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
('resource', 'rewards', 'resource', '리소스 획득 시 다른 리소스 보상'),
('resource', 'rewards', 'content', '리소스 획득 시 콘텐츠 보상'),
('gameobject', 'rewards', 'resource', '게임오브젝트가 리소스 보상'),
('gameobject', 'rewards', 'content', '게임오브젝트가 콘텐츠 보상'),
('content', 'rewards', 'gameobject', '콘텐츠가 게임오브젝트 보상'),
('gameobject', 'rewards', 'condition', '게임오브젝트가 조건 보상'),
('resource', 'rewards', 'condition', '리소스 획득 시 조건 보상'),
('resource', 'rewards', 'mechanic', '리소스 획득 시 메카닉 보상'),
('mechanic', 'rewards', 'resource', '메카닉 실행 시 리소스 보상'),
('resource', 'rewards', 'gameobject', '리소스로 게임오브젝트 보상'),
('gameobject', 'rewards', 'gameobject', '게임오브젝트가 다른 게임오브젝트 보상'),
('system', 'rewards', 'content', '시스템이 콘텐츠 보상'),
('content', 'rewards', 'content', '콘텐츠가 다른 콘텐츠 보상'),
('gameobject', 'rewards', 'system', '게임오브젝트가 시스템 보상')
ON CONFLICT (subject_type, predicate, object_type) DO NOTHING;

-- CONTAINS (2개)
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
('content', 'contains', 'gameobject', '콘텐츠가 게임오브젝트 포함'),
('gameobject', 'contains', 'content', '게임오브젝트가 콘텐츠 포함')
ON CONFLICT (subject_type, predicate, object_type) DO NOTHING;

-- REQUIRES (11개)
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
('condition', 'requires', 'content', '조건 충족 필요'),
('gameobject', 'requires', 'content', '게임오브젝트 필요'),
('content', 'requires', 'content', '선행 콘텐츠 필요'),
('mechanic', 'requires', 'content', '메카닉 실행 필요'),
('resource', 'requires', 'resource', '리소스 필요'),
('resource', 'requires', 'content', '리소스 사용 필요'),
('resource', 'requires', 'condition', '조건 필요'),
('condition', 'requires', 'condition', '조건 충족 필요'),
('system', 'requires', 'content', '시스템 작동 필요'),
('gameobject', 'requires', 'resource', '리소스 필요'),
('condition', 'requires', 'system', '시스템 필요')
ON CONFLICT (subject_type, predicate, object_type) DO NOTHING;

-- CONSUMES (2개)
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
('resource', 'consumes', 'resource', '리소스 소비'),
('resource', 'consumes', 'content', '콘텐츠 소비')
ON CONFLICT (subject_type, predicate, object_type) DO NOTHING;

-- SYNERGIZES_WITH (1개)
INSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES
('resource', 'synergizes_with', 'resource', '리소스 시너지')
ON CONFLICT (subject_type, predicate, object_type) DO NOTHING;

-- 완료 메시지
SELECT '✅ v3.0 마이그레이션 완료!' as message;
SELECT COUNT(*) as total_rules FROM playbook_ontology_rules;
