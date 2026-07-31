import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { animate, motion, useInView, useReducedMotion, useScroll, useSpring, useTransform, type MotionValue } from 'framer-motion'
import {
  Activity,
  AlertTriangle,
  ArrowDown,
  ArrowUpRight,
  Atom,
  BookOpen,
  Brain,
  Braces,
  ChevronRight,
  Container,
  Cpu,
  Database,
  Eye,
  FileText,
  Gauge,
  Github,
  Globe,
  Layers,
  Layout,
  Linkedin,
  Lock,
  Mail,
  Menu,
  Network,
  Scan,
  Search,
  Server,
  Shield,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Workflow,
  X,
  Zap,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { OnboardingWizardPage } from '@/features/onboarding/OnboardingWizardPage'
import { ThreatGlobe } from '@/components/ThreatGlobe'

const sectionPadding = 'px-6 md:px-12 lg:px-20'

function Counter({ value, suffix = '', label }: { value: number; suffix?: string; label: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })
  const [display, setDisplay] = useState(0)
  const shouldReduce = useReducedMotion()

  useEffect(() => {
    if (!inView) return
    if (shouldReduce) {
      setDisplay(value)
      return
    }
    const controls = animate(0, value, {
      duration: 1.6,
      onUpdate: (v) => setDisplay(Math.round(v)),
    })
    return () => controls.stop()
  }, [inView, value, shouldReduce])

  return (
    <div ref={ref} className="text-center">
      <span className="block text-4xl font-semibold tracking-tight text-[#f2eee8] md:text-5xl">
        {display}{suffix}
      </span>
      <span className="mt-2 block text-xs uppercase tracking-widest text-stone-500">{label}</span>
    </div>
  )
}

function ScrollLink({ to, children }: { to: string; children: React.ReactNode }) {
  const handle = () => {
    const el = document.getElementById(to)
    el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  return (
    <button onClick={handle} className="text-sm text-stone-400 transition hover:text-[#f2eee8]">
      {children}
    </button>
  )
}

const features = [
  { icon: Eye, title: 'Real-Time Monitoring', desc: 'Continuous ingest of Wazuh alerts, assets, and telemetry in a single stream.' },
  { icon: Brain, title: 'AI SOC Analyst', desc: 'Local Ollama-powered alert analysis, incident investigation, and playbook generation.' },
  { icon: Shield, title: 'Threat Intelligence', desc: 'IOC tracking, campaign correlation, and external connector enrichment.' },
  { icon: Network, title: 'MITRE ATT&CK Mapping', desc: 'Technique coverage and gap analysis mapped to the enterprise matrix.' },
  { icon: AlertTriangle, title: 'Incident Management', desc: 'Correlated incidents with timeline, notes, AI reports, and case status.' },
  { icon: Scan, title: 'Asset Discovery', desc: 'Network scanning, OS detection, service discovery, and topology mapping.' },
  { icon: Gauge, title: 'Risk Scoring', desc: 'Asset, vulnerability, and detection coverage risk in one posture view.' },
  { icon: Workflow, title: 'SOAR Automation', desc: 'Approval-gated workflows, node-based playbooks, and response actions.' },
  { icon: ShieldCheck, title: 'Compliance', desc: 'PCI-DSS, GDPR, and hotel-industry control templates with scoring.' },
  { icon: FileText, title: 'Reporting', desc: 'One-click incident, validation, and posture reports with Markdown export.' },
]

const tech = [
  { name: 'React', icon: Atom, color: '#61DAFB' },
  { name: 'FastAPI', icon: Zap, color: '#009485' },
  { name: 'PostgreSQL', icon: Database, color: '#336791' },
  { name: 'Redis', icon: Layers, color: '#DC382D' },
  { name: 'Docker', icon: Container, color: '#2496ED' },
  { name: 'Wazuh', icon: Shield, color: '#2563EB' },
  { name: 'OpenSearch', icon: Search, color: '#005EB8' },
  { name: 'Ollama', icon: Brain, color: '#F0A500' },
  { name: 'TypeScript', icon: Braces, color: '#3178C6' },
  { name: 'Material UI', icon: Layout, color: '#007FFF' },
]

const architecture = [
  { label: 'Internet', icon: Globe },
  { label: 'Firewall', icon: Lock },
  { label: 'Wazuh', icon: Shield },
  { label: 'Golden Dome', icon: Cpu },
  { label: 'AI', icon: Brain },
  { label: 'Dashboard', icon: Layout },
]

const why = [
  { icon: Eye, title: 'Enterprise visibility', desc: 'All telemetry, incidents, and assets in one operational pane.' },
  { icon: Sparkles, title: 'AI-assisted investigations', desc: 'Local models accelerate alert triage and incident reconstruction.' },
  { icon: Activity, title: 'Security operations', desc: 'Detection, validation, response, and reporting in one workflow.' },
  { icon: TrendingUp, title: 'Risk reduction', desc: 'Risk scoring and posture management prioritize what matters most.' },
  { icon: Server, title: 'Scalable architecture', desc: 'Multi-tenant, containerized, and built for production deployment.' },
  { icon: ShieldCheck, title: 'Professional monitoring', desc: 'SOC-grade alerting, SOAR automation, and compliance tracking.' },
]

function FounderCard() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.35 }}
      transition={{ duration: 0.7 }}
      className="relative overflow-hidden rounded-2xl border border-white/[0.06] bg-white/[0.02] p-8 backdrop-blur-md"
    >
      <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-[#c97848]/10 blur-2xl" />
      <div className="flex flex-col gap-6 md:flex-row md:items-center">
        <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl border border-white/[0.08] bg-[#c97848]/10 text-2xl font-bold text-[#e8d2af]">
          SA
        </div>
        <div className="flex-1">
          <p className="text-xs font-semibold uppercase tracking-widest text-stone-500">Founder</p>
          <h3 className="mt-1 text-3xl font-medium tracking-tight text-[#f2eee8]">Salah Anez</h3>
          <p className="mt-1 text-sm text-stone-400">Cybersecurity Engineering Student · AI Security Research</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {['Security Operations', 'Infrastructure Monitoring', 'AI Security'].map((t) => (
              <span key={t} className="rounded-full border border-white/[0.08] bg-white/[0.03] px-3 py-1 text-xs text-stone-300">
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-8 border-t border-white/[0.06] pt-6">
        <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-stone-500">Built with</p>
        <div className="flex flex-wrap gap-2">
          {['React', 'FastAPI', 'Wazuh', 'Docker', 'PostgreSQL', 'Redis', 'Ollama', 'TypeScript'].map((t) => (
            <span key={t} className="rounded-md bg-[#0e0f11] px-2.5 py-1 text-[11px] text-stone-400">
              {t}
            </span>
          ))}
        </div>
      </div>
    </motion.div>
  )
}

function FeatureCard({ feature, index }: { feature: typeof features[0]; index: number }) {
  const Icon = feature.icon
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.5, delay: index * 0.05 }}
      whileHover={{ y: -6, scale: 1.01 }}
      className="group relative overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.02] p-6 transition-shadow hover:shadow-[0_0_40px_-12px_rgba(201,120,72,0.15)]"
    >
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-[#c97848]/10 text-[#d8b17a]">
        <Icon className="h-5 w-5" />
      </div>
      <h4 className="text-base font-medium text-[#f2eee8]">{feature.title}</h4>
      <p className="mt-2 text-sm leading-relaxed text-stone-500">{feature.desc}</p>
    </motion.div>
  )
}

function TechCard({ item, index }: { item: typeof tech[0]; index: number }) {
  const Icon = item.icon
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.4, delay: index * 0.04 }}
      whileHover={{ scale: 1.04 }}
      className="group flex items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 backdrop-blur-sm transition-shadow hover:shadow-[0_0_30px_-10px_rgba(255,255,255,0.08)]"
    >
      <div
        className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/[0.08] bg-[#0e0f11]"
        style={{ color: item.color }}
      >
        <Icon className="h-5 w-5" />
      </div>
      <span className="text-sm font-medium text-stone-200">{item.name}</span>
    </motion.div>
  )
}

function ArchitectureFlow() {
  return (
    <div className="relative mx-auto max-w-3xl">
      <div className="flex flex-col items-center gap-8 md:flex-row md:justify-between md:gap-4">
        {architecture.map((node, i) => {
          const Icon = node.icon
          return (
            <div key={node.label} className="relative flex flex-col items-center">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
                className="relative z-10 flex h-20 w-20 items-center justify-center rounded-2xl border border-white/[0.08] bg-white/[0.03] backdrop-blur-md"
              >
                <Icon className="h-7 w-7 text-[#d8b17a]" />
              </motion.div>
              <p className="mt-3 text-xs font-medium text-stone-400">{node.label}</p>
              {i < architecture.length - 1 && (
                <>
                  <ChevronRight className="absolute -right-9 top-8 hidden h-5 w-5 text-stone-600 md:block" />
                  <motion.div
                    initial={{ y: 0, opacity: 0.8 }}
                    animate={{ y: [0, 24, 0], opacity: [0.8, 1, 0.8] }}
                    transition={{ duration: 1.6, repeat: Infinity, delay: i * 0.2 }}
                    className="absolute -bottom-10 h-2 w-2 rounded-full bg-[#c97848] md:hidden"
                  />
                </>
              )}
            </div>
          )
        })}
      </div>
      <div className="mt-8 text-center text-xs text-stone-600">Telemetry flows from the edge through detection, correlation, AI, and into the analyst dashboard.</div>
    </div>
  )
}

function Navigation({ onLaunch }: { onLaunch: () => void }) {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  return (
    <nav
      className={`fixed left-0 top-0 z-50 w-full transition-all duration-300 ${
        scrolled ? 'border-b border-white/[0.06] bg-[#090a0b]/90 backdrop-blur-md' : 'bg-transparent'
      }`}
    >
      <div className="flex items-center justify-between px-6 py-4 md:px-12">
        <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="text-sm font-semibold tracking-tight text-[#f2eee8]">
          GOLDEN DOME
        </button>
        <div className="hidden items-center gap-8 md:flex">
          <ScrollLink to="platform">Platform</ScrollLink>
          <ScrollLink to="features">Features</ScrollLink>
          <ScrollLink to="architecture">Architecture</ScrollLink>
          <a href="#" className="text-sm text-stone-400 transition hover:text-[#f2eee8]">Documentation</a>
          <a href="https://github.com/worldsalah/Golden-Dome-SOC" target="_blank" rel="noreferrer" className="text-sm text-stone-400 transition hover:text-[#f2eee8]">GitHub</a>
        </div>
        <div className="hidden md:block">
          <button
            onClick={onLaunch}
            className="inline-flex items-center gap-1.5 rounded-full bg-[#f2eee8] px-4 py-2 text-xs font-medium text-[#090a0b] transition hover:bg-white"
          >
            Launch Platform <ArrowUpRight className="h-3.5 w-3.5" />
          </button>
        </div>
        <button className="md:hidden" onClick={() => setOpen(!open)}>
          {open ? <X className="h-5 w-5 text-[#f2eee8]" /> : <Menu className="h-5 w-5 text-[#f2eee8]" />}
        </button>
      </div>
      {open && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          className="border-b border-white/[0.06] bg-[#090a0b]/95 px-6 pb-6 md:hidden"
        >
          <div className="flex flex-col gap-4 pt-4">
            <ScrollLink to="platform">Platform</ScrollLink>
            <ScrollLink to="features">Features</ScrollLink>
            <ScrollLink to="architecture">Architecture</ScrollLink>
            <button onClick={onLaunch} className="text-left text-sm text-[#f2eee8]">Launch Platform</button>
          </div>
        </motion.div>
      )}
    </nav>
  )
}

function BackgroundGlows({ mouseX, mouseY }: { mouseX: MotionValue<number>; mouseY: MotionValue<number> }) {
  const x = useTransform(mouseX, [0, 1], [-30, 30])
  const y = useTransform(mouseY, [0, 1], [-30, 30])
  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      <motion.div style={{ x, y }} className="absolute -left-32 top-1/4 h-96 w-96 rounded-full bg-[#c97848]/5 blur-[100px]" />
      <div className="absolute right-0 top-1/3 h-[28rem] w-[28rem] rounded-full bg-[#7cc9a5]/4 blur-[120px]" />
      <div className="absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-[#314842]/20 blur-[100px]" />
    </div>
  )
}

export function ExperiencePage() {
  const navigate = useNavigate()
  const [exiting, setExiting] = useState(false)
  const shouldReduce = useReducedMotion()

  const { scrollYProgress } = useScroll()
  const heroOpacity = useTransform(scrollYProgress, [0, 0.4], [1, 0])
  const heroY = useTransform(scrollYProgress, [0, 0.4], [0, -60])

  const mouseX = useSpring(0.5, { stiffness: 40, damping: 20 })
  const mouseY = useSpring(0.5, { stiffness: 40, damping: 20 })

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      mouseX.set(e.clientX / window.innerWidth)
      mouseY.set(e.clientY / window.innerHeight)
    }
    window.addEventListener('mousemove', onMove)
    return () => window.removeEventListener('mousemove', onMove)
  }, [mouseX, mouseY])

  const launch = () => {
    setExiting(true)
    setTimeout(() => navigate('/login'), 650)
  }

  const learnMore = () => {
    document.getElementById('platform')?.scrollIntoView({ behavior: 'smooth' })
  }

  const { data: setup } = useQuery({
    queryKey: ['onboarding-status'],
    queryFn: async () => {
      try {
        const r = await fetch('/api/onboarding/status')
        if (!r.ok) return { needs_setup: false }
        return await r.json()
      } catch {
        return { needs_setup: false }
      }
    },
    refetchInterval: 5000,
    staleTime: 0,
  })

  if (setup?.needs_setup) {
    return (
      <main className="relative min-h-screen overflow-x-hidden bg-soc-bg text-stone-100 selection:bg-[#c97848]/40">
        <div className="mx-auto max-w-4xl px-6 py-20">
          <div className="mb-8 text-center">
            <h1 className="text-4xl font-medium tracking-tight">Welcome to Golden Dome</h1>
            <p className="mt-2 text-stone-400">Complete the initial setup to activate the appliance.</p>
          </div>
          <OnboardingWizardPage onComplete={() => navigate('/login')} />
        </div>
      </main>
    )
  }

  return (
    <motion.main
      initial={{ opacity: 0 }}
      animate={exiting ? { opacity: 0, y: -20 } : { opacity: 1, y: 0 }}
      transition={{ duration: shouldReduce ? 0 : 0.6 }}
      className="relative min-h-screen overflow-x-hidden bg-[#090a0b] text-[#f2eee8] selection:bg-[#c97848]/40"
    >
      <BackgroundGlows mouseX={mouseX} mouseY={mouseY} />
      <Navigation onLaunch={launch} />

      {/* Hero */}
      <section className="relative flex h-screen w-full items-center justify-center overflow-hidden">
        <div className="absolute inset-0 z-0">
          <ThreatGlobe attacks={[]} />
        </div>
        <div className="absolute inset-0 z-0 bg-gradient-to-b from-[#090a0b]/60 via-[#090a0b]/20 to-[#090a0b]" />
        <motion.div
          style={{ opacity: shouldReduce ? 1 : heroOpacity, y: shouldReduce ? 0 : heroY }}
          className="relative z-10 w-full max-w-7xl px-6 md:px-12 lg:px-20"
        >
          <div className="max-w-2xl">
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-[#c97848]"
            >
              AI-Powered Security Operations Platform
            </motion.p>
            <motion.h1
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.9, delay: 0.35 }}
              className="text-6xl font-medium leading-[0.95] tracking-[-0.05em] md:text-8xl lg:text-9xl"
            >
              Golden Dome
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.55 }}
              className="mt-6 max-w-lg text-base leading-relaxed text-stone-400 md:text-lg"
            >
              An enterprise platform that centralizes security monitoring, threat detection, AI-assisted investigation, and operational visibility through a unified interface.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.75 }}
              className="mt-8 flex flex-wrap items-center gap-4"
            >
              <button
                onClick={launch}
                className="inline-flex items-center gap-2 rounded-full bg-[#f2eee8] px-6 py-3 text-sm font-medium text-[#090a0b] transition hover:bg-white"
              >
                Launch Platform <ArrowUpRight className="h-4 w-4" />
              </button>
              <button
                onClick={learnMore}
                className="inline-flex items-center gap-2 rounded-full border border-white/[0.12] bg-white/[0.03] px-6 py-3 text-sm font-medium text-stone-200 backdrop-blur-sm transition hover:bg-white/[0.08]"
              >
                Learn More <ArrowDown className="h-4 w-4" />
              </button>
            </motion.div>
          </div>
        </motion.div>
        <div className="absolute bottom-10 left-1/2 z-10 -translate-x-1/2">
          <ArrowDown className="h-5 w-5 animate-bounce text-stone-600" />
        </div>
      </section>

      {/* Founder + Stats */}
      <section id="platform" className={`relative z-10 py-28 ${sectionPadding}`}>
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-12 lg:grid-cols-2">
            <div>
              <motion.p
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="eyebrow text-stone-500"
              >
                Built by a cybersecurity engineering student
              </motion.p>
              <motion.h2
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.7 }}
                className="mt-4 text-4xl font-medium tracking-[-0.03em] text-[#f2eee8] md:text-5xl"
              >
                A founder-led approach to building a modern SOC.
              </motion.h2>
              <div className="mt-10">
                <FounderCard />
              </div>
            </div>
            <div className="flex flex-col justify-center">
              <motion.h3
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="mb-10 text-2xl font-medium tracking-tight text-[#f2eee8]"
              >
                Platform at a glance
              </motion.h3>
              <div className="grid grid-cols-2 gap-8 md:grid-cols-3">
                <Counter value={14} label="Platform Modules" />
                <Counter value={7} label="AI Features" />
                <Counter value={10} label="Integrations" />
                <Counter value={60} suffix="+" label="API Endpoints" />
                <Counter value={6} label="Docker Services" />
                <Counter value={1} label="Live Wazuh Link" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className={`relative z-10 py-24 ${sectionPadding}`}>
        <div className="mx-auto max-w-7xl">
          <div className="mb-16 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">Capabilities</p>
            <h2 className="mt-3 text-4xl font-medium tracking-[-0.03em] text-[#f2eee8] md:text-5xl">Features</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {features.map((f, i) => (
              <FeatureCard key={f.title} feature={f} index={i} />
            ))}
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section id="architecture" className={`relative z-10 py-24 ${sectionPadding}`}>
        <div className="mx-auto max-w-7xl rounded-3xl border border-white/[0.06] bg-white/[0.02] px-8 py-20 backdrop-blur-md">
          <div className="mb-14 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">Data Flow</p>
            <h2 className="mt-3 text-4xl font-medium tracking-[-0.03em] text-[#f2eee8] md:text-5xl">Architecture</h2>
          </div>
          <ArchitectureFlow />
        </div>
      </section>

      {/* Tech Stack */}
      <section className={`relative z-10 py-24 ${sectionPadding}`}>
        <div className="mx-auto max-w-7xl">
          <div className="mb-14 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">Stack</p>
            <h2 className="mt-3 text-4xl font-medium tracking-[-0.03em] text-[#f2eee8] md:text-5xl">Technology</h2>
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-5">
            {tech.map((item, i) => (
              <TechCard key={item.name} item={item} index={i} />
            ))}
          </div>
        </div>
      </section>

      {/* Why Golden Dome */}
      <section className={`relative z-10 py-24 ${sectionPadding}`}>
        <div className="mx-auto max-w-7xl">
          <div className="mb-14 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">Why</p>
            <h2 className="mt-3 text-4xl font-medium tracking-[-0.03em] text-[#f2eee8] md:text-5xl">Why Golden Dome</h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {why.map((w, i) => (
              <motion.div
                key={w.title}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.08 }}
                className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6"
              >
                <w.icon className="h-6 w-6 text-[#c97848]" />
                <h4 className="mt-4 text-lg font-medium text-[#f2eee8]">{w.title}</h4>
                <p className="mt-2 text-sm leading-relaxed text-stone-500">{w.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={`relative z-10 border-t border-white/[0.06] bg-[#0e0f11] py-16 ${sectionPadding}`}>
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col items-start justify-between gap-10 md:flex-row md:items-center">
            <div>
              <h4 className="text-xl font-medium tracking-tight text-[#f2eee8]">Golden Dome</h4>
              <p className="mt-1 text-sm text-stone-500">Version 1.0 · Enterprise AI Security Operations</p>
              <p className="mt-4 text-xs text-stone-600">© {new Date().getFullYear()} Salah Anez. All rights reserved.</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <a href="https://github.com/worldsalah/Golden-Dome-SOC" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-2 text-sm text-stone-300 transition hover:bg-white/[0.08]">
                <Github className="h-4 w-4" /> GitHub
              </a>
              <a href="#" className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-2 text-sm text-stone-300 transition hover:bg-white/[0.08]">
                <BookOpen className="h-4 w-4" /> Documentation
              </a>
              <a href="mailto:contact@goldendome.local" className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-2 text-sm text-stone-300 transition hover:bg-white/[0.08]">
                <Mail className="h-4 w-4" /> Contact
              </a>
              <a href="#" className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-2 text-sm text-stone-300 transition hover:bg-white/[0.08]">
                <Linkedin className="h-4 w-4" /> LinkedIn
              </a>
            </div>
          </div>
        </div>
      </footer>
    </motion.main>
  )
}
