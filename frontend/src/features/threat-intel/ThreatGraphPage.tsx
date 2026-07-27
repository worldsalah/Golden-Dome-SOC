/* eslint-disable @typescript-eslint/no-explicit-any */
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { ChartCard } from '@/components/ChartCard'
import { getThreatGraph } from '@/services/api'
import ReactECharts from 'echarts-for-react'

const groupColors: Record<string, string> = {
  ioc: '#06b6d4',
  campaign: '#8b5cf6',
  malware: '#ec4899',
  actor: '#f97316',
  alert: '#facc15',
  incident: '#ef4444',
}

export function ThreatGraphPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['threat', 'graph'],
    queryFn: () => getThreatGraph(200),
  })

  const option = useMemo(() => {
    if (!data) return {}
    const nodes = (data.nodes || []).map((n: any) => ({
      id: n.id,
      name: n.label,
      symbolSize: n.group === 'ioc' ? 14 + (n.score || 0) / 10 : n.group === 'actor' || n.group === 'campaign' ? 22 : 16,
      value: n.score || 1,
      category: n.group,
      itemStyle: { color: groupColors[n.group] || '#9ca3af' },
      label: { show: n.group !== 'ioc' && n.group !== 'alert', color: '#e5e7eb' },
    }))
    const edges = (data.edges || []).map((e: any) => ({
      source: e.source,
      target: e.target,
      label: { show: false, formatter: e.label },
      lineStyle: { curveness: 0.2, color: '#4b5563' },
    }))

    return {
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          if (params.dataType === 'edge') return `${params.data.source} → ${params.data.target}`
          return `<strong>${params.name}</strong><br/>Type: ${params.data.category}`
        },
      },
      legend: { data: Object.keys(groupColors), textStyle: { color: '#9ca3af' }, bottom: 0 },
      series: [
        {
          type: 'graph',
          layout: 'force',
          data: nodes,
          links: edges,
          categories: Object.keys(groupColors).map((name) => ({ name, itemStyle: { color: groupColors[name] } })),
          roam: true,
          draggable: true,
          label: { position: 'right' },
          force: { repulsion: 300, edgeLength: 90 },
          emphasis: { focus: 'adjacency', lineStyle: { width: 4 } },
        },
      ],
    }
  }, [data])

  return (
    <div className="space-y-6">
      <ChartCard title="Threat Relationship Graph">
        <p className="mb-4 text-sm text-gray-400">
          Interactive graph showing IOCs, campaigns, malware, threat actors, alerts, and incidents.
        </p>
        {isLoading ? (
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-gray-400" />
        ) : (
          <ReactECharts option={option} style={{ height: 600 }} />
        )}
      </ChartCard>
    </div>
  )
}
