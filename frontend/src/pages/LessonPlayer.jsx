import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Shell } from '../components/Shell'
import { TeacherStage } from '../features/lesson/TeacherStage'
import { LanguageSwitcher } from '../features/lesson/LanguageSwitcher'
import { api } from '../services/api'

export default function LessonPlayer() {
  const { lessonId } = useParams()
  const navigate = useNavigate()
  const [lesson, setLesson] = useState(null)
  const [answer, setAnswer] = useState('')
  const [result, setResult] = useState(null)
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    const l = await api.getLesson(lessonId)
    setLesson(l)
    const concept = l.concepts[l.current_concept_index]
    setActiveQuestion(concept?.question || null)
    return l
  }, [lessonId])

  useEffect(() => { load() }, [load])

  function handleLanguageSwitched(updatedLesson) {
    setLesson(updatedLesson)
    const concept = updatedLesson.concepts[updatedLesson.current_concept_index]
    setActiveQuestion(concept?.question || null)
  }

  async function submitAnswer(e) {
    e.preventDefault()
    if (!activeQuestion) return
    setSubmitting(true)
    setError(null)
    try {
      const res = await api.answerQuestion(activeQuestion.id, answer)
      setResult(res)
      setAnswer('')
      if (res.advanced) {
        setTimeout(async () => {
          setResult(null)
          if (res.lesson_status === 'completed') {
            navigate(`/lesson/${lessonId}/report`)
          } else {
            await load()
          }
        }, 2200)
      } else if (res.reexplanation?.followup_question) {
        // Reuse the same question slot with a fresh, targeted follow-up.
        setActiveQuestion({
          id: activeQuestion.id, // same question id: still submits into the same concept's evaluation history
          prompt: res.reexplanation.followup_question.prompt,
          options: res.reexplanation.followup_question.options,
          question_type: res.reexplanation.followup_question.question_type,
        })
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (!lesson) return <Shell><p className="text-white/50">Loading…</p></Shell>

  const concept = lesson.concepts[lesson.current_concept_index]
  const progressPct = Math.round(((lesson.current_concept_index) / Math.max(lesson.concepts.length, 1)) * 100)

  return (
    <Shell>
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-display text-xl font-semibold text-white">{lesson.title}</h1>
        <div className="flex items-center gap-4">
          <LanguageSwitcher lessonId={lesson.id} currentLanguage={lesson.language} onSwitched={handleLanguageSwitched} />
          <span className="text-xs text-white/50">{lesson.current_concept_index + 1} / {lesson.concepts.length}</span>
        </div>
      </div>
      <div className="h-1 bg-white/10 rounded-full mb-8 overflow-hidden">
        <div className="h-full bg-cyan-400 transition-all duration-500" style={{ width: `${progressPct}%` }} />
      </div>

      <div className="grid md:grid-cols-[1fr_1.4fr] gap-6">
        <TeacherStage
          conceptId={concept.id}
          isWaitingForAnswer={!!activeQuestion && !result}
          isChecking={submitting}
          className="h-80"
        />

        <div className="space-y-4">
          <div className="glass rounded-2xl p-6">
            <div className="text-xs text-cyan-400 mb-2">{concept.concept}</div>
            <p className="text-white/90 leading-relaxed text-sm">{concept.explanation}</p>
            {concept.analogy && <p className="text-white/60 text-sm mt-3 italic">{concept.analogy}</p>}
            {concept.example && <p className="text-white/60 text-sm mt-2"><span className="text-white/40">Example: </span>{concept.example}</p>}
            {concept.source_citation && (
              <p className="text-white/30 text-xs mt-3">Based on {concept.source_citation}</p>
            )}
          </div>

          {result?.reexplanation && (
            <div className="glass rounded-2xl p-6 border-l-2 border-l-amber-400">
              <div className="text-xs text-amber-400 mb-2">Let's look at it differently</div>
              <p className="text-white/90 text-sm leading-relaxed">{result.reexplanation.reexplanation}</p>
              <p className="text-white/60 text-sm mt-2 italic">{result.reexplanation.new_analogy}</p>
            </div>
          )}

          {result && (
            <div className={`glass rounded-2xl p-5 border-l-2 ${result.evaluation.correct ? 'border-l-emerald-400' : 'border-l-amber-400'}`}>
              <p className="text-sm text-white/90">{result.evaluation.reasoning}</p>
              {result.advanced && <p className="text-emerald-400 text-xs mt-2">Moving on…</p>}
            </div>
          )}

          {activeQuestion && !result?.advanced && (
            <form onSubmit={submitAnswer} className="glass rounded-2xl p-6">
              <p className="text-white text-sm mb-3">{activeQuestion.prompt}</p>
              {activeQuestion.options ? (
                <div className="space-y-2">
                  {activeQuestion.options.map((opt) => (
                    <button
                      type="button"
                      key={opt}
                      onClick={() => setAnswer(opt)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm border transition-colors ${answer === opt ? 'border-cyan-400 bg-cyan-400/10' : 'border-white/10 text-white/70'}`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              ) : (
                <textarea
                  required
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  rows={3}
                  placeholder="Type your answer…"
                  className="w-full bg-navy-900/70 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-cyan-400"
                />
              )}
              {error && <p className="text-red-400 text-xs mt-2">{error}</p>}
              <button
                type="submit"
                disabled={submitting || !answer}
                className="mt-4 px-5 py-2 rounded-lg bg-cyan-500 text-navy-950 text-sm font-medium hover:bg-cyan-400 transition-colors disabled:opacity-40"
              >
                {submitting ? 'Checking…' : 'Submit answer'}
              </button>
            </form>
          )}
        </div>
      </div>
    </Shell>
  )
}
