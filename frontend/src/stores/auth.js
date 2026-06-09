import { defineStore } from 'pinia'
import { fetchCurrentUser, loginUser, registerUser } from '../services/auth'

const TOKEN_KEY = 'scenic_avatar_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY),
    user: null,
    loading: false,
    error: '',
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token && state.user),
    displayName: (state) => state.user?.display_name || state.user?.email || '游客',
  },
  actions: {
    setToken(token) {
      this.token = token
      localStorage.setItem(TOKEN_KEY, token)
    },
    async loadUser() {
      if (!this.token) return

      try {
        this.user = await fetchCurrentUser(this.token)
      } catch {
        this.logout()
      }
    },
    async login(payload) {
      this.loading = true
      this.error = ''

      try {
        const data = await loginUser(payload)
        this.setToken(data.access_token)
        await this.loadUser()
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async register(payload) {
      this.loading = true
      this.error = ''

      try {
        await registerUser(payload)
        const data = await loginUser(payload)
        this.setToken(data.access_token)
        await this.loadUser()
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    logout() {
      this.token = null
      this.user = null
      this.error = ''
      localStorage.removeItem(TOKEN_KEY)
    },
  },
})
