import { useEffect, useState } from 'react'
import { Shell } from '../components/Shell'
import { api } from '../services/api'

export default function Progress() {
  const [data, setData] = useState(null)
  useEffect(() => { api.getProgress().then(setData) }, [])
  if (!data) return <Shell><p className="text-white/50">Loading…</p></Shell>

  return (
    <Shell>
      <h1 className="font-display text-2xl font-semibold text-white mb-8">Your progress</h1>

      <div className="grid sm:grid-cols-3 gap-4 mb-8">
        {[
          ['Sessions started', data.total_sessions],
          ['Lessons completed', data.completed_lessons],
          ['Topics studied', data.topics_studied.length],
        ].map(([label, value]) => (
          <div key={label} className="glass rounded-xl p-5">
            <div className="font-display text-3xl text-cyan-400">{value}</div>
            <div className="text-white/50 text-xs mt-1">{label}</div>
          </div>
        ))}
      </div>

      <div className="glass rounded-xl p-5 mb-6">
        <h2 className="text-white text-sm font-medium mb-3">History</h2>
        {data.history.length ? (
          <ul className="divide-y divide-white/5">
            {data.history.map((h) => (
              <li key={h.lesson_id} className="py-2 flex justify-between text-sm">
                <span className="text-white/80">{h.title}</span>
                <span className="text-white/40 text-xs">{h.status}</span>
              </li>
            ))}
          </ul>
        ) : <p className="text-white/40 text-sm">No lessons yet.</p>}
      </div>
    </Shell>
  )
}
