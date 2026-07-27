import { ReactNode } from 'react'

export type DataWorkspaceColumn<Row extends object> = {
  field: keyof Row | string
  headerName: string
  flex?: number
  sortable?: boolean
  renderCell?: (params: { value: unknown; row: Row }) => ReactNode
}

export function DataWorkspace<Row extends object>({ rows, columns }: { rows: Row[]; columns: DataWorkspaceColumn<Row>[] }) {
  return (
    <div className="overflow-auto">
      <table className="w-full min-w-[760px] border-collapse text-left text-[13px]">
        <thead className="sticky top-0 z-10 bg-[#1d2023] text-[10px] uppercase tracking-[.12em] text-slate-500"><tr>{columns.map((column) => <th key={String(column.field)} className="border-b border-white/[0.07] px-3 py-3 font-semibold">{column.headerName}</th>)}</tr></thead>
        <tbody>{rows.map((row, rowIndex) => <tr key={String((row as Record<string, unknown>).id ?? rowIndex)} className="group border-b border-white/[0.045] transition-colors hover:bg-white/[0.025]">{columns.map((column) => { const value = row[column.field as keyof Row]; return <td key={String(column.field)} className="px-3 py-3 text-slate-300">{column.renderCell ? column.renderCell({ value, row }) : String(value ?? '—')}</td> })}</tr>)}</tbody>
      </table>
    </div>
  )
}
