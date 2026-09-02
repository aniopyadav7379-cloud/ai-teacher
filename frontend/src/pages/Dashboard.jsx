import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shell } from '../components/Shell'
import { api } from '../services/api'

const LEVELS = ['beginner', 'intermediate', 'advanced']
const STYLES = ['socratic', 'direct', 'story-driven', 'example-first']
const LANGUAGES = [
  ['en', 'English'], ['hi', 'Hindi'], ['hi-en', 'Hinglish'],
]

export default function Dashboard() {
  const navigate = useNavigate()
  const [mode, setMode] = useState('topic')
  const [topic, setTopic] = useState('')
  const [file, setFile] = useState(null)
  const [profile, setProfile] = useState({
    learner_level: 'beginner', goal: '', language: 'en',
    teaching_style: 'socratic', available_minutes: 20, depth: 'standard',
  })
  const [progress, setProgress] = useState(null)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => { api.getProgress().then(setProgress).catch(() => {}) }, [])

  async function createSession(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const session = await api.createSession({ mode, topic: mode === 'topic' ? topic : null, profile })
      if (mode === 'material') {
        if (!file) throw new Error('Choose a file to upload.')
        await api.uploadMaterial(session.id, file)
      }
      navigate(`/session/${session.id}`)
    } catch (e) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Shell>
      {progress && progress.total_lessons > 0 && (
        <div className="glass rounded-xl p-4 mb-8 flex gap-8 text-sm">
          <div><span className="text-white/50">Lessons completed</span> <span className="text-cyan-400 font-medium">{progress.completed_lessons}</span></div>
          <div><span className="text-white/50">Topics studied</span> <span className="text-cyan-400 font-medium">{progress.topics_studied.length}</span></div>
        </div>
      )}

      <h1 className="font-display text-2xl font-semibold text-white mb-6">Start a lesson</h1>

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setMode('topic')}
          className={`px-4 py-2 rounded-lg text-sm transition-colors ${mode === 'topic' ? 'bg-cyan-500 text-navy-950 font-medium' : 'glass text-white/70'}`}
        >
          Enter a topic
        </button>
        <button
          onClick={() => setMode('material')}
          className={`px-4 py-2 rounded-lg text-sm transition-colors ${mode === 'material' ? 'bg-cyan-500 text-navy-950 font-medium' : 'glass text-white/70'}`}
        >
          Upload material
        </button>
      </div>

      <form onSubmit={createSession} className="glass rounded-2xl p-6 space-y-5">
        {mode === 'topic' ? (
          <input
            required
            placeholder="e.g. Newton's Laws, React for a technical interview, Ohm's Law"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="w-full bg-navy-900/70 border border-white/10 rounded-lg px-3 py-2.5 text-sm outline-none focus:border-cyan-400"
          />
        ) : (
          <input
            type="file"
            required
            accept=".pdf,.docx,.doc,.pptx,.ppt,.txt,.md"
            onChange={(e) => setFile(e.target.files[0])}
            className="w-full text-sm text-white/70 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-cyan-500 file:text-navy-950 file:font-medium"
          />
        )}

        <div className="grid sm:grid-cols-2 gap-4">
          <label className="text-xs text-white/50 block">
            Your level
            <select
              value={profile.learner_level}
              onChange={(e) => setProfile({ ...profile, learner_level: e.target.value })}
              className="w-full mt-1 bg-navy-900/70 border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
            >
              {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </label>
          <label className="text-xs text-white/50 block">
            Teaching style
            <select
              value={profile.teaching_style}
              onChange={(e) => setProfile({ ...profile, teaching_style: e.target.value })}
              className="w-full mt-1 bg-navy-900/70 border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
            >
              {STYLES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label className="text-xs text-white/50 block">
            Language
            <select
              value={profile.language}
              onChange={(e) => setProfile({ ...profile, language: e.target.value })}
              className="w-full mt-1 bg-navy-900/70 border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
            >
              {LANGUAGES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </label>
          <label className="text-xs text-white/50 block">
            Time available: {profile.available_minutes} min
            <input
              type="range" min={5} max={90} step={5}
              value={profile.available_minutes}
              onChange={(e) => setProfile({ ...profile, available_minutes: Number(e.target.value) })}
              className="w-full mt-2 accent-cyan-400"
            />
          </label>
        </div>

        <input
          placeholder="What's your goal? (e.g. pass my exam, understand it for an interview)"
          value={profile.goal}
          onChange={(e) => setProfile({ ...profile, goal: e.target.value })}
          className="w-full bg-navy-900/70 border border-white/10 rounded-lg px-3 py-2.5 text-sm outline-none focus:border-cyan-400"
        />

        {error && <p className="text-red-400 text-xs">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="px-5 py-2.5 rounded-lg bg-cyan-500 text-navy-950 font-medium hover:bg-cyan-400 transition-colors disabled:opacity-50"
        >
          {submitting ? 'Creating session…' : 'Continue'}
        </button>
      </form>
    </Shell>
  )
}
