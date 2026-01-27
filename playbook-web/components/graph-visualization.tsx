'use client'

import { useCallback, useEffect } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'

interface GraphVisualizationProps {
  data: {
    nodes: Array<{ id: string; label: string; category: string }>
    edges: Array<{
      from: string
      to: string
      label: string
      confidence?: number
    }>
  } | null
}

const categoryColors: Record<string, string> = {
  Content: '#3b82f6', // blue
  GameObject: '#10b981', // green
  Resource: '#f59e0b', // amber
  Mechanic: '#8b5cf6', // purple
  Condition: '#ef4444', // red
  System: '#6366f1', // indigo
  Metric: '#ec4899', // pink
  default: '#64748b', // slate
}

export default function GraphVisualization({
  data,
}: GraphVisualizationProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  useEffect(() => {
    if (!data || !data.nodes || data.nodes.length === 0) {
      setNodes([])
      setEdges([])
      return
    }

    console.log('Graph data:', data) // Debug

    // Convert to ReactFlow format
    const flowNodes: Node[] = data.nodes.map((node, index) => {
      const color = categoryColors[node.category] || categoryColors.default
      const angle = (index * 2 * Math.PI) / data.nodes.length
      const radius = data.nodes.length > 3 ? 250 : 150

      return {
        id: node.id,
        type: 'default',
        data: {
          label: (
            <div className="text-center px-2">
              <div className="font-semibold text-sm whitespace-nowrap">
                {node.label}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {node.category}
              </div>
            </div>
          ),
        },
        position: {
          x: Math.cos(angle) * radius + 300,
          y: Math.sin(angle) * radius + 300,
        },
        style: {
          background: 'white',
          color: color,
          border: `3px solid ${color}`,
          borderRadius: '12px',
          padding: '12px 16px',
          fontSize: '13px',
          minWidth: 120,
          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
        },
      }
    })

    const flowEdges: Edge[] = (data.edges || []).map((edge, index) => ({
      id: `edge-${index}`,
      source: edge.from,
      target: edge.to,
      label: `${edge.label}${edge.confidence ? ` (${(edge.confidence * 100).toFixed(0)}%)` : ''}`,
      type: 'smoothstep',
      animated: true,
      style: {
        stroke: '#64748b',
        strokeWidth: 2.5,
      },
      labelStyle: {
        fill: '#475569',
        fontSize: 11,
        fontWeight: 600,
        background: 'white',
      },
      labelBgStyle: {
        fill: 'white',
        fillOpacity: 0.95,
        rx: 4,
        ry: 4,
      },
      labelBgPadding: [8, 4] as [number, number],
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#64748b',
        width: 20,
        height: 20,
      },
    }))

    console.log('Flow nodes:', flowNodes.length, 'Flow edges:', flowEdges.length) // Debug

    setNodes(flowNodes)
    setEdges(flowEdges)
  }, [data, setNodes, setEdges])

  return (
    <div className="h-full w-full rounded-lg overflow-hidden border border-slate-200">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        fitViewOptions={{ padding: 0.2, minZoom: 0.5, maxZoom: 1.5 }}
        attributionPosition="bottom-right"
        minZoom={0.1}
        maxZoom={2}
      >
        <Background color="#e2e8f0" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const style = node.style as any
            return style?.border?.match(/#[0-9a-f]{6}/i)?.[0] || categoryColors.default
          }}
          maskColor="rgba(0, 0, 0, 0.05)"
          style={{
            background: 'white',
            border: '1px solid #e2e8f0',
          }}
        />
      </ReactFlow>
    </div>
  )
}
