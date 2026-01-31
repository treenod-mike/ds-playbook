'use client';

import { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Connection,
  addEdge,
  Panel,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

interface GraphData {
  nodes: Array<{
    id: string;
    label: string;
    category?: string;
    group?: string;
  }>;
  edges?: Array<{
    from: string;
    to: string;
    label: string;
    confidence?: number;
  }>;
  links?: Array<{
    source: string;
    target: string;
    label: string;
    confidence?: number;
  }>;
}

interface KnowledgeGraphProps {
  data: GraphData | null;
  onNodeClick?: (nodeId: string, nodeData: any) => void;
}

// 카테고리별 색상 (다크모드)
const CATEGORY_COLORS: Record<string, string> = {
  'Content': '#22c55e',      // green-500
  'GameObject': '#3b82f6',   // blue-500
  'Currency_Soft': '#eab308', // yellow-500
  'Currency_Hard': '#ef4444', // red-500
  'Resource': '#a855f7',     // purple-500
  'Mechanic': '#f97316',     // orange-500
  'Difficulty': '#ec4899',   // pink-500
  'Metric': '#06b6d4',       // cyan-500
  'UX_Factor': '#8b5cf6',    // violet-500
  'Condition': '#64748b',    // slate-500
  'System': '#6366f1',       // indigo-500
};

const DEFAULT_COLOR = '#475569'; // slate-600

export default function KnowledgeGraph({ data, onNodeClick }: KnowledgeGraphProps) {
  const [selectedNode, setSelectedNode] = useState<any>(null);

  // Transform API data to ReactFlow format
  const transformData = useCallback((graphData: GraphData | null) => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
      return { nodes: [], edges: [] };
    }

    // 중심 노드 찾기 (첫 번째 노드 = 사용자가 질문한 핵심 노드)
    const centerNodeId = graphData.nodes[0]?.id;

    // 노드 변환 - 방사형 레이아웃
    const nodes: Node[] = graphData.nodes.map((node, index) => {
      const category = node.category || node.group || 'Unknown';
      const color = CATEGORY_COLORS[category] || DEFAULT_COLOR;
      const isCenterNode = node.id === centerNodeId;

      // 방사형 배치 계산
      let position;
      if (isCenterNode) {
        // 중심 노드는 정중앙
        position = { x: 400, y: 300 };
      } else {
        // 주변 노드는 원형으로 배치
        const angle = (2 * Math.PI * (index - 1)) / (graphData.nodes.length - 1);
        const radius = 250;
        position = {
          x: 400 + radius * Math.cos(angle),
          y: 300 + radius * Math.sin(angle)
        };
      }

      return {
        id: node.id,
        type: 'default',
        position,
        data: {
          label: (
            <div className="text-center px-2 py-1">
              <div className={`font-semibold ${isCenterNode ? 'text-base' : 'text-sm'}`}>
                {isCenterNode && '🎯 '}
                {node.label}
              </div>
              <div className={`text-xs font-medium mt-1 px-2 py-0.5 rounded ${
                isCenterNode
                  ? 'bg-orange-600 bg-opacity-50'
                  : 'bg-black bg-opacity-30'
              }`}>
                {category}
              </div>
            </div>
          ),
          category,
          rawLabel: node.label,
          isCenterNode,
        },
        style: {
          background: isCenterNode ? '#f59e0b' : color, // 중심 노드는 황금색
          color: 'white',
          border: isCenterNode ? '4px solid #fbbf24' : '2px solid rgba(255, 255, 255, 0.2)',
          borderRadius: '12px',
          padding: isCenterNode ? '12px' : '8px',
          fontSize: isCenterNode ? '14px' : '12px',
          width: 'auto',
          minWidth: isCenterNode ? '160px' : '130px',
          boxShadow: isCenterNode ? '0 4px 20px rgba(245, 158, 11, 0.5)' : 'none',
          zIndex: isCenterNode ? 10 : 1,
        },
      };
    });

    // 엣지 변환 (edges 또는 links 필드 지원)
    const edgeData = graphData.edges || graphData.links || [];
    const edges: Edge[] = edgeData.map((edge, index) => {
      const sourceId = 'from' in edge ? edge.from : edge.source;
      const targetId = 'to' in edge ? edge.to : edge.target;
      const confidence = edge.confidence || 1.0;

      // 중심 노드와 연결된 엣지인지 확인
      const isConnectedToCenter = sourceId === centerNodeId || targetId === centerNodeId;
      const confidencePercent = Math.round(confidence * 100);

      return {
        id: `edge-${index}`,
        source: sourceId,
        target: targetId,
        label: `${edge.label} (${confidencePercent}%)`, // predicate + 신뢰도 %
        type: 'smoothstep',
        animated: confidence > 0.9,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: isConnectedToCenter ? 30 : 25, // 중심 노드 연결 엣지는 더 큼
          height: isConnectedToCenter ? 30 : 25,
          color: confidence > 0.9 ? '#22c55e' : '#eab308',
        },
        style: {
          stroke: confidence > 0.9 ? '#22c55e' : '#eab308',
          strokeWidth: isConnectedToCenter ? 3 : 2.5, // 중심 노드 연결 엣지는 더 두껍게
        },
        labelStyle: {
          fill: '#e2e8f0',
          fontSize: 12,
          fontWeight: 700,
        },
        labelBgStyle: {
          fill: '#1e293b',
          fillOpacity: 0.9,
          borderRadius: 4,
        },
        labelBgPadding: [8, 4],
        labelBgBorderRadius: 4,
      };
    });

    return { nodes, edges };
  }, []);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // 데이터 변경 시 그래프 업데이트
  useEffect(() => {
    const { nodes: newNodes, edges: newEdges } = transformData(data);
    setNodes(newNodes);
    setEdges(newEdges);
  }, [data, setNodes, setEdges, transformData]);

  const onNodeClickHandler = useCallback(
    (event: React.MouseEvent, node: Node) => {
      setSelectedNode(node.data);
      if (onNodeClick) {
        onNodeClick(node.id, node.data);
      }
    },
    [onNodeClick]
  );

  // 엣지 연결 (인터랙티브 편집 가능하게)
  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-900 rounded-lg border border-slate-700">
        <div className="text-center text-slate-400">
          <div className="text-4xl mb-4">🌐</div>
          <p className="text-sm">그래프 데이터를 기다리는 중...</p>
          <p className="text-xs mt-2">질문을 하면 지식 그래프가 표시됩니다</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-slate-900 rounded-lg border border-slate-700 overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClickHandler}
        fitView
        attributionPosition="bottom-left"
        className="bg-slate-900"
      >
        <Background color="#475569" gap={16} />
        <Controls className="bg-slate-800 border-slate-700" />
        <MiniMap
          nodeColor={(node) => {
            const category = node.data?.category || 'Unknown';
            return CATEGORY_COLORS[category] || DEFAULT_COLOR;
          }}
          maskColor="rgba(15, 23, 42, 0.8)"
          className="bg-slate-800 border-slate-700"
        />

        {/* 상단 정보 패널 */}
        <Panel position="top-left" className="bg-slate-800 border border-slate-700 rounded-lg p-3">
          <div className="text-xs text-slate-300">
            <div className="font-semibold mb-1">📊 지식 그래프</div>
            <div className="flex gap-4">
              <span>노드: {nodes.length}개</span>
              <span>관계: {edges.length}개</span>
            </div>
          </div>
        </Panel>

        {/* 선택된 노드 상세 정보 */}
        {selectedNode && (
          <Panel position="top-right" className="bg-slate-800 border border-slate-700 rounded-lg p-3 max-w-xs">
            <div className="text-xs text-slate-300">
              <div className="font-semibold mb-2">🔍 노드 상세</div>
              <div className="space-y-1">
                <div><span className="text-slate-500">이름:</span> {selectedNode.rawLabel}</div>
                <div><span className="text-slate-500">카테고리:</span> {selectedNode.category}</div>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="mt-2 text-xs text-blue-400 hover:text-blue-300"
              >
                닫기
              </button>
            </div>
          </Panel>
        )}

        {/* 범례 (Legend) */}
        <Panel position="bottom-right" className="bg-slate-800 border border-slate-700 rounded-lg p-3 max-h-96 overflow-y-auto">
          <div className="text-xs text-slate-400">
            <div className="font-semibold mb-2 text-slate-200">📌 범례</div>

            {/* 노드 카테고리 */}
            <div className="mb-3">
              <div className="text-[11px] font-semibold text-slate-300 mb-1.5">노드 카테고리</div>
              <div className="space-y-1">
                {Object.entries(CATEGORY_COLORS).map(([category, color]) => (
                  <div key={category} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded" style={{ backgroundColor: color }}></div>
                    <span className="text-[11px]">{category}</span>
                  </div>
                ))}
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-orange-500"></div>
                  <span className="text-[11px]">중심 노드 🎯</span>
                </div>
              </div>
            </div>

            {/* 엣지 신뢰도 */}
            <div className="pt-2 border-t border-slate-700">
              <div className="text-[11px] font-semibold text-slate-300 mb-1.5">엣지 신뢰도</div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-[11px]">신뢰도 높음 (&gt;0.9)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <span className="text-[11px]">신뢰도 보통 (≤0.9)</span>
                </div>
              </div>
            </div>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}
