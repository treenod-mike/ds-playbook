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
    <Card className="w-2/5 h-screen flex flex-col shadow-lg">
      {/* Header */}
      <div className="p-4 border-b bg-gradient-to-r from-blue-50 to-purple-50 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
            <span className="text-white text-xl">🤖</span>
          </div>
          <div>
            <h3 className="font-semibold text-lg">GraphRAG Test Assistant</h3>
            <p className="text-xs text-muted-foreground">
              Semantic Relation Table Verification
            </p>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4 overflow-y-auto">
        <div className="space-y-4">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center space-y-6 p-8">
              <div className="text-center space-y-3">
                <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  PokoPoko GraphRAG
                </h2>
                <p className="text-sm text-muted-foreground max-w-md">
                  지식 그래프 기반으로 게임 콘텐츠에 대해 질문해보세요
                </p>
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx}>
              {/* Show search process BEFORE assistant messages */}
              {msg.role === 'assistant' && msg.searchProcess && (
                <SearchProcess process={msg.searchProcess} />
              )}

              <MessageCard role={msg.role} content={msg.content} />
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg px-4 py-3 border border-gray-200">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce delay-100" />
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce delay-200" />
                  <span className="text-gray-600 ml-2">생각하는 중...</span>
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
      <div className="p-4 border-t bg-white">
        <MessageInput
          onSend={onSendMessage}
          disabled={isLoading}
        />
      </div>
    </Card>
  )
}
