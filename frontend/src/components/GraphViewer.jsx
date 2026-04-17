import { useState, useCallback, useEffect, useRef } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
} from '@xyflow/react';
import { getGraphNodes, getGraphEdges, getNodeState } from '../services/api';
import NodeTooltip from './NodeTooltip';
import {
  Database,
  FileSearch,
  RefreshCw,
  Globe,
  Filter,
  Sparkles,
  Play,
  Flag,
} from 'lucide-react';

// ── Icon map ─────────────────────────────────────
const ICONS = {
  __start__: <Play size={16} />,
  retrieve: <Database size={16} />,
  eval_each_doc: <FileSearch size={16} />,
  rewrite_query: <RefreshCw size={16} />,
  web_search: <Globe size={16} />,
  refine: <Filter size={16} />,
  generate: <Sparkles size={16} />,
  __end__: <Flag size={16} />,
};

// ── Layout positions for the CRAG graph ──────────
const POSITIONS = {
  __start__: { x: 340, y: 0 },
  retrieve: { x: 340, y: 150 },
  eval_each_doc: { x: 340, y: 300 },
  refine: { x: 340, y: 600 },
  generate: { x: 340, y: 750 },
  __end__: { x: 340, y: 900 },
  rewrite_query: { x: 680, y: 400 },
  web_search: { x: 680, y: 550 },
};

// ── Custom CRAG node component ───────────────────
function CragNode({ data }) {
  const icon = ICONS[data.nodeId] || null;
  const statusClass = `status-${data.status || 'idle'}`;

  return (
    <div className={`crag-node ${statusClass}`}>
      <Handle type="target" position={Position.Top} className="!bg-subtle !w-2 !h-2 !border-none" />
      <div className="flex items-center justify-center gap-2">
        <span className="opacity-70">{icon}</span>
        <span>{data.label}</span>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-subtle !w-2 !h-2 !border-none" />
    </div>
  );
}

const nodeTypes = { cragNode: CragNode };

// ── Main component ───────────────────────────────
export default function GraphViewer({ nodeStatuses }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [tooltip, setTooltip] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const containerRef = useRef();

  // Load graph structure on mount
  useEffect(() => {
    (async () => {
      try {
        const [nodesRes, edgesRes] = await Promise.all([
          getGraphNodes(),
          getGraphEdges(),
        ]);

        const flowNodes = nodesRes.data.nodes.map((n) => ({
          id: n.id,
          type: 'cragNode',
          position: POSITIONS[n.id] || { x: 300, y: 0 },
          data: { label: n.label, nodeId: n.id, status: 'idle' },
        }));

        const flowEdges = edgesRes.data.edges.map((e, i) => ({
          id: `e-${i}`,
          source: e.source,
          target: e.target,
          label: e.label || undefined,
          animated: false,
          style: { stroke: '#334155', strokeWidth: 1.5 },
          labelStyle: { fill: '#64748b', fontSize: 10 },
          labelBgStyle: { fill: '#111827', fillOpacity: 0.9 },
          type: 'smoothstep',
        }));

        setNodes(flowNodes);
        setEdges(flowEdges);
      } catch (err) {
        console.error('Failed to load graph:', err);
      }
    })();
  }, []);

  // Update node statuses when the prop changes
  useEffect(() => {
    if (!nodeStatuses) return;
    setNodes((prev) =>
      prev.map((n) => ({
        ...n,
        data: {
          ...n.data,
          status: nodeStatuses[n.id] || n.data.status,
        },
      }))
    );

    setEdges((prev) =>
      prev.map((e) => {
        const srcDone = nodeStatuses[e.source] === 'running' || nodeStatuses[e.source] === 'completed';
        const tgtRunning = nodeStatuses[e.target] === 'running';
        const isActive = srcDone && tgtRunning;
        const tgtDone = nodeStatuses[e.target] === 'completed';
        return {
          ...e,
          animated: isActive,
          style: {
            ...e.style,
            stroke: isActive ? '#f59e0b' : tgtDone ? '#22c55e' : '#334155',
          },
        };
      })
    );
  }, [nodeStatuses, setNodes, setEdges]);

  // Node hover → fetch state for tooltip
  const handleNodeMouseEnter = useCallback(async (event, node) => {
    const rect = containerRef.current?.getBoundingClientRect();
    const x = event.clientX - (rect?.left || 0);
    const y = event.clientY - (rect?.top || 0);
    setTooltipPos({ x, y });

    try {
      const res = await getNodeState(node.id);
      setTooltip(res.data);
    } catch {
      setTooltip(null);
    }
  }, []);

  const handleNodeMouseLeave = useCallback(() => {
    setTooltip(null);
  }, []);

  return (
    <div ref={containerRef} className="relative w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        onNodeMouseEnter={handleNodeMouseEnter}
        onNodeMouseLeave={handleNodeMouseLeave}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        proOptions={{ hideAttribution: true }}
        minZoom={0.4}
        maxZoom={1.5}
        nodesDraggable={false}
        nodesConnectable={false}
      >
        <Background color="#334155" gap={24} size={1} variant="dots" />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(n) => {
            const s = n.data?.status;
            if (s === 'completed') return '#22c55e';
            if (s === 'running') return '#f59e0b';
            if (s === 'error') return '#ef4444';
            return '#334155';
          }}
          maskColor="rgba(0,0,0,0.5)"
        />
      </ReactFlow>
      {tooltip && <NodeTooltip data={tooltip} position={tooltipPos} />}
    </div>
  );
}
