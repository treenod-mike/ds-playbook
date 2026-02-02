-- ============================================================
-- 누락된 온톨로지 규칙 추가 (로그 분석 기반)
-- 2026-02-01: Phase 2에서 스킵된 관계 타입들
--
-- 실행 전 확인사항:
-- - playbook_ontology_rules 테이블 구조 확인
-- - 컬럼명: source_category, relation_type, target_category (v3.0)
-- - 또는: subject_type, predicate, object_type (v2.0)
-- ============================================================

-- ========================================
-- 1. REWARDS 관계 (보상 시스템) - 14개 규칙
-- ========================================

-- resource -> resource (74건, 가장 많이 스킵됨)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'rewards', 'resource', false, 0.7, '리소스 획득 시 다른 리소스 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> content (72건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'rewards', 'content', false, 0.7, '리소스 획득 시 콘텐츠 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> resource (56건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'rewards', 'resource', false, 0.7, '게임오브젝트가 리소스 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> content (40건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'rewards', 'content', false, 0.7, '게임오브젝트가 콘텐츠 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- content -> gameobject (21건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('content', 'rewards', 'gameobject', false, 0.7, '콘텐츠가 게임오브젝트 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> condition (19건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'rewards', 'condition', false, 0.7, '게임오브젝트가 조건 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> condition (9건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'rewards', 'condition', false, 0.7, '리소스 획득 시 조건 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> mechanic (8건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'rewards', 'mechanic', false, 0.7, '리소스 획득 시 메카닉 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- mechanic -> resource (6건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('mechanic', 'rewards', 'resource', false, 0.7, '메카닉 실행 시 리소스 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> gameobject (5건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'rewards', 'gameobject', false, 0.7, '리소스로 게임오브젝트 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> gameobject (5건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'rewards', 'gameobject', false, 0.7, '게임오브젝트가 다른 게임오브젝트 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- system -> content (4건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('system', 'rewards', 'content', false, 0.7, '시스템이 콘텐츠 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- content -> content (3건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('content', 'rewards', 'content', false, 0.7, '콘텐츠가 다른 콘텐츠 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> system (3건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'rewards', 'system', false, 0.7, '게임오브젝트가 시스템 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- ========================================
-- 2. CONTAINS 관계 (포함 관계) - 2개 규칙
-- ========================================

-- content -> gameobject (16건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('content', 'contains', 'gameobject', false, 0.7, '콘텐츠가 게임오브젝트 포함')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> content (7건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'contains', 'content', false, 0.7, '게임오브젝트가 콘텐츠 포함')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- ========================================
-- 3. REQUIRES 관계 (필요 조건) - 10개 규칙
-- ========================================

-- condition -> content (12건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('condition', 'requires', 'content', false, 0.7, '조건 충족 필요 (콘텐츠)')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> content (8건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'requires', 'content', false, 0.7, '게임오브젝트 필요 (콘텐츠)')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- content -> content (8건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('content', 'requires', 'content', false, 0.7, '선행 콘텐츠 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- mechanic -> content (7건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('mechanic', 'requires', 'content', false, 0.7, '메카닉 실행에 콘텐츠 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> resource (6건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'requires', 'resource', false, 0.7, '리소스 획득/사용에 다른 리소스 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> content (6건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'requires', 'content', false, 0.7, '리소스 사용에 콘텐츠 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> condition (5건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'requires', 'condition', false, 0.7, '리소스 사용에 조건 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- condition -> condition (5건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('condition', 'requires', 'condition', false, 0.7, '조건 충족에 다른 조건 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- system -> content (3건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('system', 'requires', 'content', false, 0.7, '시스템 작동에 콘텐츠 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> resource (3건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'requires', 'resource', false, 0.7, '게임오브젝트 사용에 리소스 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- condition -> system (3건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('condition', 'requires', 'system', false, 0.7, '조건 충족에 시스템 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- ========================================
-- 4. CONSUMES 관계 (소비) - 2개 규칙
-- ========================================

-- resource -> resource (10건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'consumes', 'resource', false, 0.7, '리소스 사용 시 다른 리소스 소비')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> content (4건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'consumes', 'content', false, 0.7, '콘텐츠 이용 시 리소스 소비')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- ========================================
-- 5. SYNERGIZES_WITH 관계 (시너지) - 1개 규칙
-- ========================================

-- resource -> resource (9건)
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'synergizes_with', 'resource', true, 0.7, '리소스 간 시너지 효과')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- ========================================
-- 통계 확인
-- ========================================

SELECT '✅ 온톨로지 규칙 추가 완료!' as message;

SELECT '총 규칙 수: ' || COUNT(*) as stats FROM playbook_ontology_rules;

SELECT
    '추가된 규칙:' as summary,
    '  - REWARDS: 14개' as rewards,
    '  - CONTAINS: 2개' as contains,
    '  - REQUIRES: 10개' as requires,
    '  - CONSUMES: 2개' as consumes,
    '  - SYNERGIZES_WITH: 1개' as synergizes,
    '  - 총 29개 신규 규칙' as total;

SELECT
    source_category,
    relation_type,
    COUNT(*) as count
FROM playbook_ontology_rules
WHERE relation_type IN ('rewards', 'contains', 'requires', 'consumes', 'synergizes_with')
GROUP BY source_category, relation_type
ORDER BY source_category, count DESC;
