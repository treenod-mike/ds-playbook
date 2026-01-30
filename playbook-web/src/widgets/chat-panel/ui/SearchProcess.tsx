/**
 * Chat Panel Widget - Search Process Component
 *
 * 검색 과정 표시 컴포넌트
 */
'use client'

import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { ChevronDown, ChevronUp } from 'lucide-react'
import type { SearchProcess as SearchProcessType } from '@/src/entities/message'

interface SearchProcessProps {
  process: SearchProcessType
}

export function SearchProcess({ process }: SearchProcessProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="mt-2 bg-slate-800 rounded-lg p-3 text-sm">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full text-left"
      >
        <span className="text-slate-300 font-medium">
          🔍 검색 과정 ({process.steps.length}단계)
        </span>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-slate-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-slate-400" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-3 space-y-2">
          {/* Steps */}
          {process.steps.map((step, idx) => (
            <div key={idx} className="flex gap-2">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold">
                {step.step}
              </div>
              <div className="flex-1">
                <div className="font-medium text-slate-200">{step.name}</div>
                <div className="text-xs text-slate-400 mt-1">{step.description}</div>
              </div>
            </div>
          ))}

          {/* Found Terms */}
          {process.found_terms && process.found_terms.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-700">
              <div className="text-slate-300 font-medium mb-2">
                발견된 용어 ({process.found_terms.length}개)
              </div>
              <div className="flex flex-wrap gap-2">
                {process.found_terms.map((term, idx) => (
                  <Badge key={idx} variant="secondary" className="bg-slate-700">
                    {term.term} ({term.category})
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Graph Stats */}
          {process.nodes_count > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-700">
              <div className="text-slate-300 text-xs">
                📊 그래프: 노드 {process.nodes_count}개, 관계 {process.edges_count}개
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
