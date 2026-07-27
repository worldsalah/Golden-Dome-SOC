import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FileText, Loader2, RefreshCw, Trash2 } from 'lucide-react'
import { motion } from 'framer-motion'
import { PageHeader } from '@/components/PageHeader'
import { ChartCard } from '@/components/ChartCard'
import { formatDate } from '@/utils/formatters'
import { generateIncidentReport, listReports, deleteReport } from '@/services/api'
import type { IncidentReport } from '@/types'

export function ReportsPage() {
  const queryClient = useQueryClient()
  const [incidentId, setIncidentId] = useState('')
  const [generating, setGenerating] = useState(false)
  const [selectedReport, setSelectedReport] = useState<IncidentReport | null>(null)

  const { data: reportsData, isLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: () => listReports(1, 50),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteReport,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reports'] }),
  })

  const generate = async () => {
    const id = parseInt(incidentId, 10)
    if (Number.isNaN(id)) return
    setGenerating(true)
    try {
      const data = await generateIncidentReport(id)
      setSelectedReport(data as IncidentReport)
      queryClient.invalidateQueries({ queryKey: ['reports'] })
    } finally {
      setGenerating(false)
    }
  }

  const downloadMarkdown = (report: IncidentReport) => {
    const blob = new Blob([report.markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `incident-report-${report.generated_at}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const reports = reportsData?.data || []

  return (
    <div className="space-y-6">
      <PageHeader title="Reports" subtitle="Generate, download, and manage security reports" />

      <div className="grid gap-6 lg:grid-cols-3">
        <ChartCard title="Generate Incident Report" className="lg:col-span-1">
          <div className="flex gap-2">
            <input
              type="number"
              value={incidentId}
              onChange={(e) => setIncidentId(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && generate()}
              placeholder="Incident ID..."
              className="flex-1 rounded-md border border-gray-700 bg-gray-900 px-4 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
            />
            <button
              onClick={generate}
              disabled={generating || !incidentId}
              className="flex items-center gap-2 rounded-md bg-cyan-600 px-4 py-2 text-sm text-white hover:bg-cyan-500 disabled:opacity-50"
            >
              {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-500">Enter an incident ID to generate a markdown/PDF report using Sentinel AI.</p>
        </ChartCard>

        <ChartCard title="Report Library" className="lg:col-span-2">
          {isLoading ? (
            <p className="text-sm text-gray-500">Loading reports...</p>
          ) : reports.length === 0 ? (
            <p className="text-sm text-gray-500">No reports generated yet.</p>
          ) : (
            <div className="space-y-3">
              {reports.map((report) => (
                <motion.div
                  key={report.id}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center justify-between rounded-md border border-gray-800 bg-gray-900/50 p-3"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-6 w-6 text-cyan-400" />
                    <div>
                      <p className="text-sm font-medium text-white">{report.title}</p>
                      <p className="text-xs text-gray-500 capitalize">{report.report_type} • {formatDate(report.created_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        const r = { ...report, markdown: report.content || '', generated_at: report.created_at, report: { summary: report.content } } as unknown as IncidentReport
                        downloadMarkdown(r)
                      }}
                      className="rounded-md border border-gray-700 bg-gray-800 px-3 py-1.5 text-xs text-white hover:bg-gray-700"
                    >
                      Download
                    </button>
                    <button onClick={() => deleteMutation.mutate(report.id)} className="rounded-md bg-red-600/10 p-1.5 text-red-400 hover:bg-red-600/20"><Trash2 className="h-4 w-4" /></button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </ChartCard>
      </div>

      {selectedReport && (
        <ChartCard title="Generated Report Preview">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs text-gray-500">Generated at {new Date(selectedReport.generated_at).toLocaleString()}</p>
            <button onClick={() => downloadMarkdown(selectedReport)} className="rounded-md bg-gray-800 px-3 py-1.5 text-xs text-white hover:bg-gray-700">Download Markdown</button>
          </div>
          <pre className="max-h-[500px] overflow-auto rounded-md bg-gray-950 p-4 text-xs text-gray-300 font-mono whitespace-pre-wrap">
            {selectedReport.markdown}
          </pre>
        </ChartCard>
      )}
    </div>
  )
}
