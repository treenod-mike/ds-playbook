-- =================================================================
-- Supabase Read-Only User 생성 (외부 플랫폼 공유용)
-- =================================================================
--
-- 사용 목적:
-- - 다른 사람/플랫폼에게 지식 그래프 읽기 권한만 부여
-- - 데이터 수정/삭제 불가능
-- - API 서버 배포 시 사용
--
-- =================================================================

-- 1. Read-Only Role 생성
CREATE ROLE playbook_reader;

-- 2. 읽기 권한 부여
GRANT USAGE ON SCHEMA public TO playbook_reader;

-- 테이블별 SELECT 권한
GRANT SELECT ON playbook_documents TO playbook_reader;
GRANT SELECT ON playbook_chunks TO playbook_reader;
GRANT SELECT ON playbook_semantic_terms TO playbook_reader;
GRANT SELECT ON playbook_ontology_rules TO playbook_reader;
GRANT SELECT ON playbook_semantic_relations TO playbook_reader;

-- View 접근 권한
GRANT SELECT ON playbook_knowledge_graph TO playbook_reader;

-- 함수 실행 권한 (search_terms)
GRANT EXECUTE ON FUNCTION search_terms(TEXT) TO playbook_reader;

-- 3. Read-Only User 생성 (실제 사용자)
-- 비밀번호는 강력하게 설정하세요!
CREATE USER playbook_api_user WITH PASSWORD 'your_strong_password_here';

-- 4. Role 할당
GRANT playbook_reader TO playbook_api_user;

-- =================================================================
-- 사용법:
-- =================================================================
--
-- 1. Supabase SQL Editor에서 이 스크립트 실행
-- 2. 비밀번호를 강력한 것으로 변경
-- 3. Connection String 공유:
--    postgresql://playbook_api_user:password@db.xxx.supabase.co:5432/postgres
--
-- 4. 또는 Supabase REST API로 접근 (anon key 대신 service_role key 필요)
--
-- =================================================================

-- 권한 확인
SELECT
    grantee,
    table_name,
    privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'playbook_reader';

-- =================================================================
-- 주의사항:
-- =================================================================
--
-- ⚠️  이 방법은 PostgreSQL 직접 접근이 필요합니다.
-- ⚠️  Supabase의 anon key는 RLS(Row Level Security)를 사용합니다.
-- ⚠️  RLS가 활성화되면 읽기 권한도 제한될 수 있습니다.
--
-- 더 나은 방법:
-- - Option A (각자 Supabase 프로젝트) 추천
-- - Option C (당신이 API 서버 호스팅) 추천
--
-- =================================================================
