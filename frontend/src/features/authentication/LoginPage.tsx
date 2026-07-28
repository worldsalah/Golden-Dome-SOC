import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { AlertCircle, ArrowLeft, Lock } from 'lucide-react'
import { login as loginApi } from '@/services/api'
import { useAuthStore } from '@/store/authStore'
import apiClient from '@/services/api'
import { ThreatGlobe } from '@/components/ThreatGlobe'

const loginSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  password: z.string().min(5, 'Password must be at least 5 characters'),
})

type LoginForm = z.infer<typeof loginSchema>

export function LoginPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) })

  const onSubmit = async (data: LoginForm) => {
    try {
      setError(null)
      const tokenData = await loginApi(data.username, data.password)
      const { data: user } = await apiClient.get('/users/me', {
        headers: { Authorization: `Bearer ${tokenData.access_token}` },
      })
      setAuth(user, tokenData.access_token)
      navigate('/dashboard')
    } catch {
      setError('Invalid username or password. Please try again.')
    }
  }

  return (
    <div className="grid min-h-screen bg-[#090a0b] text-stone-200 lg:grid-cols-[1.15fr_1fr]">
      {/* Brand panel */}
      <div className="relative hidden overflow-hidden border-r border-white/[0.07] lg:block">
        <div className="absolute inset-0 opacity-80">
          <ThreatGlobe />
        </div>
        <div className="relative z-10 flex h-full flex-col justify-between p-10">
          <Link to="/" className="flex items-center gap-2 text-xs text-stone-500 transition hover:text-stone-300">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to overview
          </Link>
          <div>
            <p className="eyebrow">Security Operations Center</p>
            <h1 className="mt-4 max-w-md text-4xl font-medium leading-[1.02] tracking-[-.045em] text-stone-100">
              Global visibility.
              <br />
              <span className="text-stone-500">Analyst control.</span>
            </h1>
            <div className="mt-8 flex gap-10 border-t border-white/[0.08] pt-6 text-sm">
              <span>
                <b className="block text-xl text-[#c97848]">Detection</b>
                <span className="text-xs text-stone-500">MITRE-aligned coverage</span>
              </span>
              <span>
                <b className="block text-xl text-[#d8b17a]">AI analysis</b>
                <span className="text-xs text-stone-500">Local Sentinel engine</span>
              </span>
              <span>
                <b className="block text-xl text-emerald-400">Response</b>
                <span className="text-xs text-stone-500">Approval-gated SOAR</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center px-6 py-12">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-sm"
        >
          <div className="mb-10">
            <span className="text-[13px] font-bold tracking-tight text-stone-100">GOLDEN DOME</span>
            <span className="ml-2 text-[9px] font-semibold uppercase tracking-[.18em] text-[#b98947]">SOC</span>
            <h2 className="mt-6 text-2xl font-medium tracking-[-.03em] text-stone-100">Sign in to the workspace</h2>
            <p className="mt-2 text-sm text-stone-500">Authenticate with your analyst credentials.</p>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              role="alert"
              className="mb-5 flex items-center gap-2 rounded border border-[#b94747]/30 bg-[#b94747]/10 px-3.5 py-2.5 text-xs text-[#e08585]"
            >
              <AlertCircle className="h-3.5 w-3.5 shrink-0" />
              {error}
            </motion.div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label htmlFor="username" className="eyebrow mb-2 block">Username</label>
              <input id="username" {...register('username')} type="text" className="field" placeholder="analyst.name" autoComplete="username" />
              {errors.username && <p className="mt-1.5 text-xs text-[#e08585]">{errors.username.message}</p>}
            </div>

            <div>
              <label htmlFor="password" className="eyebrow mb-2 block">Password</label>
              <input id="password" {...register('password')} type="password" className="field" placeholder="••••••••••" autoComplete="current-password" />
              {errors.password && <p className="mt-1.5 text-xs text-[#e08585]">{errors.password.message}</p>}
            </div>

            <button type="submit" disabled={isSubmitting} className="btn-primary w-full justify-center py-3">
              <Lock className="h-3.5 w-3.5" />
              {isSubmitting ? 'Authenticating…' : 'Enter workspace'}
            </button>
          </form>

          <p className="mt-8 border-t border-white/[0.07] pt-5 text-center text-[11px] leading-relaxed text-stone-600">
            Access is restricted to authorized SOC personnel.
            <br />
            Contact your administrator if you cannot sign in.
          </p>
        </motion.div>
      </div>
    </div>
  )
}
