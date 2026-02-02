-- 누락된 온톨로지 규칙 추가 (로그 분석 기반)
-- 2026-02-01: Phase 2에서 스킵된 관계 타입들

-- ========================================
-- 1. REWARDS 관계 (보상 시스템)
-- ========================================

-- resource -> resource (74건, 가장 많이 스킵됨)
-- 예: "코인 -> 경험치", "아이템 -> 아이템"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'rewards', 'resource', false, 0.7, '리소스 획득 시 다른 리소스 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> content (72건)
-- 예: "코인 -> 챕터", "아이템 -> 미션"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'rewards', 'content', false, 0.7, '리소스 획득 시 콘텐츠 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> resource (56건)
-- 예: "보스 -> 아이템", "상자 -> 코인"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'rewards', 'resource', false, 0.7, '게임오브젝트가 리소스 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> content (40건)
-- 예: "던전 -> 챕터", "NPC -> 퀘스트"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'rewards', 'content', false, 0.7, '게임오브젝트가 콘텐츠 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- content -> gameobject (21건)
-- 예: "퀘스트 -> 아이템", "미션 -> 보상"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('content', 'rewards', 'gameobject', false, 0.7, '콘텐츠가 게임오브젝트 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> condition (19건)
-- 예: "보스 -> 클리어 조건", "상자 -> 획득 조건"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'rewards', 'condition', false, 0.7, '게임오브젝트가 조건 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> condition (9건)
-- 예: "코인 -> 구매 조건", "레벨 -> 해금 조건"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'rewards', 'condition', false, 0.7, '리소스 획득 시 조건 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> mechanic (8건)
-- 예: "경험치 -> 레벨업 메카닉", "코인 -> 구매 메카닉"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'rewards', 'mechanic', false, 0.7, '리소스 획득 시 메카닉 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- mechanic -> resource (6건)
-- 예: "가챠 -> 아이템", "합성 -> 장비"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('mechanic', 'rewards', 'resource', false, 0.7, '메카닉 실행 시 리소스 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> gameobject (5건)
-- 예: "재료 -> 장비", "코인 -> 캐릭터"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'rewards', 'gameobject', false, 0.7, '리소스로 게임오브젝트 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> gameobject (5건)
-- 예: "보스 -> 장비", "상자 -> 아이템"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'rewards', 'gameobject', false, 0.7, '게임오브젝트가 다른 게임오브젝트 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- system -> content (4건)
-- 예: "이벤트 시스템 -> 특별 미션"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('system', 'rewards', 'content', false, 0.7, '시스템이 콘텐츠 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- content -> content (3건)
-- 예: "챕터 -> 보너스 스테이지"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('content', 'rewards', 'content', false, 0.7, '콘텐츠가 다른 콘텐츠 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> system (3건)
-- 예: "보스 -> 업적 시스템"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'rewards', 'system', false, 0.7, '게임오브젝트가 시스템 보상')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- ========================================
-- 2. CONTAINS 관계 (포함 관계)
-- ========================================

-- content -> gameobject (16건)
-- 예: "던전 -> 몬스터", "스테이지 -> 보스"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('content', 'contains', 'gameobject', false, 0.7, '콘텐츠가 게임오브젝트 포함')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> content (7건)
-- 예: "던전 -> 방", "맵 -> 구역"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'contains', 'content', false, 0.7, '게임오브젝트가 콘텐츠 포함')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- ========================================
-- 3. REQUIRES 관계 (필요 조건)
-- ========================================

-- condition -> content (12건)
-- 예: "레벨 조건 -> 던전 입장"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('condition', 'requires', 'content', false, 0.7, '조건 충족 필요 (콘텐츠)')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> content (8건)
-- 예: "열쇠 -> 던전 입장", "아이템 -> 퀘스트 진행"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'requires', 'content', false, 0.7, '게임오브젝트 필요 (콘텐츠)')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- content -> content (8건)
-- 예: "챕터 1 -> 챕터 2", "튜토리얼 -> 메인 게임"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('content', 'requires', 'content', false, 0.7, '선행 콘텐츠 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- mechanic -> content (7건)
-- 예: "합성 메카닉 -> 재료 콘텐츠"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('mechanic', 'requires', 'content', false, 0.7, '메카닉 실행에 콘텐츠 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> resource (6건)
-- 예: "장비 강화 -> 강화석", "진화 -> 진화 재료"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'requires', 'resource', false, 0.7, '리소스 획득/사용에 다른 리소스 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> content (6건)
-- 예: "입장권 -> 던전", "키 -> 챕터"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'requires', 'content', false, 0.7, '리소스 사용에 콘텐츠 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> condition (5건)
-- 예: "레벨업 -> 레벨 조건", "진화 -> 진화 조건"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'requires', 'condition', false, 0.7, '리소스 사용에 조건 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- condition -> condition (5건)
-- 예: "최종 조건 -> 중간 조건들"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('condition', 'requires', 'condition', false, 0.7, '조건 충족에 다른 조건 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- system -> content (3건)
-- 예: "퀘스트 시스템 -> 퀘스트 콘텐츠"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('system', 'requires', 'content', false, 0.7, '시스템 작동에 콘텐츠 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- gameobject -> resource (3건)
-- 예: "보스 도전 -> 입장권", "상점 -> 화폐"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('gameobject', 'requires', 'resource', false, 0.7, '게임오브젝트 사용에 리소스 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- condition -> system (3건)
-- 예: "레벨 조건 -> 레벨업 시스템"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('condition', 'requires', 'system', false, 0.7, '조건 충족에 시스템 필요')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- ========================================
-- 4. CONSUMES 관계 (소비)
-- ========================================

-- resource -> resource (10건)
-- 예: "강화 -> 강화석", "합성 -> 재료"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'consumes', 'resource', false, 0.7, '리소스 사용 시 다른 리소스 소비')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- resource -> content (4건)
-- 예: "스태미나 -> 던전 입장"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, confidence_threshold, description)
VALUES ('resource', 'consumes', 'content', false, 0.7, '콘텐츠 이용 시 리소스 소비')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- ========================================
-- 5. SYNERGIZES_WITH 관계 (시너지)
-- ========================================

-- resource -> resource (9건)
-- 예: "불 속성 -> 불 강화", "세트 아이템 -> 세트 효과"
INSERT INTO playbook_ontology_rules (source_category, relation_type, target_category, bidirectional, true, confidence_threshold, description)
VALUES ('resource', 'synergizes_with', 'resource', true, 0.7, '리소스 간 시너지 효과')
ON CONFLICT (source_category, relation_type, target_category) DO NOTHING;

-- ========================================
-- 통계 확인
-- ========================================

SELECT '✅ 온톨로지 규칙 추가 완료!' as message;

SELECT
    '총 규칙 수: ' || COUNT(*) as stats
FROM playbook_ontology_rules;

SELECT
    '카테고리별 분포:' as category_stats;

SELECT
    source_category,
    relation_type,
    COUNT(*) as count
FROM playbook_ontology_rules
GROUP BY source_category, relation_type
ORDER BY source_category, count DESC;
