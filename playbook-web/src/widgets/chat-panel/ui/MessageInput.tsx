/**
 * Chat Panel Widget - Message Input Component
 *
 * 메시지 입력 컴포넌트
 */
'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Send } from 'lucide-react'

interface MessageInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function MessageInput({ onSend, disabled = false }: MessageInputProps) {
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (!input.trim() || disabled) return
    onSend(input)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex gap-2">
      <Input
        placeholder="질문을 입력하세요... (예: 클로버는 뭐야?)"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className="flex-1 bg-white border-gray-300"
      />
      <Button
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white"
      >
        <Send className="h-4 w-4" />
      </Button>
    </div>
  )
}
