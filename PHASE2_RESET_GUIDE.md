# Phase 2 재실행 가이드 (v3.1)

최신성 가중치를 적용하기 위한 Phase 2 재실행 가이드입니다.

## 🚀 빠른 실행 (추천)

### Step 1: Supabase에서 관계 삭제

1. **Supabase Dashboard** 접속
2. 왼쪽 메뉴에서 **SQL Editor** 선택
3. 다음 SQL 실행:

```sql
DELETE FROM playbook_semantic_relations;
```

4. **Run** 버튼 클릭 (약 1-2초 소요)

---

### Step 2: Phase 2 재실행

터미널에서 실행:

```bash
python3 src/core/processors/ontology_builder.py
```

**예상 소요시간**: 약 10-15분

---

## 📊 실행 결과 확인

```bash
# 통계 확인
python3 << 'EOF'
import sys, os
env_path = '.env'
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"').strip("'")

from supabase import create_client
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_KEY')
supabase = create_client(url, key)

relations = supabase.table('playbook_semantic_relations').select('id', count='exact').execute()
print(f"✅ 관계 수: {relations.count:,}개")
EOF
```

---

## 🎯 기대 효과

### v3.1 최신성 가중치 적용

관계 생성 시 문서 날짜에 따라 가중치 부여:

| 문서 연령 | 문서 수 | 가중치 | 효과 |
|----------|---------|--------|------|
| 최근 1개월 | 93개 | 1.5x | +50% |
| 최근 3개월 | 225개 | 1.3x | +30% |
| 최근 6개월 | 438개 | 1.2x | +20% |
| 최근 1년 | 918개 | 1.1x | +10% |
| 1년 이상 | 2,645개 | 1.0x | 기본 |

### 실제 예시

**Before (v3.0)**:
```
"클로버" -consumes-> "스테이지"
  문서 날짜: 2026-01-26
  confidence: 0.8
```

**After (v3.1)**:
```
"클로버" -consumes-> "스테이지"
  문서 날짜: 2026-01-26
  confidence: 1.0 ✨ (0.8 × 1.5 = 1.2 → capped at 1.0)
  → 최신 문서는 최대 신뢰도!
```

---

## 🔧 대안: 테스트용 소규모 실행

전체 재실행이 부담스럽다면:

```bash
# 최근 10개 문서만 테스트
python3 src/core/processors/ontology_builder.py --max-docs 10

# 로그에서 가중치 적용 확인
tail -f logs/playbook.log | grep -E "recency weight|RECENCY BOOST"
```

---

## ❗ 문제 해결

### Python 스크립트로 삭제가 안 되는 경우

Supabase API 제한으로 대량 삭제가 실패할 수 있습니다.
**해결**: Supabase SQL Editor 사용 (위 Step 1 참조)

### Phase 2 실행 중 오류

```bash
# 로그 확인
tail -f logs/playbook.log

# 특정 문서만 재시도
python3 src/core/processors/ontology_builder.py --doc-ids DOC_ID_1 DOC_ID_2
```

---

## 📞 추가 도움말

더 자세한 내용은 README.md의 "Phase 2: Knowledge Graph Construction" 섹션을 참조하세요.
