import { useState } from 'react'
import { api } from '../../services/api'

const LANGUAGES = [
  ['en', 'English'], ['hi', 'Hindi'], ['hi-en', 'Hinglish'],
]

/**
 * Switches the active lesson's language mid-lesson (limitation #3). Calls
 * POST /lessons/{id}/language, which translates only the not-yet-taught
 * concepts in place — current_concept_index and response history are
 * untouched (see backend/services/lesson/translator.py) — so this never
 * restarts the lesson, just re-renders it in the new language.
 */
export function LanguageSwitcher({ lessonId, currentLanguage, onSwitched }) {
  const [switching, setSwitching] = useState(false)
  const [error, setError] = useState(null)

  async function handleChange(e) {
    const language = e.target.value
    if (language === currentLanguage) return
    setSwitching(true)
    setError(null)
    try {
      const updated = await api.switchLessonLanguage(lessonId, language)
      onSwitched(updated)
    } catch (err) {
      setError(err.message)
    } finally {
      setSwitching(false)
    }
  }

  return (
    <div className="flex items-center gap-2">
      <select
        value={currentLanguage}
        onChange={handleChange}
        disabled={switching}
        className="bg-navy-900/70 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white/70 outline-none focus:border-cyan-400 disabled:opacity-50"
        title="Switch lesson language — keeps your progress"
      >
        {LANGUAGES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
      {switching && <span className="text-xs text-cyan-400">Translating…</span>}
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  )
}
