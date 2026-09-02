import { useEffect, useRef, useState } from 'react'
import { AvatarStage } from '../avatar/AvatarStage'
import { api } from '../../services/api'
import { useSpeakingAudio } from '../../hooks/useSpeakingAudio'

const STATUS_LABEL = {
  pending: 'Preparing…',
  script_ready: 'Writing the lesson…',
  voice_ready: 'Voice ready',
  assembling: 'Rendering avatar video…',
  ready: null,
  failed: null,
}

/**
 * Drives the "teacher" visual for the current concept:
 *  - polls /teaching/video/{conceptId} for status (limitation #2: D-ID's
 *    talking-head video is generated asynchronously, so this actually
 *    surfaces the async states instead of only reading audio_url)
 *  - if the avatar provider returns a rendered video (avatar_video_url,
 *    e.g. D-ID), plays that <video> directly
 *  - otherwise (the default browser-avatar path, or while a video job is
 *    still processing) falls back to the live 3D avatar lip-synced to the
 *    TTS audio via Web Audio amplitude analysis
 */
export function TeacherStage({ conceptId, isWaitingForAnswer, isChecking, className }) {
  const [video, setVideo] = useState(null)
  const [statusNote, setStatusNote] = useState(null)
  const pollRef = useRef(null)
  const { play, isSpeaking, mouthOpen } = useSpeakingAudio()
  const playedAudioFor = useRef(null)

  useEffect(() => {
    let cancelled = false
    setVideo(null)
    setStatusNote('Preparing…')

    async function start() {
      try {
        await api.generateVideo(conceptId)
      } catch {
        setStatusNote(null)
        return // no TTS/avatar keys configured — teach silently via text
      }
      poll()
    }

    async function poll() {
      if (cancelled) return
      try {
        const v = await api.getVideoStatus(conceptId)
        if (cancelled) return
        setVideo(v)
        setStatusNote(STATUS_LABEL[v.status] ?? null)

        if (v.audio_url && !v.avatar_video_url && playedAudioFor.current !== conceptId) {
          playedAudioFor.current = conceptId
          play(v.audio_url)
        }

        if (v.status === 'ready' || v.status === 'failed') return
        pollRef.current = setTimeout(poll, 1500)
      } catch {
        setStatusNote(null)
      }
    }

    start()
    return () => { cancelled = true; clearTimeout(pollRef.current) }
  }, [conceptId]) // eslint-disable-line react-hooks/exhaustive-deps

  const hasRenderedVideo = video?.status === 'ready' && video?.avatar_video_url

  return (
    <div className={className}>
      {hasRenderedVideo ? (
        <video
          key={video.avatar_video_url}
          src={video.avatar_video_url}
          autoPlay
          controls
          className="w-full h-full object-cover rounded-2xl bg-navy-900/60 border border-white/5"
        />
      ) : (
        <AvatarStage
          isSpeaking={isSpeaking}
          isListening={isWaitingForAnswer}
          isLoading={isChecking}
          mouthOpen={mouthOpen}
          className="h-full"
        />
      )}
      {statusNote && (
        <div className="mt-2 text-center text-white/40 text-xs">{statusNote}</div>
      )}
      {video?.status === 'failed' && (
        <div className="mt-2 text-center text-amber-400/80 text-xs">
          Spoken/video playback isn't available right now — teaching continues as text.
        </div>
      )}
    </div>
  )
}
