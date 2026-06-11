<script setup>
import { computed, nextTick, onActivated, onBeforeUnmount, onMounted, ref } from 'vue'
import { initOpenAvatarConfig } from '../services/openAvatarClient'
import {
  closeAvatarWebRtc,
  createLocalStream,
  playRemoteVideo,
  replaceInputAudioTrack,
  setupAvatarWebRtc,
} from '../utils/avatarWebRtc'

const remoteVideo = ref(null)
const messagesContainer = ref(null)
const voiceEnabled = ref(false)
const input = ref('')
const status = ref('idle')
const error = ref('')
const messages = ref([])
const loadingSeconds = ref(0)
const waitingReply = ref(false)

let localStream = null
let peerConnection = null
let dataChannel = null
let loadingTimer = null
const activeStreamMessageIds = {
  user: '',
  avatar: '',
}

const connected = computed(() => status.value === 'connected')
const showLoading = computed(() => status.value === 'connecting' || Boolean(error.value))
const statusText = computed(() => {
  if (error.value) return error.value
  if (status.value === 'connecting') return `数字人正在初始化，已等待 ${loadingSeconds.value} 秒...`
  if (waitingReply.value) return '问题已发送，正在等待数字人回复...'
  if (voiceEnabled.value) return '语音模式已开启，可以直接说话'
  return '文字输入模式'
})

const startLoadingTimer = () => {
  window.clearInterval(loadingTimer)
  loadingSeconds.value = 0
  loadingTimer = window.setInterval(() => {
    loadingSeconds.value += 1
  }, 1000)
}

const stopLoadingTimer = () => {
  window.clearInterval(loadingTimer)
  loadingTimer = null
}

const scrollMessagesToBottom = () => {
  nextTick(() => {
    const target = messagesContainer.value
    if (target) target.scrollTop = target.scrollHeight
  })
}

const appendMessage = (role, text) => {
  if (!text) return
  const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`
  messages.value.push({
    id,
    role,
    text,
  })
  if (messages.value.length > 8) {
    messages.value = messages.value.slice(-8)
  }
  scrollMessagesToBottom()
  return id
}

const appendToMessage = (id, chunk) => {
  const target = messages.value.find((message) => message.id === id)
  if (target) {
    target.text += chunk
    scrollMessagesToBottom()
  }
}

const appendOrUpdateStreamMessage = (role, chunk) => {
  if (!chunk) return

  const activeId = activeStreamMessageIds[role]
  if (activeId) {
    appendToMessage(activeId, chunk)
    return
  }

  activeStreamMessageIds[role] = appendMessage(role, chunk) || ''
}

const finishStreamMessages = () => {
  activeStreamMessageIds.user = ''
  activeStreamMessageIds.avatar = ''
}

const resumeRemoteVideo = async () => {
  await nextTick()

  const video = remoteVideo.value
  if (!video) return

  if (peerConnection && ['closed', 'failed'].includes(peerConnection.connectionState)) {
    await connect()
    return
  }

  await playRemoteVideo(video, { unmuteAfterPlay: !video.muted })
}

const bindDataChannel = () => {
  dataChannel?.addEventListener('message', (event) => {
    let data
    try {
      data = JSON.parse(event.data)
    } catch {
      return
    }

    const name = data?.header?.name
    const text = data?.payload?.text
    if (name === 'EchoHumanText' || name === 'EchoAvatarText') {
      if (name === 'EchoAvatarText') waitingReply.value = false
      appendOrUpdateStreamMessage(name === 'EchoHumanText' ? 'user' : 'avatar', text || '')
    } else if (name === 'EndSpeech' || name === 'InterruptNotification') {
      waitingReply.value = false
      finishStreamMessages()
    } else if (name === 'ChatSignal' && data?.payload?.type === 'stream_end') {
      waitingReply.value = false
      finishStreamMessages()
    }
  })
}

const connect = async () => {
  if (status.value === 'connecting') return
  error.value = ''
  waitingReply.value = false
  finishStreamMessages()

  if (peerConnection) {
    closeAvatarWebRtc({ peerConnection, stream: localStream })
    peerConnection = null
    dataChannel = null
    localStream = null
  }

  try {
    status.value = 'connecting'
    startLoadingTimer()
    const config = await initOpenAvatarConfig()
    localStream = await createLocalStream({ useAsr: false })
    const connection = await setupAvatarWebRtc({
      stream: localStream,
      remoteVideo: remoteVideo.value,
      rtcConfiguration: config.rtc_configuration,
    })
    peerConnection = connection.peerConnection
    dataChannel = connection.dataChannel
    bindDataChannel()
    status.value = 'connected'
  } catch (err) {
    status.value = 'idle'
    error.value = err?.message || '数字人连接失败'
  } finally {
    stopLoadingTimer()
  }
}

const setVoiceEnabled = async (nextValue) => {
  if (voiceEnabled.value === nextValue) return
  error.value = ''

  if (!connected.value) {
    await connect()
  }

  if (!connected.value) return

  try {
    await replaceInputAudioTrack({
      peerConnection,
      stream: localStream,
      useAsr: nextValue,
    })
    voiceEnabled.value = nextValue
  } catch (err) {
    voiceEnabled.value = false
    error.value = err?.message || '麦克风切换失败'
  }
}

const sendText = () => {
  const text = input.value.trim()
  if (!text) return

  if (!dataChannel || dataChannel.readyState !== 'open') {
    error.value = '数字人还没有连接好，请稍等。'
    return
  }

  const requestId = `${Date.now()}-${Math.random().toString(16).slice(2)}`
  dataChannel.send(
    JSON.stringify({
      header: {
        name: 'SendHumanText',
        request_id: requestId,
      },
      payload: {
        request_id: requestId,
        stream_key: requestId,
        mode: 'full_text',
        text,
        end_of_speech: true,
      },
    })
  )
  waitingReply.value = true
  input.value = ''
  finishStreamMessages()
}

onMounted(() => {
  connect()
})

onActivated(() => {
  resumeRemoteVideo()
  scrollMessagesToBottom()
})

onBeforeUnmount(() => {
  stopLoadingTimer()
  finishStreamMessages()
  closeAvatarWebRtc({ peerConnection, stream: localStream })
})
</script>

<template>
  <section class="avatar-stage">
    <div class="avatar-stage__video-card">
      <video ref="remoteVideo" class="avatar-stage__video" autoplay playsinline />
      <div v-if="showLoading" class="avatar-stage__status">
        <span class="avatar-stage__loader" />
        <strong>{{ statusText }}</strong>
        <p>数字人模型启动比较慢，请保持页面打开。</p>
        <button v-if="error" type="button" @click="connect">重新连接</button>
      </div>

      <div class="avatar-live-layer">
        <div class="avatar-live-chat">
          <div ref="messagesContainer" class="avatar-live-chat__messages">
            <p v-if="!messages.length" class="avatar-live-chat__empty">
              可以先问：适合亲子游的路线怎么安排？
            </p>
            <p
              v-for="message in messages"
              :key="message.id"
              :class="`avatar-live-chat__message avatar-live-chat__message--${message.role}`"
            >
              <strong>{{ message.role === 'user' ? '游客' : '数字人' }}</strong>
              <span>{{ message.text }}</span>
            </p>
          </div>

          <form class="avatar-live-chat__form" @submit.prevent="sendText">
            <input v-model="input" type="text" autocomplete="off" placeholder="说点什么..." />
            <button type="submit" :disabled="!input.trim() || !connected">发送</button>
          </form>
        </div>

        <button
          class="avatar-asr-button"
          :class="{ 'avatar-asr-button--on': voiceEnabled }"
          type="button"
          :aria-pressed="voiceEnabled"
          :title="voiceEnabled ? '关闭语音输入' : '开启语音输入'"
          @click="setVoiceEnabled(!voiceEnabled)"
        >
          <span class="avatar-asr-button__orb">
            <i class="avatar-asr-button__wave avatar-asr-button__wave--one" />
            <i class="avatar-asr-button__wave avatar-asr-button__wave--two" />
            <i class="avatar-asr-button__dot" />
          </span>
          <em>{{ voiceEnabled ? 'ASR 开' : 'ASR 关' }}</em>
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.avatar-stage {
  position: relative;
  display: grid;
  height: calc(100vh - 92px);
  min-height: calc(100vh - 92px);
  padding: 0;
  overflow: hidden;
  color: #fff;
}

.avatar-stage__video-card {
  position: relative;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: #0b0f0d;
}

.avatar-stage__video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
  background: #0b0f0d;
}

.avatar-stage__status {
  position: absolute;
  inset: 0;
  z-index: 4;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 12px;
  padding: 24px;
  color: #43584c;
  text-align: center;
  background: rgba(248, 250, 251, 0.86);
  backdrop-filter: blur(10px);
}

.avatar-stage__status strong {
  font-size: 17px;
}

.avatar-stage__status p {
  margin: 0;
  color: var(--text-muted);
  font-size: 13px;
}

.avatar-stage__status button {
  border: 0;
  border-radius: 999px;
  padding: 7px 12px;
  color: #fff;
  background: #244f3a;
  font-weight: 800;
}

.avatar-stage__loader {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #2d704b;
  animation: blink 1.1s ease-in-out infinite;
}

.avatar-live-layer {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  padding: 16px var(--shell-padding) calc(env(safe-area-inset-bottom, 0px) + 42px);
  pointer-events: none;
}

.avatar-live-chat {
  position: relative;
  z-index: 1;
  display: grid;
  width: min(100%, 620px);
  min-width: 0;
  gap: 10px;
  pointer-events: auto;
}

.avatar-live-chat__messages {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  max-height: min(34vh, 260px);
  gap: 7px;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding-right: 4px;
  color: rgba(255, 255, 255, 0.92);
  font-size: 15px;
  line-height: 1.45;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.42);
}

.avatar-live-chat__messages::-webkit-scrollbar {
  width: 4px;
}

.avatar-live-chat__messages::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(170, 226, 213, 0.5);
}

.avatar-live-chat__messages p {
  margin: 0;
}

.avatar-live-chat__empty,
.avatar-live-chat__message {
  width: fit-content;
  max-width: 100%;
  padding: 8px 11px;
  border: 1px solid rgba(215, 244, 236, 0.16);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.24);
}

.avatar-live-chat__message strong {
  margin-right: 7px;
  color: #b9f2df;
  font-weight: 800;
}

.avatar-live-chat__message--avatar strong {
  color: #8ce6d1;
}

.avatar-live-chat__form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
}

.avatar-live-chat__form input {
  min-width: 0;
  height: 42px;
  padding: 0 14px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 999px;
  outline: none;
  color: #fff;
  background: rgba(0, 0, 0, 0.28);
  font: inherit;
}

.avatar-live-chat__form input::placeholder {
  color: rgba(221, 247, 239, 0.68);
}

.avatar-live-chat__form button {
  height: 42px;
  padding: 0 16px;
  border: 0;
  border-radius: 999px;
  color: #f7fffb;
  background: #2d7078;
  font-weight: 800;
}

.avatar-live-chat__form button:disabled {
  cursor: not-allowed;
  opacity: 0.56;
}

.avatar-asr-button {
  position: relative;
  display: grid;
  width: 66px;
  min-height: 78px;
  flex: 0 0 auto;
  gap: 5px;
  place-items: center;
  border: 0;
  color: rgba(255, 255, 255, 0.82);
  background: transparent;
  pointer-events: auto;
}

.avatar-asr-button__orb {
  position: relative;
  display: grid;
  width: 52px;
  height: 52px;
  place-items: center;
  border-radius: 50%;
  border: 1px solid rgba(215, 244, 236, 0.2);
  background: rgba(0, 0, 0, 0.28);
}

.avatar-asr-button__dot {
  position: relative;
  z-index: 2;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(221, 247, 239, 0.82);
}

.avatar-asr-button__wave {
  position: absolute;
  inset: 7px;
  border: 1px solid transparent;
  border-radius: 50%;
}

.avatar-asr-button--on {
  color: #fff;
}

.avatar-asr-button--on .avatar-asr-button__orb {
  border-color: rgba(207, 250, 235, 0.5);
  background: #2d7078;
}

.avatar-asr-button--on .avatar-asr-button__dot {
  background: #f7fffb;
}

.avatar-asr-button--on .avatar-asr-button__wave {
  border-color: rgba(207, 250, 235, 0.68);
  animation: wave 1.8s ease-out infinite;
}

.avatar-asr-button--on .avatar-asr-button__wave--two {
  animation-delay: 0.48s;
}

.avatar-asr-button em {
  font-style: normal;
  font-size: 12px;
  font-weight: 800;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.38);
}

@keyframes wave {
  0% {
    opacity: 0.72;
    transform: scale(0.72);
  }

  100% {
    opacity: 0;
    transform: scale(1.9);
  }
}

@keyframes blink {
  0%,
  100% {
    opacity: 0.3;
    transform: scale(0.82);
  }

  50% {
    opacity: 1;
    transform: scale(1);
  }
}

@media (max-width: 720px) {
  .avatar-live-layer {
    padding: 12px 12px calc(env(safe-area-inset-bottom, 0px) + 38px);
  }

  .avatar-live-chat__messages {
    max-height: min(30vh, 220px);
    font-size: 14px;
  }

  .avatar-live-chat__form button {
    padding: 0 13px;
  }
}
</style>
