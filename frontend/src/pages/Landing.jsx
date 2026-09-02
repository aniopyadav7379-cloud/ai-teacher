import { Link } from 'react-router-dom'
import { Shell } from '../components/Shell'
import { AvatarStage } from '../features/avatar/AvatarStage'

const LOOP = [
  ['Understand', 'Reads what you know, your goal, and your pace before saying a word.'],
  ['Explain', 'Teaches the concept with an analogy and a worked example, grounded in your material when you have it.'],
  ['Question', 'Checks understanding with a real question, not a recap quiz.'],
  ['Adapt', 'Wrong answer? It finds the actual misconception and re-teaches it differently — not louder.'],
  ['Assess', 'Ends with a score, what you\u2019re strong at, and exactly what to revise next.'],
]

export default function Landing() {
  return (
    <Shell>
      <section className="grid md:grid-cols-2 gap-10 items-center py-8">
        <div>
          <h1 className="font-display text-4xl sm:text-5xl font-semibold leading-tight text-white">
            A teacher that notices<br />when you're stuck.
          </h1>
          <p className="mt-5 text-white/70 max-w-md leading-relaxed">
            Upload a textbook chapter or just name a topic. It plans a lesson for your level and
            time, teaches it out loud, and changes course the moment your answers show a gap —
            the way a good tutor would, not a quiz app.
          </p>
          <div className="mt-8 flex gap-4">
            <Link to="/auth" className="px-5 py-2.5 rounded-lg bg-cyan-500 text-navy-950 font-medium hover:bg-cyan-400 transition-colors">
              Start learning
            </Link>
            <Link to="/auth" className="px-5 py-2.5 rounded-lg border border-white/15 text-white/80 hover:border-white/30 transition-colors">
              Sign in
            </Link>
          </div>
        </div>
        <AvatarStage isSpeaking isListening={false} isLoading={false} mouthOpen={0.4} className="h-72" />
      </section>

      <section className="mt-16">
        <h2 className="font-display text-xl font-semibold text-white mb-6">How a lesson actually runs</h2>
        <div className="grid sm:grid-cols-5 gap-3">
          {LOOP.map(([title, desc], i) => (
            <div key={title} className="glass rounded-xl p-4">
              <div className="text-cyan-400 text-xs font-medium mb-2">{i + 1}</div>
              <div className="font-display font-medium text-white text-sm mb-1">{title}</div>
              <p className="text-white/60 text-xs leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>
    </Shell>
  )
}
