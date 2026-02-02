-- ============================================================
-- Phase 2 재실행을 위한 관계 데이터 초기화
-- ============================================================

-- 기존 관계 삭제
DELETE FROM playbook_semantic_relations;

-- 통계 확인
SELECT
    'playbook_semantic_terms' as table_name,
    COUNT(*) as count
FROM playbook_semantic_terms

UNION ALL

SELECT
    'playbook_semantic_relations' as table_name,
    COUNT(*) as count
FROM playbook_semantic_relations

UNION ALL

SELECT
    'playbook_ontology_rules' as table_name,
    COUNT(*) as count
FROM playbook_ontology_rules;

-- 완료 메시지
SELECT '✅ Phase 2 데이터 초기화 완료 - 관계 데이터 삭제됨' as message;
