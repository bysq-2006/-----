<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const authStore = useAuthStore()
const inputText = ref('你好')
const answer = ref('')
const errorMessage = ref('')
const loading = ref(false)
const requestMs = ref(null)
const firstContentMs = ref(null)
const finishMs = ref(null)

let abortController = null

const parseDeltaContent = (line) => {
  if (!line.startsWith('data:')) return ''
  const data = line.slice(5).trim()
  if (!data || data === '[DONE]') return ''

  try {
    const delta = JSON.parse(data)?.choices?.[0]?.delta
    return delta?.content || ''
  } catch {
    return ''
  }
}

const sendDirectChat = async () => {
  const message = inputText.value.trim()
  if (!message || loading.value) return

  if (!authStore.token) {
    errorMessage.value = '请先登录后再测试。'
    return
  }

  abortController?.abort()
  abortController = new AbortController()
  answer.value = ''
  errorMessage.value = ''
  requestMs.value = null
  firstContentMs.value = null
  finishMs.value = null
  loading.value = true

  const startedAt = performance.now()

  try {
    const response = await fetch(`${API_BASE_URL}/v1/chat/completions`, {
      method: 'POST',
      signal: abortController.signal,
      headers: {
        Authorization: `Bearer ${authStore.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        stream: true,
        messages: [{ role: 'user', content: message }],
      }),
    })

    requestMs.value = Math.round(performance.now() - startedAt)

    if (!response.ok) {
      const text = await response.text()
      throw new Error(text || `请求失败：${response.status}`)
    }

    if (!response.body) {
      throw new Error('浏览器没有拿到流式响应。')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split(/\r?\n/)
      buffer = lines.pop() || ''

      for (const line of lines) {
        const content = parseDeltaContent(line.trim())
        if (!content) continue
        if (firstContentMs.value === null) {
          firstContentMs.value = Math.round(performance.now() - startedAt)
        }
        answer.value += content
      }
    }

    finishMs.value = Math.round(performance.now() - startedAt)
  } catch (error) {
    if (error.name !== 'AbortError') {
      errorMessage.value = error.message || '请求失败'
    }
  } finally {
    loading.value = false
  }
}

const stopDirectChat = () => {
  abortController?.abort()
  loading.value = false
}
</script>

<template>
  <section class="map-test">
    <div class="map-test__panel">
      <div class="map-test__header">
        <p>后端直连测试</p>
        <h1>流式聊天延迟</h1>
      </div>

      <form class="map-test__form" @submit.prevent="sendDirectChat">
        <textarea
          v-model="inputText"
          rows="4"
          placeholder="输入一句话，直接请求你的 backend /v1/chat/completions"
        ></textarea>

        <div class="map-test__actions">
          <button type="submit" :disabled="loading || !inputText.trim()">
            {{ loading ? '请求中...' : '发送测试' }}
          </button>
          <button v-if="loading" type="button" class="map-test__ghost" @click="stopDirectChat">
            停止
          </button>
        </div>
      </form>

      <div class="map-test__metrics">
        <span>响应头：{{ requestMs === null ? '-' : `${requestMs}ms` }}</span>
        <span>首字：{{ firstContentMs === null ? '-' : `${firstContentMs}ms` }}</span>
        <span>完成：{{ finishMs === null ? '-' : `${finishMs}ms` }}</span>
      </div>

      <p v-if="errorMessage" class="map-test__error">{{ errorMessage }}</p>
      <div class="map-test__answer">
        {{ answer || '回复会以流式方式显示在这里。' }}
      </div>
    </div>
  </section>
</template>

<style scoped>
.map-test {
  min-height: calc(100vh - 72px);
  padding: 24px;
  background: #f4fbf7;
  display: grid;
  place-items: start center;
}

.map-test__panel {
  width: min(720px, 100%);
  padding: 20px;
  border: 1px solid rgba(45, 135, 98, 0.18);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
}

.map-test__header p {
  margin: 0 0 6px;
  color: #2d8762;
  font-size: 13px;
}

.map-test__header h1 {
  margin: 0 0 18px;
  color: #18372b;
  font-size: 24px;
}

.map-test__form {
  display: grid;
  gap: 12px;
}

.map-test__form textarea {
  width: 100%;
  resize: vertical;
  border: 1px solid rgba(45, 135, 98, 0.24);
  border-radius: 8px;
  padding: 12px;
  font: inherit;
  color: #18372b;
  background: #fff;
}

.map-test__form textarea:focus {
  outline: 2px solid rgba(45, 135, 98, 0.18);
  border-color: #2d8762;
}

.map-test__actions {
  display: flex;
  gap: 10px;
}

.map-test__actions button {
  border: 0;
  border-radius: 8px;
  padding: 10px 16px;
  color: #fff;
  background: #2d8762;
  font: inherit;
  cursor: pointer;
}

.map-test__actions button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.map-test__actions .map-test__ghost {
  color: #2d8762;
  background: rgba(45, 135, 98, 0.1);
}

.map-test__metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 16px 0;
}

.map-test__metrics span {
  border-radius: 999px;
  padding: 6px 10px;
  color: #245d46;
  background: rgba(45, 135, 98, 0.1);
  font-size: 13px;
}

.map-test__error {
  margin: 0 0 12px;
  color: #b42318;
}

.map-test__answer {
  min-height: 160px;
  white-space: pre-wrap;
  line-height: 1.7;
  color: #1b3329;
  border-top: 1px solid rgba(45, 135, 98, 0.14);
  padding-top: 14px;
}
</style>
