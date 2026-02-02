-- ============================================================
-- Phase 2 재실행을 위한 관계 데이터 초기화
--
-- 실행 방법:
-- 1. Supabase Dashboard 접속
-- 2. SQL Editor 선택
-- 3. 이 SQL을 붙여넣고 실행 (Run)
-- ============================================================

-- 삭제 전 현재 상태 확인
SELECT
    '📊 삭제 전 상태' as info,
    (SELECT COUNT(*) FROM playbook_semantic_terms) as terms_count,
    (SELECT COUNT(*) FROM playbook_semantic_relations) as relations_count,
    (SELECT COUNT(*) FROM playbook_ontology_rules) as rules_count;

-- 기존 관계 삭제
DELETE FROM playbook_semantic_relations;

-- 삭제 후 상태 확인
SELECT
    '✅ 삭제 후 상태' as info,
    (SELECT COUNT(*) FROM playbook_semantic_terms) as terms_count,
    (SELECT COUNT(*) FROM playbook_semantic_relations) as relations_count,
    (SELECT COUNT(*) FROM playbook_ontology_rules) as rules_count;

-- 완료 메시지
SELECT '✅ Phase 2 데이터 초기화 완료!' as message,
       'python3 src/core/processors/ontology_builder.py' as next_step;
