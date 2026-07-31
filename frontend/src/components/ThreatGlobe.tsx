import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, useTexture } from '@react-three/drei'
import { Suspense, useMemo, useRef } from 'react'
import * as THREE from 'three'

type Attack = {
  from: { lat: number; lon: number }
  to: { lat: number; lon: number }
  color?: string
}

function latLonToVector3(lat: number, lon: number, radius = 2.02) {
  const phi = (90 - lat) * (Math.PI / 180)
  const theta = (lon + 180) * (Math.PI / 180)
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  )
}

function AttackArcs({ attacks }: { attacks: Attack[] }) {
  const groupRef = useRef<THREE.Group>(null)
  const materialRefs = useRef<THREE.LineBasicMaterial[]>([])

  const lines = useMemo(() => {
    return attacks.map((attack) => {
      const start = latLonToVector3(attack.from.lat, attack.from.lon)
      const end = latLonToVector3(attack.to.lat, attack.to.lon)
      const mid = start.clone().add(end).normalize().multiplyScalar(3.0)
      const curve = new THREE.QuadraticBezierCurve3(start, mid, end)
      const points = curve.getPoints(32)
      const geometry = new THREE.BufferGeometry().setFromPoints(points)
      const material = new THREE.LineBasicMaterial({
        color: attack.color || '#c97848',
        transparent: true,
        opacity: 0.65,
      })
      materialRefs.current.push(material)
      return new THREE.Line(geometry, material)
    })
  }, [attacks])

  useFrame(({ clock }) => {
    const t = clock.elapsedTime
    materialRefs.current.forEach((material, i) => {
      material.opacity = 0.35 + 0.3 * Math.sin(t * 2 + i * 0.7)
    })
    if (groupRef.current) groupRef.current.rotation.y += 0.002
  })

  return <group ref={groupRef}>{lines.map((line, i) => <primitive key={i} object={line} />)}</group>
}

function Earth() {
  const globe = useRef<THREE.Group>(null)
  const texture = useTexture('/earth-day.jpg')
  useFrame((_, delta) => { if (globe.current) globe.current.rotation.y += delta * .07 })
  return (
    <group ref={globe}>
      <mesh>
        <sphereGeometry args={[2, 96, 96]} />
        <meshStandardMaterial map={texture} roughness={.8} metalness={.02} emissive="#080a0a" emissiveIntensity={.18} />
      </mesh>
      <mesh scale={1.025}>
        <sphereGeometry args={[2, 64, 64]} />
        <meshBasicMaterial color="#d6ecdc" transparent opacity={.055} />
      </mesh>
    </group>
  )
}

export function ThreatGlobe({ attacks }: { attacks?: Attack[] }) {
  const hasAttacks = attacks && attacks.length > 0
  return (
    <div className="relative h-full w-full overflow-hidden bg-[#090909]" aria-label="Rotating Earth globe">
      <div className="absolute left-1/2 top-1/2 z-0 h-[min(68vw,560px)] w-[min(68vw,560px)] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#314842] opacity-40 blur-2xl" />
      <div className="relative z-10 h-full w-full">
        <Canvas camera={{ position: [0, 0, 6.4], fov: 38 }} dpr={[1, 1.75]}>
          <ambientLight intensity={1.3} />
          <directionalLight position={[5, 3, 5]} intensity={2.2} color="#fff2dc" />
          <Suspense fallback={null}>
            <Earth />
            {hasAttacks && <AttackArcs attacks={attacks} />}
          </Suspense>
          <OrbitControls enablePan={false} enableZoom={false} autoRotate={!hasAttacks} autoRotateSpeed={0.7} />
        </Canvas>
      </div>
    </div>
  )
}
