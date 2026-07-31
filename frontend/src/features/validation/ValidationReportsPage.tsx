import { formatDateTime } from '@/utils/formatters'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, FileText, RefreshCcw, WifiOff } from 'lucide-react'
import { getSocHealthScore, downloadValidationReport } from '@/services/api'

export function ValidationReportsPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['soc-health-score'],
    queryFn: () => getSocHealthScore(),
    retry: false,
  })
  const [downloading, setDownloading] = useState(false)

  const handleDownload = async () => {
    setDownloading(true)
    try {
      await downloadValidationReport()
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Detection Engineering · Sprint 5</p>
          <h1 className="mt-1 text-2xl font-medium tracking-[-.03em] text-stone-100">Validation Reports</h1>
          <p className="mt-1 text-xs text-stone-500">Download a full PDF report built from real detection validation, coverage, and health metrics.</p>
        </div>
        <button onClick={() => refetch()} className="btn-ghost py-2" disabled={isFetching}>
          <RefreshCcw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {isError && (
        <div className="enterprise-panel flex items-start gap-3 border-[#b94747]/30 p-4">
          <WifiOff className="mt-0.5 h-4 w-4 shrink-0 text-[#e08585]" />
          <div>
            <p className="text-sm font-medium text-stone-100">Cannot reach Wazuh Manager / Indexer</p>
            <p className="mt-1 text-xs text-stone-500">{(error as Error)?.message}</p>
          </div>
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-3">
        <div className="enterprise-panel p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#d8b17a]/10">
              <FileText className="h-5 w-5 text-[#d8b17a]" />
            </div>
            <div>
              <p className="eyebrow">Latest grade</p>
              <p className="mt-0.5 font-mono text-2xl text-stone-100">{isLoading ? '—' : data?.grade ?? '—'}</p>
            </div>
          </div>
        </div>
        <div className="enterprise-panel p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#d8b17a]/10">
              <Download className="h-5 w-5 text-[#d8b17a]" />
            </div>
            <div>
              <p className="eyebrow">Overall score</p>
              <p className="mt-0.5 font-mono text-2xl text-stone-100">{isLoading ? '—' : data ? `${data.overall_score.toFixed(1)} / 100` : '—'}</p>
            </div>
          </div>
        </div>
        <div className="enterprise-panel p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#d8b17a]/10">
              <RefreshCcw className="h-5 w-5 text-[#d8b17a]" />
            </div>
            <div>
              <p className="eyebrow">Generated at</p>
              <p className="mt-0.5 text-sm text-stone-300">{data ? formatDateTime(data.generated_at) : '—'}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="enterprise-panel p-6">
        <h2 className="text-lg font-medium text-stone-100">SOC Validation Report</h2>
        <p className="mt-1 text-sm text-stone-500">
          This PDF includes the validation center, ATT&CK coverage, false-positive analysis, detection performance, rule optimization, and the SOC health grade.
        </p>
        <button
          onClick={handleDownload}
          disabled={downloading || isLoading || isError}
          className="btn-primary mt-4 inline-flex items-center gap-2 disabled:opacity-50"
        >
          <Download className="h-4 w-4" />
          {downloading ? 'Generating PDF…' : 'Download PDF Report'}
        </button>
      </div>
    </div>
  )
}
