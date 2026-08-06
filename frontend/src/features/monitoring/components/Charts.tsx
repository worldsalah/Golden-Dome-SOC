import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import ReactECharts from 'echarts-for-react'
import { ChartCard } from '@/components/ChartCard'
import { getMetricsHistory } from '@/services/api'

type RangeKey = '1h' | '24h' | '7d'

const RANGES: { key: RangeKey; label: string }[] = [
  { key: '1h', label: '1H' },
  { key: '24h', label: '24H' },
  { key: '7d', label: '7D' },
]

function RangeSelector({ value, onChange }: { value: RangeKey; onChange: (v: RangeKey) => void }) {
  return (
    <div className="flex items-center gap-1 rounded-md border border-white/[0.08] bg-[#131417] p-0.5">
      {RANGES.map((r) => (
        <button
          key={r.key}
          onClick={() => onChange(r.key)}
          className={`rounded px-2.5 py-1 text-[11px] font-medium transition ${
            value === r.key ? 'bg-[#c97848] text-white' : 'text-stone-500 hover:text-stone-300'
          }`}
        >
          {r.label}
        </button>
      ))}
    </div>
  )
}

function HistoryChart({
  metric,
  title,
  color,
  suffix,
}: {
  metric: 'cpu' | 'memory' | 'network'
  title: string
  color: string
  suffix: string
}) {
  const [range, setRange] = useState<RangeKey>('1h')

  const { data } = useQuery({
    queryKey: ['monitoring-history', metric, range],
    queryFn: () => getMetricsHistory(metric, range),
    refetchInterval: 15_000,
  })

  const option = useMemo(
    () => ({
      backgroundColor: 'transparent',
      grid: { top: 15, right: 15, bottom: 30, left: 45 },
      xAxis: {
        type: 'category',
        data: (data?.points || []).map((p) =>
          new Date(p.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        ),
        axisLine: { lineStyle: { color: '#4b5563' } },
        axisLabel: { color: '#9ca3af', fontSize: 10 },
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: '#374151' } },
        axisLabel: { color: '#9ca3af', fontSize: 10, formatter: `{value}${suffix}` },
      },
      tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v.toFixed(1)}${suffix}` },
      series: [
        {
          type: 'line',
          data: (data?.points || []).map((p) => Number(p.value.toFixed(1))),
          smooth: true,
          symbol: 'none',
          lineStyle: { color, width: 2 },
          areaStyle: { color, opacity: 0.12 },
        },
      ],
    }),
    [data, color, suffix]
  )

  return (
    <ChartCard title={title} right={<RangeSelector value={range} onChange={setRange} />}>
      {data && !data.available ? (
        <div className="flex h-[220px] items-center justify-center text-sm text-stone-600">
          Prometheus not connected — historical charts unavailable.
        </div>
      ) : (
        <ReactECharts option={option} style={{ height: '220px' }} notMerge />
      )}
    </ChartCard>
  )
}

export function MonitoringCharts() {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <HistoryChart metric="cpu" title="CPU History" color="#c97848" suffix="%" />
      <HistoryChart metric="memory" title="Memory History" color="#8d7ab5" suffix="%" />
      <div className="lg:col-span-2">
        <HistoryChart metric="network" title="Network Traffic" color="#10b981" suffix=" Mb/s" />
      </div>
    </div>
  )
}
