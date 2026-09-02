import { Canvas } from '@react-three/fiber'
import { Avatar3D } from './Avatar3D'

/**
 * Wraps Avatar3D in a Canvas with lighting. Used everywhere the teacher
 * "speaks" — lesson player and video generation fallback.
 */
export function AvatarStage({ isSpeaking, isListening, isLoading, mouthOpen, className = '' }) {
  return (
    <div className={`relative rounded-2xl overflow-hidden bg-navy-900/60 border border-white/5 ${className}`}>
      <Canvas camera={{ position: [0, 0, 3.2], fov: 40 }}>
        <ambientLight intensity={0.7} />
        <pointLight position={[2, 2, 2]} intensity={40} color="#22d3ee" />
        <pointLight position={[-2, -1, 2]} intensity={20} color="#ffffff" />
        <Avatar3D isSpeaking={isSpeaking} isListening={isListening} isLoading={isLoading} mouthOpen={mouthOpen} />
      </Canvas>
    </div>
  )
}
