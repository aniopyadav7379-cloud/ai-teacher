import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Shell } from '../components/Shell'
import { api } from '../services/api'

export default function Report() {
  const { lessonId } = useParams()
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    (async () => {
      try {
        setReport(await api.generateAssessment(lessonId))
      } catch (e) {
        setError(e.message)
      }
    })()
  }, [lessonId])

  if (error) return <Shell><p className="text-red-400 text-sm">{error}</p></Shell>
  if (!report) return <Shell><p className="text-white/50">Scoring your lesson…</p></Shell>

  return (
    <Shell>
      <h1 className="font-display text-2xl font-semibold text-white mb-1">Lesson report</h1>
      <p className="text-white/50 text-sm mb-8">Here's how it went.</p>

      <div className="glass rounded-2xl p-8 mb-6 text-center">
        <div className="font-display text-5xl font-semibold text-cyan-400">{Math.round(report.overall_score * 100)}%</div>
        <p className="text-white/50 text-sm mt-1">overall score</p>
      </div>

      <div className="grid sm:grid-cols-2 gap-4 mb-6">
        <div className="glass rounded-xl p-5">
          <h2 className="text-emerald-400 text-sm font-medium mb-3">Strong</h2>
          {report.strong_areas.length ? (
            <ul className="space-y-1 text-sm text-white/80">{report.strong_areas.map((a) => <li key={a}>{a}</li>)}</ul>
          ) : <p className="text-white/40 text-sm">Nothing flagged yet.</p>}
        </div>
        <div className="glass rounded-xl p-5">
          <h2 className="text-amber-400 text-sm font-medium mb-3">Needs revision</h2>
          {report.weak_areas.length ? (
            <ul className="space-y-1 text-sm text-white/80">{report.weak_areas.map((a) => <li key={a}>{a}</li>)}</ul>
          ) : <p className="text-white/40 text-sm">No weak spots detected.</p>}
        </div>
      </div>

      <div className="glass rounded-xl p-5 mb-8">
        <h2 className="text-white text-sm font-medium mb-2">Recommendation</h2>
        <p className="text-white/70 text-sm leading-relaxed">{report.recommendation}</p>
      </div>

      <Link to="/dashboard" className="px-5 py-2.5 rounded-lg bg-cyan-500 text-navy-950 font-medium hover:bg-cyan-400 transition-colors inline-block">
        Start another lesson
      </Link>
    </Shell>
  )
}
