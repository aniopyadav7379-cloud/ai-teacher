import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Shell } from '../components/Shell'
import { api } from '../services/api'

export default function SessionPrep() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [session, setSession] = useState(null)
  const [materials, setMaterials] = useState([])
  const [planning, setPlanning] = useState(false)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    const s = await api.getSession(sessionId)
    setSession(s)
    if (s.mode === 'material') {
      setMaterials(await api.listSessionMaterials(sessionId))
    }
  }, [sessionId])

  useEffect(() => { refresh() }, [refresh])

  useEffect(() => {
    if (!materials.length) return
    if (materials.every((m) => m.status === 'ready' || m.status === 'failed')) return
    const t = setInterval(refresh, 2000)
    return () => clearInterval(t)
  }, [materials, refresh])

  async function plan() {
    setPlanning(true)
    setError(null)
    try {
      const lesson = await api.planLesson(sessionId)
      await api.startLesson(sessionId)
      navigate(`/lesson/${lesson.id}`)
    } catch (e) {
      setError(e.message)
    } finally {
      setPlanning(false)
    }
  }

  if (!session) return <Shell><p className="text-white/50">Loading…</p></Shell>

  const materialsReady = session.mode === 'topic' || (materials.length > 0 && materials.every((m) => m.status === 'ready'))
  const materialsFailed = materials.some((m) => m.status === 'failed')

  return (
    <Shell>
      <h1 className="font-display text-2xl font-semibold text-white mb-2">
        {session.topic || 'Your uploaded material'}
      </h1>
      <p className="text-white/50 text-sm mb-8">
        {session.learner_level} · {session.language} · {session.available_minutes} min
      </p>

      {session.mode === 'material' && (
        <div className="glass rounded-2xl p-6 mb-6">
          <h2 className="font-medium text-white mb-3 text-sm">Processing your material</h2>
          {materials.map((m) => (
            <div key={m.id} className="flex items-center justify-between text-sm py-2 border-b border-white/5 last:border-0">
              <span className="text-white/80">{m.filename}</span>
              <StatusBadge status={m.status} />
            </div>
          ))}
          {materialsFailed && (
            <p className="text-red-400 text-xs mt-3">
              {materials.find((m) => m.status === 'failed')?.error_message}
            </p>
          )}
        </div>
      )}

      {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

      <button
        onClick={plan}
        disabled={!materialsReady || materialsFailed || planning}
        className="px-6 py-3 rounded-lg bg-cyan-500 text-navy-950 font-medium hover:bg-cyan-400 transition-colors disabled:opacity-40"
      >
        {planning ? 'Planning your lesson…' : 'Generate lesson plan'}
      </button>
    </Shell>
  )
}

function StatusBadge({ status }) {
  const colors = {
    uploaded: 'text-white/50', processing: 'text-cyan-400', ready: 'text-emerald-400', failed: 'text-red-400',
  }
  return <span className={`text-xs font-medium ${colors[status] || 'text-white/50'}`}>{status}</span>
}
