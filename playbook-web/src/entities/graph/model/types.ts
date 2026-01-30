/**
 * Graph Entity - Types
 *
 * 지식 그래프 관련 타입 정의
 */

export interface GraphNode {
  id: string
  label: string
  category: string
  group?: string
}

export interface GraphEdge {
  from: string
  to: string
  label: string
  confidence: number
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}
