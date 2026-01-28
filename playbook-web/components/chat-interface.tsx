'use client'

import { useState, useRef, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Send, Loader2, Bot, User } from 'lucide-react'
import axios from 'axios'

interface Message {
  role: 'user' | 'assistant'
  content: string
  searchProcess?: {
    steps: Array<{ step: number; name: string; description: string }>
    found_terms: Array<{ term: string; category: string }>
    center_term: string | null
    nodes_count: number
    edges_count: number
    traversal_log?: string[]
  }
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = async (question?: string) => {
    const userMessage = question || input
    if (!userMessage.trim() || isLoading) return

    // Add user message
    const newMessages: Message[] = [
      ...messages,
      { role: 'user', content: userMessage },
    ]
    setMessages(newMessages)
    setInput('')
    setIsLoading(true)

    try {
      // Call chat API
      const response = await axios.post(`${BACKEND_URL}/api/chat`, {
        messages: newMessages,
        use_graph: true,
      })

      const { message, search_process } = response.data

      // Update messages with assistant response
      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: message,
          searchProcess: search_process,
        },
      ])
    } catch (error: any) {
      console.error('Chat error:', error)

      let errorMessage = '죄송합니다. 오류가 발생했습니다.'

      if (error.response?.status === 503) {
        errorMessage = '⚠️ 채팅 서비스를 사용할 수 없습니다. OPENAI_API_KEY가 설정되지 않았습니다.'
      } else if (error.response?.data?.detail) {
        errorMessage = `오류: ${error.response.data.detail}`
      }

      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: errorMessage,
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <Card className="flex flex-col shadow-lg h-full w-full">
        {/* Header */}
        <div className="p-4 border-b bg-gradient-to-r from-blue-50 to-purple-50 flex-shrink-0">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10 bg-gradient-to-br from-blue-500 to-purple-500">
              <div className="flex items-center justify-center h-full w-full">
                <Bot className="h-6 w-6 text-white" />
              </div>
            </Avatar>
            <div>
              <h3 className="font-semibold text-lg">GraphRAG Test Assistant</h3>
              <p className="text-xs text-muted-foreground">
                Semantic Relation Table Verification
              </p>
            </div>
          </div>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 p-4 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center space-y-6 p-8">
              <div className="text-center space-y-3">
                <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  PokoPoko GraphRAG
                </h2>
                <p className="text-sm text-muted-foreground max-w-md">
                  지식 그래프 기반으로 게임 콘텐츠에 대해 질문해보세요
                </p>
                <p className="text-xs text-slate-500 mt-2">
                  현재 DB: 1,733개 문서 | 11,971개 용어 | 104개 관계
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-3 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.role === 'assistant' && (
                <Avatar className="h-8 w-8 bg-gradient-to-br from-blue-500 to-purple-500 flex-shrink-0">
                  <div className="flex items-center justify-center h-full w-full">
                    <Bot className="h-5 w-5 text-white" />
                  </div>
                </Avatar>
              )}

              <div
                className={`rounded-2xl px-4 py-3 max-w-[85%] ${
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white ml-auto'
                    : 'bg-slate-100 text-slate-900'
                }`}
              >
                {message.role === 'assistant' && message.searchProcess && (
                  <div className="mb-3 pb-3 border-b border-slate-300">
                    <div className="text-xs font-semibold text-slate-600 mb-2">🔍 검색 과정</div>
                    <div className="space-y-1">
                      {message.searchProcess.steps.map((step, idx) => (
                        <div key={idx} className="text-xs text-slate-600">
                          <span className="font-medium">{step.step}.</span> {step.name}
                          {step.description.includes('\n추론 체인:') ? (
                            <div className="mt-1">
                              <span className="text-slate-500">
                                {step.description.split('\n추론 체인:')[0]}
                              </span>
                              <div className="mt-1 p-2 bg-purple-50 rounded border border-purple-200">
                                <div className="text-xs font-medium text-purple-700 mb-1">🔗 추론 체인</div>
                                <div className="text-xs text-purple-600 font-mono break-words">
                                  {step.description.split('\n추론 체인:')[1]}
                                </div>
                              </div>
                            </div>
                          ) : (
                            <span className="text-slate-500">: {step.description}</span>
                          )}
                        </div>
                      ))}
                    </div>
                    {message.searchProcess.found_terms.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {message.searchProcess.found_terms.map((term, idx) => (
                          <span key={idx} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                            {term.term} ({term.category})
                          </span>
                        ))}
                      </div>
                    )}

                    {message.searchProcess.traversal_log && message.searchProcess.traversal_log.length > 0 && (
                      <div className="mt-3 p-3 bg-amber-50 rounded border border-amber-200">
                        <div className="text-xs font-medium text-amber-700 mb-2">🔎 BFS 탐색 로그 (상세)</div>
                        <div className="space-y-0.5 max-h-48 overflow-y-auto">
                          {message.searchProcess.traversal_log.map((log, idx) => (
                            <div key={idx} className="text-xs font-mono text-amber-900 whitespace-pre-wrap">
                              {log}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                <div className="text-sm whitespace-pre-wrap leading-relaxed">
                  {message.content}
                </div>
              </div>

              {message.role === 'user' && (
                <Avatar className="h-8 w-8 bg-slate-300 flex-shrink-0">
                  <div className="flex items-center justify-center h-full w-full">
                    <User className="h-5 w-5 text-slate-600" />
                  </div>
                </Avatar>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3">
              <Avatar className="h-8 w-8 bg-gradient-to-br from-blue-500 to-purple-500">
                <div className="flex items-center justify-center h-full w-full">
                  <Bot className="h-5 w-5 text-white" />
                </div>
              </Avatar>
              <div className="rounded-2xl px-4 py-3 bg-slate-100">
                <Loader2 className="h-5 w-5 animate-spin text-slate-600" />
              </div>
            </div>
          )}

              {/* Auto-scroll anchor */}
              <div ref={messagesEndRef} />
            </div>
          )}
        </ScrollArea>

        {/* Input */}
        <div className="p-4 border-t bg-white flex-shrink-0">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="관계 테이블 검증을 위한 질문을 입력하세요..."
              disabled={isLoading}
              className="flex-1"
            />
            <Button
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              size="icon"
              className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </Card>
  )
}
