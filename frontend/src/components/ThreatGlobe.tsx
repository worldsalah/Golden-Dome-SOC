import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, useTexture } from '@react-three/drei'
import { Suspense, useRef } from 'react'
import * as THREE from 'three'

function Earth() {
  const globe = useRef<THREE.Group>(null)
  const texture = useTexture('/earth-day.jpg')
  useFrame((_, delta) => { if (globe.current) globe.current.rotation.y += delta * .07 })
  return <group ref={globe}><mesh><sphereGeometry args={[2, 96, 96]} /><meshStandardMaterial map={texture} roughness={.8} metalness={.02} emissive="#080a0a" emissiveIntensity={.18} /></mesh><mesh scale={1.025}><sphereGeometry args={[2, 64, 64]} /><meshBasicMaterial color="#d6ecdc" transparent opacity={.055} /></mesh></group>
}

export function ThreatGlobe() {
  return <div className="relative h-full w-full overflow-hidden bg-[#090909]" aria-label="Rotating Earth globe"><div className="absolute left-1/2 top-1/2 z-0 h-[min(68vw,560px)] w-[min(68vw,560px)] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#314842] opacity-40 blur-2xl" /><div className="relative z-10 h-full w-full"><Canvas camera={{ position: [0, 0, 6.4], fov: 38 }} dpr={[1, 1.75]}><ambientLight intensity={1.3} /><directionalLight position={[5, 3, 5]} intensity={2.2} color="#fff2dc" /><Suspense fallback={null}><Earth /></Suspense><OrbitControls enablePan={false} enableZoom={false} /></Canvas></div></div>
}
