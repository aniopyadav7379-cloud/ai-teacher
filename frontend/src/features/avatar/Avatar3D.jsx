/**
 * Ported from 3d-teacher-ia-main/src/components/Avatar.jsx (see
 * docs/COMPONENT_INVENTORY.md for the reuse decision). Procedural, no
 * external 3D assets needed. Extended with a `mouthOpen` prop (0..1) driven
 * by live TTS audio amplitude for real lip-sync, replacing the original's
 * static "speaking" bar.
 */
import { useRef, useState, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import { Sphere, Cylinder } from '@react-three/drei'
import * as THREE from 'three'

export function Avatar3D({ isSpeaking, isListening, isLoading, mouthOpen = 0 }) {
  const groupRef = useRef()
  const headRef = useRef()
  const leftHandRef = useRef()
  const rightHandRef = useRef()

  const [blink, setBlink] = useState(false)
  useEffect(() => {
    let alive = true
    const blinkLoop = () => {
      if (!alive) return
      setBlink(true)
      setTimeout(() => setBlink(false), 150)
      setTimeout(blinkLoop, 2000 + Math.random() * 3000)
    }
    const t = setTimeout(blinkLoop, 2000)
    return () => { alive = false; clearTimeout(t) }
  }, [])

  useFrame((state) => {
    const t = state.clock.getElapsedTime()
    if (groupRef.current) {
      if (isLoading) {
        groupRef.current.position.y = 0.4 + Math.sin(t * 10) * 0.05
        groupRef.current.rotation.y += 0.05
      } else {
        groupRef.current.position.y = 0.4 + Math.sin(t * 1) * 0.1
        groupRef.current.rotation.y = Math.sin(t * 0.5) * 0.05
      }
    }
    if (headRef.current) {
      if (isLoading) {
        headRef.current.rotation.x = Math.sin(t * 10) * 0.1
        headRef.current.rotation.y = 0
      } else {
        const targetX = state.mouse.y * 0.3
        const targetY = state.mouse.x * 0.3
        headRef.current.rotation.x = THREE.MathUtils.lerp(headRef.current.rotation.x, targetX, 0.1)
        headRef.current.rotation.y = THREE.MathUtils.lerp(headRef.current.rotation.y, targetY, 0.1)
      }
    }
    if (leftHandRef.current && rightHandRef.current) {
      leftHandRef.current.position.y = -0.5 + Math.sin(t * 2 + 1) * 0.05
      rightHandRef.current.position.y = -0.5 + Math.sin(t * 2 + 2) * 0.05
      if (isSpeaking) {
        rightHandRef.current.position.x = 0.6 + Math.sin(t * 10) * 0.1
        rightHandRef.current.rotation.z = Math.sin(t * 10) * 0.2
      }
    }
  })

  const primaryColor = isLoading ? '#f1c40f' : '#22d3ee'
  const baseColor = '#e8ecf3'
  const screenColor = '#0a0e1a'
  const mouthHeight = 0.015 + mouthOpen * 0.09

  return (
    <group ref={groupRef} position={[0, 0.4, 0]}>
      <group ref={headRef}>
        <mesh>
          <boxGeometry args={[0.8, 0.7, 0.7]} />
          <meshStandardMaterial color={baseColor} />
        </mesh>
        <Sphere args={[0.55, 32, 32]} scale={[1, 0.85, 0.85]}>
          <meshStandardMaterial color={baseColor} roughness={0.2} metalness={0.1} />
        </Sphere>

        <group position={[0, 0, 0.38]}>
          <mesh>
            <planeGeometry args={[0.6, 0.35]} />
            <meshStandardMaterial color={screenColor} roughness={0.2} metalness={0.8} />
          </mesh>
          <mesh position={[0, 0, -0.01]}>
            <boxGeometry args={[0.65, 0.4, 0.1]} />
            <meshStandardMaterial color="#1a2138" />
          </mesh>

          <group position={[0, 0.05, 0.01]}>
            <mesh position={[-0.15, 0, 0]} scale={[1, blink ? 0.1 : 1, 1]}>
              <circleGeometry args={[0.06, 32]} />
              <meshBasicMaterial color={primaryColor} toneMapped={false} />
            </mesh>
            <mesh position={[0.15, 0, 0]} scale={[1, blink ? 0.1 : 1, 1]}>
              <circleGeometry args={[0.06, 32]} />
              <meshBasicMaterial color={primaryColor} toneMapped={false} />
            </mesh>
          </group>

          {(isSpeaking || mouthOpen > 0) && (
            <mesh position={[0, -0.1, 0.01]}>
              <planeGeometry args={[0.2, mouthHeight]} />
              <meshBasicMaterial color={primaryColor} toneMapped={false} />
            </mesh>
          )}
        </group>

        <group position={[0, 0.5, 0]}>
          <Cylinder args={[0.02, 0.02, 0.3]} position={[0, 0.15, 0]}>
            <meshStandardMaterial color="#1a2138" />
          </Cylinder>
          <Sphere args={[0.08]} position={[0, 0.3, 0]}>
            <meshStandardMaterial
              color={isListening ? '#ff4757' : primaryColor}
              emissive={isListening ? '#ff4757' : primaryColor}
              emissiveIntensity={0.5}
            />
          </Sphere>
        </group>
      </group>

      <group position={[0, -0.8, 0]}>
        <Sphere args={[0.4, 32, 32]} scale={[1, 1.2, 1]}>
          <meshStandardMaterial color={baseColor} roughness={0.2} />
        </Sphere>
        <mesh position={[0, 0, 0.35]}>
          <circleGeometry args={[0.12, 32]} />
          <meshStandardMaterial color="#1a2138" />
        </mesh>
        <mesh position={[0, 0, 0.36]}>
          <circleGeometry args={[0.08, 32]} />
          <meshBasicMaterial color={primaryColor} toneMapped={false} />
        </mesh>
      </group>

      <group position={[0, -0.2, 0]}>
        <group ref={leftHandRef} position={[-0.6, -0.5, 0.2]}>
          <Sphere args={[0.12, 16, 16]}>
            <meshStandardMaterial color={baseColor} />
          </Sphere>
        </group>
        <group ref={rightHandRef} position={[0.6, -0.5, 0.2]}>
          <Sphere args={[0.12, 16, 16]}>
            <meshStandardMaterial color={baseColor} />
          </Sphere>
          <group position={[0, 0.2, 0]} rotation={[-0.5, 0, 0]}>
            <mesh>
              <boxGeometry args={[0.4, 0.5, 0.02]} />
              <meshStandardMaterial color="#1a2138" />
            </mesh>
            <mesh position={[0, 0, 0.02]}>
              <planeGeometry args={[0.36, 0.46]} />
              <meshBasicMaterial color={primaryColor} transparent opacity={0.3} side={THREE.DoubleSide} />
            </mesh>
          </group>
        </group>
      </group>
    </group>
  )
}
