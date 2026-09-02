// Relative by default: works unmodified through both the Vite dev proxy
// (vite.config.js) and the nginx proxy in the Docker deployment (frontend
// and backend share an origin from the browser's point of view in both
// cases). Only needs overriding if the frontend is deployed on a separate
// origin from the backend (e.g. static hosting + a separately-hosted API) —
// set VITE_API_BASE_URL at build time in that case.
const BASE = import.meta.env.VITE_API_BASE_URL || '/api'

function authHeaders() {
  const token = localStorage.getItem('ai_teacher_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(path, { method = 'GET', body, isForm = false } = {}) {
  const headers = isForm ? { ...authHeaders() } : { 'Content-Type': 'application/json', ...authHeaders() }
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
  })
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const data = await res.json()
      detail = data.detail || detail
    } catch { /* non-JSON error body */ }
    throw new Error(detail)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  register: (email, password, full_name) => request('/auth/register', { method: 'POST', body: { email, password, full_name } }),
  login: (email, password) => request('/auth/login', { method: 'POST', body: { email, password } }),

  createSession: (payload) => request('/sessions', { method: 'POST', body: payload }),
  getSession: (id) => request(`/sessions/${id}`),

  uploadMaterial: (sessionId, file) => {
    const form = new FormData()
    form.append('file', file)
    return request(`/materials/upload?session_id=${sessionId}`, { method: 'POST', body: form, isForm: true })
  },
  getMaterial: (id) => request(`/materials/${id}`),
  listSessionMaterials: (sessionId) => request(`/materials/session/${sessionId}`),

  analyzeTopic: (topic) => request('/topics/analyze', { method: 'POST', body: { topic } }),

  planLesson: (sessionId) => request(`/sessions/${sessionId}/plan`, { method: 'POST' }),
  startLesson: (sessionId) => request(`/sessions/${sessionId}/start`, { method: 'POST' }),
  getLesson: (lessonId) => request(`/lessons/${lessonId}`),
  switchLessonLanguage: (lessonId, language) => request(`/lessons/${lessonId}/language`, { method: 'POST', body: { language } }),

  answerQuestion: (questionId, answer_text) => request(`/questions/${questionId}/answer`, { method: 'POST', body: { answer_text } }),

  generateVideo: (conceptId) => request(`/teaching/video/${conceptId}/generate`, { method: 'POST' }),
  getVideoStatus: (conceptId) => request(`/teaching/video/${conceptId}`),
  getVisual: (conceptId) => request(`/teaching/visual/${conceptId}`),

  generateAssessment: (lessonId) => request(`/assessment/generate/${lessonId}`, { method: 'POST' }),
  getAssessment: (lessonId) => request(`/assessment/${lessonId}`),

  getProgress: () => request('/progress'),

  createLearningPath: (subject) => request(`/learning-path?subject=${encodeURIComponent(subject)}`, { method: 'POST' }),
  getLearningPath: (id) => request(`/learning-path/${id}`),

  getProfile: () => request('/student/profile'),
  updateProfile: (payload) => request('/student/profile', { method: 'PUT', body: payload }),
}
