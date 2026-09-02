import { create } from 'zustand'
import { api } from '../services/api'

export const useAuth = create((set) => ({
  token: localStorage.getItem('ai_teacher_token'),
  error: null,
  loading: false,

  register: async (email, password, fullName) => {
    set({ loading: true, error: null })
    try {
      const { access_token } = await api.register(email, password, fullName)
      localStorage.setItem('ai_teacher_token', access_token)
      set({ token: access_token, loading: false })
      return true
    } catch (e) {
      set({ error: e.message, loading: false })
      return false
    }
  },

  login: async (email, password) => {
    set({ loading: true, error: null })
    try {
      const { access_token } = await api.login(email, password)
      localStorage.setItem('ai_teacher_token', access_token)
      set({ token: access_token, loading: false })
      return true
    } catch (e) {
      set({ error: e.message, loading: false })
      return false
    }
  },

  logout: () => {
    localStorage.removeItem('ai_teacher_token')
    set({ token: null })
  },
}))
