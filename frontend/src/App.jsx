import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './store/auth'
import Landing from './pages/Landing'
import Auth from './pages/Auth'
import Dashboard from './pages/Dashboard'
import SessionPrep from './pages/SessionPrep'
import LessonPlayer from './pages/LessonPlayer'
import Report from './pages/Report'
import Progress from './pages/Progress'

function Protected({ children }) {
  const { token } = useAuth()
  return token ? children : <Navigate to="/auth" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/auth" element={<Auth />} />
      <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
      <Route path="/session/:sessionId" element={<Protected><SessionPrep /></Protected>} />
      <Route path="/lesson/:lessonId" element={<Protected><LessonPlayer /></Protected>} />
      <Route path="/lesson/:lessonId/report" element={<Protected><Report /></Protected>} />
      <Route path="/progress" element={<Protected><Progress /></Protected>} />
    </Routes>
  )
}
