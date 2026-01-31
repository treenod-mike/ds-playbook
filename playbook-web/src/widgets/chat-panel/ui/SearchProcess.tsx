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
    <div className="mt-2 bg-purple-50 border border-purple-200 rounded-lg p-3 text-sm">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full text-left"
      >
        <span className="text-purple-900 font-medium">
          🔍 검색 과정 ({process.steps.length}단계)
        </span>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-purple-600" />
        ) : (
          <ChevronDown className="h-4 w-4 text-purple-600" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-3 space-y-3">
          {/* Search Steps - 회색 박스 */}
          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
            <div className="text-gray-700 font-semibold mb-2 text-xs">
              📋 검색 단계 (Search Steps)
            </div>
            <div className="space-y-1">
              {process.steps.map((step, idx) => (
                <div key={idx} className="text-xs text-gray-600">
                  <span className="font-mono bg-gray-200 px-1.5 py-0.5 rounded text-gray-800 font-semibold">
                    Step {step.step}
                  </span>
                  <span className="ml-2 font-medium text-gray-700">{step.name}</span>
                  {step.description && (
                    <div className="ml-14 text-gray-500 mt-0.5">{step.description}</div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Reasoning Chain - 보라색 박스 */}
          {process.reasoning_chain && process.reasoning_chain.length > 0 && (
            <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
              <div className="text-purple-900 font-semibold mb-2 text-xs">
                🧠 추론 체인 (Reasoning Chain)
              </div>
              <div className="space-y-1.5">
                {process.reasoning_chain.map((chain, idx) => (
                  <div key={idx} className="text-xs">
                    <div className="flex items-start gap-2">
                      <span className="flex-shrink-0 font-mono bg-purple-200 px-1.5 py-0.5 rounded text-purple-900 font-semibold text-[10px]">
                        {idx + 1}
                      </span>
                      <div className="flex-1 text-purple-900 font-mono break-words">
                        {chain}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Found Terms */}
          {process.found_terms && process.found_terms.length > 0 && (
            <div className="bg-white rounded-lg p-3 border border-purple-100">
              <div className="text-purple-900 font-semibold mb-2 text-xs">
                🔍 발견된 용어 ({process.found_terms.length}개)
              </div>
              <div className="flex flex-wrap gap-2">
                {process.found_terms.map((term, idx) => (
                  <Badge key={idx} variant="secondary" className="bg-purple-100 text-purple-800 border border-purple-200 text-xs">
                    {term.term} ({term.category})
                  </Badge>
                ))}
              </div>
              {process.center_term && (
                <div className="mt-2 text-xs text-purple-700">
                  <span className="font-semibold">중심 용어:</span> {process.center_term}
                </div>
              )}
            </div>
          )}

          {/* Traversal Log with Hop Information */}
          {process.traversal_log && process.traversal_log.length > 0 && (
            <div className="bg-amber-50 rounded-lg p-3 border border-amber-200">
              <div className="text-amber-900 font-semibold mb-2 text-xs">
                🔄 그래프 순회 로그 (Hop Traversal)
              </div>
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {process.traversal_log.map((log, idx) => (
                  <div key={idx} className="text-xs text-amber-800 font-mono bg-white px-2 py-1 rounded border border-amber-100">
                    <span className="text-amber-600 font-bold">Hop {idx + 1}:</span> {log}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Graph Stats */}
          {process.nodes_count > 0 && (
            <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
              <div className="text-blue-900 text-xs">
                📊 <span className="font-semibold">서브그래프 통계:</span> 노드 {process.nodes_count}개, 관계 {process.edges_count}개
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
