import { motion } from 'framer-motion'
import { BrainCircuit, ShieldCheck, Workflow } from 'lucide-react'

const capabilities = [
  { icon: ShieldCheck, title: 'Detect', number: '01', text: 'Ingest and normalize Wazuh, FortiGate, Windows, Linux, and application security events.' },
  { icon: BrainCircuit, title: 'Understand', number: '02', text: 'Enrich indicators, map MITRE ATT&CK techniques, calculate explainable risk, and provide AI-guided analysis.' },
  { icon: Workflow, title: 'Respond', number: '03', text: 'Execute evidence-led playbooks with approval gates for high-impact containment actions.' },
]

const stack = ['React + TypeScript', 'FastAPI', 'PostgreSQL', 'Redis', 'Ollama', 'Wazuh', 'Docker Compose', 'Nginx Gateway']

export function ProjectNarrative() {
  return <section className="relative border-y border-white/[.08] bg-[#0e1010] px-7 py-24 md:px-16 md:py-32">
    <div className="mx-auto max-w-7xl">
      <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: .65 }} className="grid gap-12 lg:grid-cols-[1.1fr_.9fr]">
        <div><p className="eyebrow">The project</p><h2 className="mt-5 max-w-3xl text-4xl font-medium leading-[1.02] tracking-[-.05em] md:text-6xl">A complete security operations platform, designed from the analyst’s point of view.</h2></div>
        <div className="border-l border-[#d8b17a]/50 pl-6 text-base leading-relaxed text-stone-400"><p>Golden Dome is more than a dashboard. It connects telemetry, detection engineering, threat intelligence, local AI analysis, incident management, evidence, and approval-gated automation into one cohesive security workflow.</p><p className="mt-5 text-sm text-stone-500">Built as a cybersecurity engineering project by Salah Anez.</p></div>
      </motion.div>
      <div className="mt-20 grid border-y border-white/[.08] md:grid-cols-3">{capabilities.map(({ icon: Icon, number, title, text }, index) => <motion.article key={title} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: index * .12 }} className="group min-h-[250px] border-b border-white/[.08] p-7 last:border-b-0 md:border-b-0 md:border-r md:last:border-r-0"><div className="flex items-start justify-between"><span className="font-mono text-xs text-[#c97848]">{number}</span><Icon size={19} strokeWidth={1.35} className="text-stone-500 transition group-hover:text-[#d8b17a]" /></div><h3 className="mt-16 text-xl font-medium text-stone-100">{title}</h3><p className="mt-3 max-w-xs text-sm leading-relaxed text-stone-500">{text}</p></motion.article>)}</div>
      <div className="mt-20 grid gap-12 lg:grid-cols-[.8fr_1.2fr]"><div><p className="eyebrow">Engineering foundation</p><p className="mt-5 text-2xl font-medium leading-tight tracking-[-.035em]">Production-minded architecture with security controls built into the delivery model.</p><div className="mt-8 grid grid-cols-2 gap-x-8 gap-y-5 text-sm"><Stat value="JWT + RBAC" label="Access control" /><Stat value="MITRE" label="Detection context" /><Stat value="Approval gates" label="Human control" /><Stat value="Health checks" label="Operational readiness" /></div></div><div className="self-end"><p className="text-[10px] font-semibold uppercase tracking-[.16em] text-stone-500">Technology system</p><div className="mt-5 flex flex-wrap gap-2">{stack.map((item) => <span key={item} className="border border-white/[.1] px-3 py-2 text-xs text-stone-300 transition hover:border-[#d8b17a]/50 hover:text-[#e8d2af]">{item}</span>)}</div><div className="mt-10 flex items-center gap-4 border-t border-white/[.08] pt-6"><div className="grid h-12 w-12 place-items-center rounded-full border border-[#d8b17a]/40 text-sm font-medium text-[#e8d2af]">SA</div><div><p className="text-sm font-medium text-stone-100">Salah Anez</p><p className="mt-1 text-xs text-stone-500">Cybersecurity Engineering Student · Platform builder</p></div></div></div></div>
    </div>
  </section>
}
function Stat({ value, label }: { value: string; label: string }) { return <div><p className="text-sm font-medium text-[#d8b17a]">{value}</p><p className="mt-1 text-xs text-stone-500">{label}</p></div> }
