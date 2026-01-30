/**
 * Chat Panel Widget - Suggested Questions Component
 *
 * 추천 질문 컴포넌트
 */
'use client'

import { Button } from '@/components/ui/button'

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void
}

const SUGGESTED_QUESTIONS = [
  '클로버는 어디에 쓰나요?',
  '포코숲 리그는 뭐야?',
  '모험 81 챕터 보상이 뭐야?',
  '이벤트 스테이지는?',
]

export function SuggestedQuestions({ onSelect }: SuggestedQuestionsProps) {
  return (
    <div className="space-y-2">
      <p className="text-xs text-slate-500 font-medium">💡 추천 질문</p>
      <div className="flex flex-wrap gap-2">
        {SUGGESTED_QUESTIONS.map((question, idx) => (
          <Button
            key={idx}
            variant="outline"
            size="sm"
            onClick={() => onSelect(question)}
            className="bg-slate-800 border-slate-600 hover:bg-slate-700 text-slate-300 text-xs"
          >
            {question}
          </Button>
        ))}
      </div>
    </div>
  )
}
