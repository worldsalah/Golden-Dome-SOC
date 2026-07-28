import { useEffect, useRef } from 'react'

interface Attack {
  from: { x: number; y: number }
  to: { x: number; y: number }
  color: string
}

const attacks: Attack[] = [
  { from: { x: 0.18, y: 0.35 }, to: { x: 0.58, y: 0.42 }, color: '#ef4444' },
  { from: { x: 0.25, y: 0.55 }, to: { x: 0.55, y: 0.4 }, color: '#f97316' },
  { from: { x: 0.72, y: 0.28 }, to: { x: 0.58, y: 0.42 }, color: '#f59e0b' },
  { from: { x: 0.45, y: 0.25 }, to: { x: 0.56, y: 0.45 }, color: '#ef4444' },
  { from: { x: 0.82, y: 0.6 }, to: { x: 0.6, y: 0.48 }, color: '#c97848' },
]

export function AttackMap() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

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
      // Simple stylized world dots
      ctx.fillStyle = 'rgba(6, 182, 212, 0.08)'
      for (let i = 0; i < 120; i++) {
        const px = ((Math.sin(i * 13.5) + 1) / 2) * width
        const py = ((Math.cos(i * 7.3) + 1) / 2) * height
        ctx.beginPath()
        ctx.arc(px, py, 1.5, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    const drawTarget = (x: number, y: number) => {
      const t = Date.now() / 1000
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.6)'
      ctx.lineWidth = 1.5
      for (let i = 0; i < 3; i++) {
        const radius = ((t + i * 0.5) % 1.5) * 25 + 2
        ctx.globalAlpha = 1 - radius / 27
        ctx.beginPath()
        ctx.arc(x, y, radius, 0, Math.PI * 2)
        ctx.stroke()
      }
      ctx.globalAlpha = 1
      ctx.fillStyle = '#c97848'
      ctx.beginPath()
      ctx.arc(x, y, 4, 0, Math.PI * 2)
      ctx.fill()
    }

    const drawAttack = (attack: Attack, offset: number) => {
      const fx = attack.from.x * width
      const fy = attack.from.y * height
      const tx = attack.to.x * width
      const ty = attack.to.y * height

      ctx.strokeStyle = attack.color
      ctx.lineWidth = 1
      ctx.globalAlpha = 0.3
      ctx.beginPath()
      ctx.moveTo(fx, fy)
      ctx.quadraticCurveTo((fx + tx) / 2, Math.min(fy, ty) - 60, tx, ty)
      ctx.stroke()
      ctx.globalAlpha = 1

      const t = (Date.now() / 1500 + offset) % 1
      const cx = (1 - t) * (1 - t) * fx + 2 * (1 - t) * t * ((fx + tx) / 2) + t * t * tx
      const cy =
        (1 - t) * (1 - t) * fy +
        2 * (1 - t) * t * (Math.min(fy, ty) - 60) +
        t * t * ty

      ctx.fillStyle = attack.color
      ctx.shadowColor = attack.color
      ctx.shadowBlur = 10
      ctx.beginPath()
      ctx.arc(cx, cy, 3, 0, Math.PI * 2)
      ctx.fill()
      ctx.shadowBlur = 0
    }

    let animationId: number
    const animate = () => {
      ctx.clearRect(0, 0, width, height)
      drawWorld()
      attacks.forEach((a, i) => drawAttack(a, i * 0.15))
      drawTarget(width * 0.58, height * 0.42)
      animationId = requestAnimationFrame(animate)
    }
    animate()

    const handleResize = () => {
      resize()
    }
    window.addEventListener('resize', handleResize)
    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="h-full w-full rounded-lg bg-gray-950/50"
      aria-label="Live attack map"
    />
  )
}
