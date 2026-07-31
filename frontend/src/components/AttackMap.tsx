import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getAttackMap } from '@/services/api'

export function AttackMap() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const { data } = useQuery({
    queryKey: ['attack-map-canvas'],
    queryFn: () => getAttackMap(24, 200),
    refetchInterval: 10_000,
  })

  const attacks = (data?.attacks || []).filter((a) => a.latitude !== null && a.longitude !== null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let width = canvas.width
    let height = canvas.height

    const resize = () => {
      const rect = canvas.getBoundingClientRect()
      width = rect.width
      height = rect.height
      canvas.width = width * window.devicePixelRatio
      canvas.height = height * window.devicePixelRatio
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
    }
    resize()

    const drawWorld = () => {
      ctx.fillStyle = 'rgba(6, 182, 212, 0.08)'
      for (let i = 0; i < 120; i++) {
        const px = ((Math.sin(i * 13.5) + 1) / 2) * width
        const py = ((Math.cos(i * 7.3) + 1) / 2) * height
        ctx.beginPath()
        ctx.arc(px, py, 1.5, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    const project = (lon: number, lat: number): [number, number] => {
      return [((lon + 180) / 360) * width, ((90 - lat) / 180) * height]
    }

    const severityColor = (level: number): string => {
      if (level >= 13) return '#ef4444'
      if (level >= 10) return '#f97316'
      if (level >= 4) return '#f59e0b'
      return '#6fbf95'
    }

    const drawAttack = (lon: number, lat: number, color: string, offset: number) => {
      const [x, y] = project(lon, lat)
      const [tx, ty] = project(0, 30)

      ctx.strokeStyle = color
      ctx.lineWidth = 1
      ctx.globalAlpha = 0.3
      ctx.beginPath()
      ctx.moveTo(x, y)
      ctx.quadraticCurveTo((x + tx) / 2, Math.min(y, ty) - 60, tx, ty)
      ctx.stroke()
      ctx.globalAlpha = 1

      const t = (Date.now() / 1500 + offset) % 1
      const cx = (1 - t) * (1 - t) * x + 2 * (1 - t) * t * ((x + tx) / 2) + t * t * tx
      const cy = (1 - t) * (1 - t) * y + 2 * (1 - t) * t * (Math.min(y, ty) - 60) + t * t * ty

      ctx.fillStyle = color
      ctx.shadowColor = color
      ctx.shadowBlur = 10
      ctx.beginPath()
      ctx.arc(cx, cy, 3, 0, Math.PI * 2)
      ctx.fill()
      ctx.shadowBlur = 0

      ctx.fillStyle = color
      ctx.beginPath()
      ctx.arc(x, y, 3, 0, Math.PI * 2)
      ctx.fill()
    }

    let animationId: number
    const animate = () => {
      ctx.clearRect(0, 0, width, height)
      drawWorld()
      attacks.forEach((a, i) => drawAttack(a.longitude!, a.latitude!, severityColor(a.rule_level), i * 0.15))
      const [tx, ty] = project(0, 30)
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.6)'
      ctx.lineWidth = 1.5
      const t = Date.now() / 1000
      for (let i = 0; i < 3; i++) {
        const radius = ((t + i * 0.5) % 1.5) * 25 + 2
        ctx.globalAlpha = 1 - radius / 27
        ctx.beginPath()
        ctx.arc(tx, ty, radius, 0, Math.PI * 2)
        ctx.stroke()
      }
      ctx.globalAlpha = 1
      ctx.fillStyle = '#c97848'
      ctx.beginPath()
      ctx.arc(tx, ty, 4, 0, Math.PI * 2)
      ctx.fill()
      animationId = requestAnimationFrame(animate)
    }
    animate()

    const handleResize = () => resize()
    window.addEventListener('resize', handleResize)
    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener('resize', handleResize)
    }
  }, [attacks])

  return (
    <canvas
      ref={canvasRef}
      className="h-full w-full rounded-lg bg-gray-950/50"
      aria-label="Live attack map"
    />
  )
}
