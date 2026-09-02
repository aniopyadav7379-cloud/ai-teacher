import { useRef, useState, useCallback, useEffect } from 'react'

/**
 * Plays a TTS audio URL and analyses live amplitude via Web Audio API to
 * drive the avatar's mouthOpen value — real lip-sync from real audio, not a
 * canned animation loop.
 */
export function useSpeakingAudio() {
  const audioRef = useRef(null)
  const analyserRef = useRef(null)
  const rafRef = useRef(null)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [mouthOpen, setMouthOpen] = useState(0)

  const tick = useCallback(() => {
    if (!analyserRef.current) return
    const data = new Uint8Array(analyserRef.current.frequencyBinCount)
    analyserRef.current.getByteFrequencyData(data)
    const avg = data.reduce((a, b) => a + b, 0) / data.length
    setMouthOpen(Math.min(avg / 90, 1))
    rafRef.current = requestAnimationFrame(tick)
  }, [])

  const play = useCallback((url) => {
    stop()
    const audio = new Audio(url)
    audioRef.current = audio
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)()
      const source = ctx.createMediaElementSource(audio)
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 64
      source.connect(analyser)
      analyser.connect(ctx.destination)
      analyserRef.current = analyser
      rafRef.current = requestAnimationFrame(tick)
    } catch {
      // Web Audio unavailable — audio still plays, just without lip-sync.
    }
    audio.onplay = () => setIsSpeaking(true)
    audio.onended = () => { setIsSpeaking(false); setMouthOpen(0) }
    audio.play().catch(() => setIsSpeaking(false))
  }, [tick])

  const stop = useCallback(() => {
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null }
    if (rafRef.current) cancelAnimationFrame(rafRef.current)
    setIsSpeaking(false)
    setMouthOpen(0)
  }, [])

  useEffect(() => () => stop(), [stop])

  return { play, stop, isSpeaking, mouthOpen }
}
