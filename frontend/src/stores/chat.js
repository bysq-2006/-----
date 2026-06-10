import { defineStore } from 'pinia'
import { sendChatCompletion } from '../services/chat'
import { useAuthStore } from './auth'

const MAX_CONTEXT_MESSAGES = 100

const makeMessage = (role, content) => ({
  id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
  role,
  content,
})

const assistantContent = (data) => data?.choices?.[0]?.message?.content?.trim() || ''

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [],
    loading: false,
    error: '',
  }),
  getters: {
    contextMessages: (state) =>
      state.messages.slice(-MAX_CONTEXT_MESSAGES).map(({ role, content }) => ({
        role,
        content,
      })),
  },
  actions: {
    clear() {
      this.messages = []
      this.error = ''
    },
    async send(content) {
      const text = content.trim()
      if (!text || this.loading) return

      const authStore = useAuthStore()
      if (!authStore.token) {
        this.error = '请先登录后再和数字人对话。'
        return
      }

      const userMessage = makeMessage('user', text)
      this.messages.push(userMessage)
      this.loading = true
      this.error = ''

      try {
        const data = await sendChatCompletion({
          token: authStore.token,
          messages: this.contextMessages,
        })
        this.messages.push(makeMessage('assistant', assistantContent(data) || '我暂时没有生成回复。'))
      } catch (error) {
        this.error = error.message || '发送失败，请稍后再试。'
        this.messages.push(makeMessage('assistant', '这次请求失败了，可以稍后再试一次。'))
      } finally {
        this.loading = false
      }
    },
  },
})
