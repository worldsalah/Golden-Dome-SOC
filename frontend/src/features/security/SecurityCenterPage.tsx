import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { KeyRound, Lock, Shield, ShieldCheck, Trash2, Plus, AlertTriangle, CheckCircle2, Copy } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { ChartCard } from '@/components/ChartCard'
import { enrollMFA, verifyMFA, disableMFA, getSecurityHeaders, createApiKey, listApiKeys, revokeApiKey, getSecurityAuditSummary } from '@/services/api'

export function SecurityCenterPage() {
  const [tab, setTab] = useState('mfa')

  return (
    <div className="space-y-6">
      <PageHeader title="Security Center" subtitle="MFA, API keys, security headers, and audit summary" />

      <div className="flex gap-2 border-b border-white/[0.07]">
        {[
          { id: 'mfa', label: 'MFA', icon: Lock },
          { id: 'apikeys', label: 'API Keys', icon: KeyRound },
          { id: 'headers', label: 'Headers', icon: Shield },
          { id: 'audit', label: 'Audit', icon: ShieldCheck },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
              tab === t.id ? 'border-[#c97848] text-[#d8b17a]' : 'border-transparent text-stone-400 hover:text-stone-200'
            }`}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'mfa' && <MFATab />}
      {tab === 'apikeys' && <ApiKeysTab />}
      {tab === 'headers' && <HeadersTab />}
      {tab === 'audit' && <AuditTab />}
    </div>
  )
}

function MFATab() {
  const [secret, setSecret] = useState<string | null>(null)
  const [qrUri, setQrUri] = useState<string | null>(null)
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [code, setCode] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const enrollMut = useMutation({
    mutationFn: enrollMFA,
    onSuccess: (data) => {
      setSecret(data.secret)
      setQrUri(data.qr_uri)
      setBackupCodes(data.backup_codes)
      setMessage(null)
      setError(null)
    },
    onError: (e: Error) => setError(e.message),
  })

  const verifyMut = useMutation({
    mutationFn: () => verifyMFA(code),
    onSuccess: (data) => {
      setMessage(data.message)
      setSecret(null)
      setQrUri(null)
      setBackupCodes([])
      setCode('')
    },
    onError: (e: Error) => setError(e.message),
  })

  const disableMut = useMutation({
    mutationFn: () => disableMFA(code),
    onSuccess: (data) => {
      setMessage(data.message)
      setCode('')
    },
    onError: (e: Error) => setError(e.message),
  })

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <ChartCard title="MFA Enrollment">
        <div className="space-y-4">
          {!secret && (
            <button
              onClick={() => enrollMut.mutate()}
              disabled={enrollMut.isPending}
              className="flex items-center gap-2 rounded-md bg-[#c97848] px-4 py-2 text-sm font-medium text-white hover:bg-[#b66838] disabled:opacity-50"
            >
              <Plus className="h-4 w-4" />
              {enrollMut.isPending ? 'Generating…' : 'Generate TOTP Secret'}
            </button>
          )}

          {secret && (
            <>
              <div className="rounded-md border border-[#b98947]/30 bg-[#17181b] p-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-stone-500">TOTP Secret</p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 break-all font-mono text-sm text-[#d8b17a]">{secret}</code>
                  <button
                    onClick={() => navigator.clipboard.writeText(secret)}
                    className="rounded p-1 text-stone-500 hover:text-stone-300"
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              {qrUri && (
                <div className="rounded-md border border-white/[0.08] bg-[#17181b] p-4">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-stone-500">QR URI (scan with authenticator app)</p>
                  <code className="break-all text-xs text-stone-400">{qrUri}</code>
                </div>
              )}

              <div className="rounded-md border border-white/[0.08] bg-[#17181b] p-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-stone-500">Backup Codes</p>
                <div className="grid grid-cols-2 gap-1.5">
                  {backupCodes.map((c, i) => (
                    <code key={i} className="font-mono text-xs text-stone-400">{c}</code>
                  ))}
                </div>
              </div>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="Enter 6-digit code"
                  maxLength={6}
                  className="flex-1 rounded-md border border-white/[0.1] bg-[#131417] px-3 py-2 text-sm text-stone-200 placeholder-stone-600 outline-none focus:border-[#b98947]/50"
                />
                <button
                  onClick={() => verifyMut.mutate()}
                  disabled={verifyMut.isPending || code.length < 6}
                  className="rounded-md bg-emerald-600/80 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600 disabled:opacity-50"
                >
                  Verify
                </button>
              </div>
            </>
          )}

          <div className="flex gap-2">
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Enter code to disable MFA"
              maxLength={6}
              className="flex-1 rounded-md border border-white/[0.1] bg-[#131417] px-3 py-2 text-sm text-stone-200 placeholder-stone-600 outline-none focus:border-[#b98947]/50"
            />
            <button
              onClick={() => disableMut.mutate()}
              disabled={disableMut.isPending || code.length < 6}
              className="rounded-md bg-red-600/80 px-4 py-2 text-sm font-medium text-white hover:bg-red-600 disabled:opacity-50"
            >
              Disable
            </button>
          </div>

          {message && (
            <div className="flex items-center gap-2 rounded-md bg-emerald-500/10 px-3 py-2 text-sm text-emerald-400">
              <CheckCircle2 className="h-4 w-4" /> {message}
            </div>
          )}
          {error && (
            <div className="flex items-center gap-2 rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-400">
              <AlertTriangle className="h-4 w-4" /> {error}
            </div>
          )}
        </div>
      </ChartCard>

      <ChartCard title="MFA Information">
        <div className="space-y-3 text-sm text-stone-400">
          <p>Multi-factor authentication adds an extra layer of security using TOTP (Time-based One-Time Password).</p>
          <div className="rounded-md bg-[#17181b]/50 p-3">
            <p className="mb-1 font-medium text-stone-300">How it works:</p>
            <ol className="list-inside list-decimal space-y-1 text-xs text-stone-500">
              <li>Click "Generate TOTP Secret" to create a new secret</li>
              <li>Scan the QR URI with your authenticator app (Google Authenticator, Authy, etc.)</li>
              <li>Enter the 6-digit code from your app to verify and enable MFA</li>
              <li>Save your backup codes in a secure location</li>
            </ol>
          </div>
          <div className="rounded-md bg-amber-500/5 border border-amber-500/20 p-3">
            <p className="text-xs text-amber-400/80">
              <AlertTriangle className="mr-1 inline h-3.5 w-3.5" />
              Backup codes are shown only once. Store them securely.
            </p>
          </div>
        </div>
      </ChartCard>
    </div>
  )
}

function ApiKeysTab() {
  const qc = useQueryClient()
  const [name, setName] = useState('')
  const [scopes, setScopes] = useState('')
  const [newKey, setNewKey] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const { data: keys } = useQuery({ queryKey: ['api-keys'], queryFn: listApiKeys })

  const createMut = useMutation({
    mutationFn: () => createApiKey({ name, scopes: scopes.split(',').map((s) => s.trim()).filter(Boolean) }),
    onSuccess: (data) => {
      setNewKey(data.key)
      setName('')
      setScopes('')
      setError(null)
      qc.invalidateQueries({ queryKey: ['api-keys'] })
    },
    onError: (e: Error) => setError(e.message),
  })

  const revokeMut = useMutation({
    mutationFn: (prefix: string) => revokeApiKey(prefix),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['api-keys'] }),
  })

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <ChartCard title="Create API Key">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-stone-300">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. SIEM Integration"
              className="mt-1 w-full rounded-md border border-white/[0.1] bg-[#131417] px-3 py-2 text-sm text-stone-200 placeholder-stone-600 outline-none focus:border-[#b98947]/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-stone-300">Scopes (comma-separated)</label>
            <input
              type="text"
              value={scopes}
              onChange={(e) => setScopes(e.target.value)}
              placeholder="read:alerts, read:assets"
              className="mt-1 w-full rounded-md border border-white/[0.1] bg-[#131417] px-3 py-2 text-sm text-stone-200 placeholder-stone-600 outline-none focus:border-[#b98947]/50"
            />
          </div>
          <button
            onClick={() => createMut.mutate()}
            disabled={createMut.isPending || name.length < 3}
            className="flex items-center gap-2 rounded-md bg-[#c97848] px-4 py-2 text-sm font-medium text-white hover:bg-[#b66838] disabled:opacity-50"
          >
            <Plus className="h-4 w-4" />
            {createMut.isPending ? 'Creating…' : 'Create Key'}
          </button>

          {newKey && (
            <div className="rounded-md border border-amber-500/30 bg-amber-500/5 p-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-amber-400">
                <AlertTriangle className="mr-1 inline h-3.5 w-3.5" />
                Save this key — it won't be shown again
              </p>
              <div className="flex items-center gap-2">
                <code className="flex-1 break-all font-mono text-sm text-amber-300">{newKey}</code>
                <button onClick={() => navigator.clipboard.writeText(newKey)} className="rounded p-1 text-stone-500 hover:text-stone-300">
                  <Copy className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-400">
              <AlertTriangle className="h-4 w-4" /> {error}
            </div>
          )}
        </div>
      </ChartCard>

      <ChartCard title="Active Keys">
        <div className="space-y-2">
          {keys && keys.length === 0 && (
            <p className="py-4 text-center text-sm text-stone-600">No API keys created yet</p>
          )}
          {keys?.map((k) => (
            <div
              key={k.id}
              className="flex items-center justify-between rounded-md border border-white/[0.06] bg-[#17181b]/50 p-3"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <code className="font-mono text-sm text-stone-300">{k.key_prefix}…</code>
                  {k.is_active ? (
                    <span className="rounded-full bg-emerald-400/10 px-2 py-0.5 text-[10px] font-medium text-emerald-400">Active</span>
                  ) : (
                    <span className="rounded-full bg-red-400/10 px-2 py-0.5 text-[10px] font-medium text-red-400">Revoked</span>
                  )}
                </div>
                <p className="mt-0.5 truncate text-xs text-stone-500">{k.name}</p>
                {k.scopes.length > 0 && (
                  <p className="mt-0.5 text-[10px] text-stone-600">{k.scopes.join(', ')}</p>
                )}
              </div>
              {k.is_active && (
                <button
                  onClick={() => revokeMut.mutate(k.key_prefix)}
                  className="rounded p-1.5 text-stone-600 hover:bg-red-500/10 hover:text-red-400"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      </ChartCard>
    </div>
  )
}

function HeadersTab() {
  const { data } = useQuery({ queryKey: ['security-headers'], queryFn: getSecurityHeaders })

  if (!data) return <p className="text-sm text-stone-600">Loading…</p>

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <ChartCard title="Security Headers">
        <div className="space-y-2">
          {Object.entries(data.headers).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between rounded-md bg-[#17181b]/50 px-3 py-2">
              <code className="text-xs text-stone-400">{key}</code>
              <code className="text-xs text-[#d8b17a]">{value}</code>
            </div>
          ))}
        </div>
      </ChartCard>

      <ChartCard title="Rate Limiting & CORS">
        <div className="space-y-3">
          <div>
            <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-stone-500">Rate Limiting</p>
            {Object.entries(data.rate_limiting).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between rounded-md bg-[#17181b]/50 px-3 py-2">
                <code className="text-xs text-stone-400">{key}</code>
                <code className="text-xs text-stone-300">{value}</code>
              </div>
            ))}
          </div>
          <div>
            <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-stone-500">CORS</p>
            <div className="rounded-md bg-[#17181b]/50 px-3 py-2">
              <code className="text-xs text-stone-400">credentials: {String(data.cors.allow_credentials)}</code>
            </div>
          </div>
        </div>
      </ChartCard>
    </div>
  )
}

function AuditTab() {
  const { data } = useQuery({ queryKey: ['security-audit-summary'], queryFn: getSecurityAuditSummary })

  if (!data) return <p className="text-sm text-stone-600">Loading…</p>

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <ChartCard title="Failed Logins">
        <div className="text-center">
          <p className="text-4xl font-bold text-red-400">{data.failed_logins}</p>
          <p className="mt-1 text-xs text-stone-600">Total failed attempts</p>
        </div>
      </ChartCard>
      <ChartCard title="Active API Keys">
        <div className="text-center">
          <p className="text-4xl font-bold text-[#d8b17a]">{data.active_api_keys}</p>
          <p className="mt-1 text-xs text-stone-600">Currently active</p>
        </div>
      </ChartCard>
      <ChartCard title="Event Breakdown">
        <div className="space-y-1.5">
          {Object.entries(data.event_counts).map(([action, count]) => (
            <div key={action} className="flex items-center justify-between text-xs">
              <code className="text-stone-400">{action}</code>
              <span className="font-mono text-stone-300">{count}</span>
            </div>
          ))}
          {Object.keys(data.event_counts).length === 0 && (
            <p className="py-2 text-center text-xs text-stone-600">No events recorded</p>
          )}
        </div>
      </ChartCard>
    </div>
  )
}
