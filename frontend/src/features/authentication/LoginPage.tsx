import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { AlertCircle, Shield, ShieldCheck } from 'lucide-react'
import { login as loginApi } from '@/services/api'
import { useAuthStore } from '@/store/authStore'
import apiClient from '@/services/api'
import { ParticleBackground } from '@/components/ParticleBackground'

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
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

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
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#050914] px-4">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-900/20 via-[#050914] to-[#050914]" />
      <ParticleBackground />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 w-full max-w-md rounded-2xl border border-cyan-500/20 bg-gray-900/80 p-8 shadow-[0_0_40px_rgba(6,182,212,0.12)] backdrop-blur-md"
      >
        <div className="mb-8 flex flex-col items-center">
          <motion.div
            animate={{ boxShadow: ['0 0 0px cyan', '0 0 20px cyan', '0 0 0px cyan'] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-cyan-500/10"
          >
            <Shield className="h-9 w-9 text-cyan-400" />
          </motion.div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Golden Dome SOC</h1>
          <p className="mt-1 text-sm text-cyan-300/80">AI-Driven Security Operations Center</p>
        </div>

        <div className="mb-6 flex items-center justify-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-300">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>Platform secure. Sentinel AI online.</span>
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            role="alert"
            className="mb-4 flex items-center gap-2 rounded-md bg-red-500/10 p-3 text-sm text-red-400"
          >
            <AlertCircle className="h-4 w-4" />
            {error}
          </motion.div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="username" className="mb-1 block text-sm font-medium text-gray-300">Username</label>
            <input
              id="username"
              {...register('username')}
              type="text"
              className="w-full rounded-lg border border-gray-700 bg-gray-950/60 px-4 py-2.5 text-white placeholder-gray-500 outline-none transition-colors focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50"
              placeholder="Enter your username"
            />
            {errors.username && (
              <p className="mt-1 text-xs text-red-400">{errors.username.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-gray-300">Password</label>
            <input
              id="password"
              {...register('password')}
              type="password"
              className="w-full rounded-lg border border-gray-700 bg-gray-950/60 px-4 py-2.5 text-white placeholder-gray-500 outline-none transition-colors focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50"
              placeholder="Enter your password"
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-400">{errors.password.message}</p>
            )}
          </div>

          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-xs text-gray-400">
              <input type="checkbox" className="rounded border-gray-600 bg-gray-800 text-cyan-500 focus:ring-cyan-500" />
              Remember me
            </label>
            <span className="cursor-pointer text-xs text-cyan-400 hover:text-cyan-300">Forgot password?</span>
          </div>

          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-cyan-500/20 transition-all hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50"
          >
            {isSubmitting ? 'Authenticating...' : 'Sign In to SOC'}
          </motion.button>
        </form>

        <p className="mt-6 text-center text-xs text-gray-500">
          Contact your SOC administrator if you cannot access your account.
        </p>
      </motion.div>
    </div>
  )
}
