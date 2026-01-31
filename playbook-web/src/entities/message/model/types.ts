/**
 * Message Entity - Types
 *
 * 채팅 메시지 관련 타입 정의
 */
import type { GraphData } from '../../graph'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  graphData?: GraphData
  searchProcess?: SearchProcess
}

export interface SearchProcess {
  steps: Array<{
    step: number
    name: string
    description: string
  }>
  found_terms: Array<{
    term: string
    category: string
  }>
  center_term: string | null
  nodes_count: number
  edges_count: number
  traversal_log?: string[]
  reasoning_chain?: string[]
  chunks_referenced?: Array<{
    chunk_id: string
    content: string
    relevance_score?: number
  }>
}

export interface ChatRequest {
  messages: Array<{
    role: string
    content: string
  }>
  use_graph: boolean
}

export interface ChatResponse {
  message: string
  graph_data?: GraphData
  search_process?: SearchProcess
}
