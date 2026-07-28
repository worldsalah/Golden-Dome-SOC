interface PageHeaderProps {
  title: string
  subtitle?: string
}

export function PageHeader({ title, subtitle }: PageHeaderProps) {
  return (
    <div className="mb-6 border-b border-white/[0.07] pb-4">
      <h1 className="text-2xl font-medium tracking-[-.03em] text-stone-100">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-stone-500">{subtitle}</p>}
    </div>
  )
}
