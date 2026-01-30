/**
 * Message Entity - UI Component
 *
 * 메시지 카드 컴포넌트
 */
import { Avatar } from '@/components/ui/avatar'
import { Bot, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface MessageCardProps {
  role: 'user' | 'assistant'
  content: string
}

export function MessageCard({ role, content }: MessageCardProps) {
  const isUser = role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <Avatar className="h-8 w-8 bg-blue-500 flex items-center justify-center">
          <Bot className="h-5 w-5 text-white" />
        </Avatar>
      )}

      <div
        className={`
          max-w-[80%] rounded-lg px-4 py-2
          ${isUser ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-100'}
        `}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{content}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="mb-2 ml-4 list-disc">{children}</ul>,
                ol: ({ children }) => <ol className="mb-2 ml-4 list-decimal">{children}</ol>,
                li: ({ children }) => <li className="mb-1">{children}</li>,
                strong: ({ children }) => <strong className="font-bold text-white">{children}</strong>,
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        )}
      </div>

      {isUser && (
        <Avatar className="h-8 w-8 bg-green-500 flex items-center justify-center">
          <User className="h-5 w-5 text-white" />
        </Avatar>
      )}
    </div>
  )
}
