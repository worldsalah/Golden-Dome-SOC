import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  addEdge,
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
  type NodeProps,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Trash2 } from 'lucide-react'

import type { PlaybookNode } from '@/types'

const NODE_WIDTH = 180

const typeColors: Record<string, string> = {
  trigger: '#10b981',
  end: '#6b7280',
  condition: '#f59e0b',
  approval: '#ef4444',
  ai_decision: '#8b5cf6',
  action: '#06b6d4',
}

interface CustomData extends Record<string, unknown> {
  label: string
  type: string
}

function CustomNode({ data, selected }: NodeProps) {
  const d = data as unknown as CustomData
  const color = typeColors[d.type] || typeColors.action
  return (
    <div
      className={`rounded-md border px-3 py-2 text-center text-xs font-medium text-white shadow ${selected ? 'ring-2 ring-white' : ''}`}
      style={{ width: NODE_WIDTH, backgroundColor: '#1f2937', borderColor: color }}
    >
      <Handle type="target" position={Position.Top} className="!h-2 !w-2" style={{ background: color }} />
      <div className="mb-1 text-[10px] uppercase tracking-wider text-gray-400">{d.type}</div>
      <div className="truncate">{d.label}</div>
      <Handle type="source" position={Position.Bottom} className="!h-2 !w-2" style={{ background: color }} />
    </div>
  )
}

const nodeTypes = { custom: CustomNode }

function layoutNodes(nodes: PlaybookNode[]): Node[] {
  const layers: Record<string, number> = {}
  for (const n of nodes) {
    layers[n.id] = 0
  }
  let changed = true
  while (changed) {
    changed = false
    for (const n of nodes) {
      for (const next of n.next_nodes || []) {
        if ((layers[next] || 0) <= layers[n.id]) {
          layers[next] = layers[n.id] + 1
          changed = true
        }
      }
    }
  }
  const byLayer: Record<number, string[]> = {}
  for (const n of nodes) {
    byLayer[layers[n.id]] = byLayer[layers[n.id]] || []
    byLayer[layers[n.id]].push(n.id)
  }
  const positions: Record<string, { x: number; y: number }> = {}
  for (const [layer, ids] of Object.entries(byLayer)) {
    const y = Number(layer) * 120 + 50
    const totalWidth = ids.length * (NODE_WIDTH + 40) - 40
    ids.forEach((id, idx) => {
      const x = idx * (NODE_WIDTH + 40) + Math.max(20, 300 - totalWidth / 2)
      positions[id] = { x, y }
    })
  }
  return nodes.map((n) => ({
    id: n.id,
    type: 'custom',
    position: positions[n.id] || { x: 100, y: 100 },
    data: { label: n.name || n.id, type: n.type } as unknown as CustomData,
  }))
}

function edgesFromNodes(nodes: PlaybookNode[]): Edge[] {
  const edges: Edge[] = []
  for (const n of nodes) {
    for (const next of n.next_nodes || []) {
      edges.push({
        id: `${n.id}->${next}`,
        source: n.id,
        target: next,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: '#6b7280' },
      })
    }
  }
  return edges
}

interface PlaybookBuilderProps {
  nodes: PlaybookNode[]
  onChange: (nodes: PlaybookNode[]) => void
}

export function PlaybookBuilder({ nodes, onChange }: PlaybookBuilderProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null)

  const initialNodes = useMemo(() => layoutNodes(nodes), [nodes])
  const initialEdges = useMemo(() => edgesFromNodes(nodes), [nodes])
  const [flowNodes, setFlowNodes, onNodesChange] = useNodesState(initialNodes)
  const [flowEdges, setFlowEdges, onEdgesChange] = useEdgesState(initialEdges)

  useEffect(() => {
    setFlowNodes(layoutNodes(nodes))
    setFlowEdges(edgesFromNodes(nodes))
  }, [nodes, setFlowEdges, setFlowNodes])

  const playbookNodeMap = useMemo(() => {
    const map = new Map<string, PlaybookNode>()
    nodes.forEach((n) => map.set(n.id, n))
    return map
  }, [nodes])

  const syncNodes = useCallback(
    (nextFlowNodes: Node[], nextFlowEdges: Edge[]) => {
      const next: PlaybookNode[] = nextFlowNodes.map((fn) => {
        const d = fn.data as unknown as CustomData
        const existing = playbookNodeMap.get(fn.id)
        return {
          id: fn.id,
          type: d.type,
          name: d.label,
          config: existing?.config || {},
          next_nodes: nextFlowEdges.filter((e) => e.source === fn.id).map((e) => e.target),
          condition: existing?.condition,
        }
      })
      onChange(next)
    },
    [onChange, playbookNodeMap]
  )

  const onConnect = useCallback(
    (connection: Connection) => {
      const edge = {
        ...connection,
        id: `${connection.source}->${connection.target}`,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: '#6b7280' },
      } as Edge
      const nextEdges = addEdge(edge, flowEdges)
      setFlowEdges(nextEdges)
      syncNodes(flowNodes, nextEdges)
    },
    [flowEdges, flowNodes, setFlowEdges, syncNodes]
  )

  const onNodeClick = (_: unknown, node: Node) => {
    setSelectedNodeId(node.id)
    setSelectedEdgeId(null)
  }

  const onEdgeClick = (_: unknown, edge: Edge) => {
    setSelectedEdgeId(edge.id)
    setSelectedNodeId(null)
  }

  const onPaneClick = () => {
    setSelectedNodeId(null)
    setSelectedEdgeId(null)
  }

  const addNode = (type: string) => {
    const id = `node_${flowNodes.length + 1}`
    const newNode: Node = {
      id,
      type: 'custom',
      position: { x: 250, y: flowNodes.length * 120 + 50 },
      data: { label: type === 'trigger' ? 'Start' : type === 'end' ? 'End' : id, type } as unknown as CustomData,
    }
    const nextNodes = [...flowNodes, newNode]
    const existing = playbookNodeMap.get(id)
    const nextPlaybookNode: PlaybookNode = {
      id,
      type,
      name: newNode.data.label as string,
      config: existing?.config || {},
      next_nodes: [],
      condition: existing?.condition,
    }
    onChange([...nodes, nextPlaybookNode])
    setFlowNodes(nextNodes)
    setSelectedNodeId(id)
  }

  const updateSelected = (patch: Partial<PlaybookNode>) => {
    if (!selectedNodeId) return
    const next = nodes.map((n) => (n.id === selectedNodeId ? { ...n, ...patch } : n))
    onChange(next)
    setFlowNodes((prev) =>
      prev.map((fn) => {
        if (fn.id !== selectedNodeId) return fn
        const d = { ...(fn.data as unknown as CustomData) }
        if (patch.name) d.label = patch.name
        if (patch.type) d.type = patch.type
        return { ...fn, data: d }
      })
    )
  }

  const deleteSelected = () => {
    if (selectedNodeId) {
      const next = nodes.filter((n) => n.id !== selectedNodeId)
      const nextFlowNodes = flowNodes.filter((n) => n.id !== selectedNodeId)
      const nextFlowEdges = flowEdges.filter((e) => e.source !== selectedNodeId && e.target !== selectedNodeId)
      onChange(next)
      setFlowNodes(nextFlowNodes)
      setFlowEdges(nextFlowEdges)
      setSelectedNodeId(null)
    } else if (selectedEdgeId) {
      const nextFlowEdges = flowEdges.filter((e) => e.id !== selectedEdgeId)
      setFlowEdges(nextFlowEdges)
      syncNodes(flowNodes, nextFlowEdges)
      setSelectedEdgeId(null)
    }
  }

  const selectedNode = selectedNodeId ? nodes.find((n) => n.id === selectedNodeId) : undefined

  return (
    <div className="flex h-[500px] gap-3">
      <div className="flex w-56 flex-col gap-2 rounded-md border border-gray-800 bg-gray-950 p-3">
        <h4 className="text-xs font-semibold text-gray-300">Node Palette</h4>
        <div className="flex flex-col gap-2 overflow-auto">
          {['trigger', 'action', 'condition', 'approval', 'ai_decision', 'enrich_ioc', 'collect_evidence', 'create_incident', 'block_ip', 'notify', 'send_email', 'generate_report', 'end'].map((t) => (
            <button key={t} onClick={() => addNode(t)} className="rounded border border-gray-800 bg-gray-900 px-2 py-1.5 text-left text-xs text-cyan-400 hover:bg-gray-800">
              + {t}
            </button>
          ))}
        </div>
      </div>
      <div className="relative flex-1 rounded-md border border-gray-800 bg-gray-950">
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          onPaneClick={onPaneClick}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background color="#374151" gap={16} />
          <Controls />
          <MiniMap className="!bg-gray-900" nodeColor={(n) => typeColors[(n.data as unknown as CustomData).type] || typeColors.action} />
        </ReactFlow>
        {(selectedNode || selectedEdgeId) && (
          <div className="absolute right-3 top-3 w-64 rounded-md border border-gray-700 bg-gray-900 p-3 shadow-lg">
            <div className="mb-2 flex items-center justify-between">
              <h4 className="text-xs font-semibold text-gray-200">{selectedNode ? 'Edit Node' : 'Edge Selected'}</h4>
              <button onClick={deleteSelected} className="text-red-400 hover:text-red-300"><Trash2 className="h-4 w-4" /></button>
            </div>
            {selectedNode && (
              <div className="space-y-2">
                <div>
                  <label className="block text-[10px] text-gray-500">ID</label>
                  <input value={selectedNode.id} disabled className="w-full rounded border border-gray-700 bg-gray-950 px-2 py-1 text-xs text-gray-400" />
                </div>
                <div>
                  <label className="block text-[10px] text-gray-500">Name</label>
                  <input value={selectedNode.name} onChange={(e) => updateSelected({ name: e.target.value })} className="w-full rounded border border-gray-700 bg-gray-950 px-2 py-1 text-xs text-white" />
                </div>
                <div>
                  <label className="block text-[10px] text-gray-500">Type</label>
                  <select value={selectedNode.type} onChange={(e) => updateSelected({ type: e.target.value })} className="w-full rounded border border-gray-700 bg-gray-950 px-1 py-1 text-xs text-white">
                    <option value="trigger">trigger</option>
                    <option value="action">action</option>
                    <option value="condition">condition</option>
                    <option value="approval">approval</option>
                    <option value="ai_decision">ai_decision</option>
                    <option value="enrich_ioc">enrich_ioc</option>
                    <option value="enrich_alert">enrich_alert</option>
                    <option value="collect_evidence">collect_evidence</option>
                    <option value="create_incident">create_incident</option>
                    <option value="update_incident">update_incident</option>
                    <option value="block_ip">block_ip</option>
                    <option value="quarantine_host">quarantine_host</option>
                    <option value="isolate_endpoint">isolate_endpoint</option>
                    <option value="disable_user">disable_user</option>
                    <option value="notify">notify</option>
                    <option value="send_email">send_email</option>
                    <option value="create_ticket">create_ticket</option>
                    <option value="webhook">webhook</option>
                    <option value="generate_report">generate_report</option>
                    <option value="close_incident">close_incident</option>
                    <option value="end">end</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] text-gray-500">Config JSON</label>
                  <textarea
                    value={JSON.stringify(selectedNode.config || {}, null, 2)}
                    onChange={(e) => { try { updateSelected({ config: JSON.parse(e.target.value) }) } catch { /* ignore */ } }}
                    rows={4}
                    className="w-full rounded border border-gray-700 bg-gray-950 px-2 py-1 font-mono text-[10px] text-white"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-gray-500">Condition</label>
                  <input value={selectedNode.condition || ''} onChange={(e) => updateSelected({ condition: e.target.value || undefined })} placeholder="e.g. severity >= 5" className="w-full rounded border border-gray-700 bg-gray-950 px-2 py-1 text-xs text-white" />
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
