/**
 * Chat Panel Widget - Main Component
 *
 * 채팅 패널 메인 컴포넌트
 */
'use client'

import { useState, useRef, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { MessageCard } from '@/src/entities/message'
import { MessageInput } from './MessageInput'
import { SearchProcess } from './SearchProcess'
import { SuggestedQuestions } from './SuggestedQuestions'
import type { ChatMessage } from '@/src/entities/message'

interface ChatPanelProps {
  messages: ChatMessage[]
  isLoading: boolean
  onSendMessage: (message: string) => void
}

export function ChatPanel({ messages, isLoading, onSendMessage }: ChatPanelProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <Card className="w-2/5 h-screen flex flex-col bg-slate-900 border-slate-700">
      {/* Header */}
      <div className="p-4 border-b border-slate-700">
        <h2 className="text-xl font-bold text-white">💬 PokoPoko 지식 그래프 챗봇</h2>
        <p className="text-sm text-slate-400 mt-1">
          용어를 물어보면 지식 그래프를 기반으로 답변합니다
        </p>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-slate-400 mt-8">
              <div className="text-6xl mb-4">🤖</div>
              <p className="text-lg">질문을 입력해주세요</p>
              <p className="text-sm mt-2">예: &quot;클로버는 어디에 쓰나요?&quot;</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx}>
              <MessageCard role={msg.role} content={msg.content} />

              {/* Show search process for assistant messages */}
              {msg.role === 'assistant' && msg.searchProcess && (
                <SearchProcess process={msg.searchProcess} />
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-slate-800 rounded-lg px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce delay-100" />
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce delay-200" />
                  <span className="text-slate-400 ml-2">생각하는 중...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Suggested Questions */}
      {messages.length === 0 && (
        <div className="px-4 pb-2">
          <SuggestedQuestions onSelect={onSendMessage} />
        </div>
      )}

      {/* Input Area */}
      <div className="p-4 border-t border-slate-700">
        <MessageInput
          onSend={onSendMessage}
          disabled={isLoading}
        />
      </div>
    </Card>
  )
}
