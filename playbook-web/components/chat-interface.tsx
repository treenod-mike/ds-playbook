/**
 * Chat Interface - Main Container
 *
 * FSD 2.1 Structure:
 * - Widgets: ChatPanel, GraphPanel
 * - Entities: messageApi, ChatMessage types
 */
'use client'

import { useState } from 'react'
import { ChatPanel } from '@/src/widgets/chat-panel'
import { GraphPanel } from '@/src/widgets/knowledge-graph-panel'
import { messageApi, type ChatMessage, type GraphData } from '@/src/entities'

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [currentGraphData, setCurrentGraphData] = useState<GraphData | null>(null)

  const handleSendMessage = async (userMessage: string) => {
    if (!userMessage.trim() || isLoading) return

    // Add user message
    const newMessages: ChatMessage[] = [
      ...messages,
      { role: 'user', content: userMessage },
    ]
    setMessages(newMessages)
    setIsLoading(true)

    try {
      // Call API using entity layer
      const response = await messageApi.sendMessage({
        messages: newMessages.map(m => ({ role: m.role, content: m.content })),
        use_graph: true,
      })

      // Update graph data if available
      if (response.graph_data) {
        setCurrentGraphData(response.graph_data)
      }

      // Add assistant message
      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: response.message,
          graphData: response.graph_data,
          searchProcess: response.search_process,
        },
      ])
    } catch (error: any) {
      console.error('Chat error:', error)
      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: `❌ 에러가 발생했습니다: ${error.message || '알 수 없는 오류'}`,
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-blue-50 to-purple-50 overflow-hidden">
      {/* Chat Panel - 40% */}
      <ChatPanel
        messages={messages}
        isLoading={isLoading}
        onSendMessage={handleSendMessage}
      />

      {/* Knowledge Graph Panel - 60% */}
      <div className="w-3/5 h-screen p-4">
        <GraphPanel data={currentGraphData} />
      </div>
    </div>
  )
}
