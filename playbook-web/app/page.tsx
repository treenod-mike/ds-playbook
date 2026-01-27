'use client'

import { useState } from 'react'
import ChatInterface from '@/components/chat-interface'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Project Playbook
              </h1>
              <p className="text-sm text-muted-foreground">
                GraphRAG Knowledge Graph Testing Interface
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">
                PokoPoko GraphRAG
              </span>
              <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-4 max-w-6xl h-[calc(100vh-88px)]">
        <ChatInterface />
      </div>
    </main>
  )
}
