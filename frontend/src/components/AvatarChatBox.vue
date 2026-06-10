<script setup>
import { computed, ref } from 'vue'

const avatarBaseUrl =
  import.meta.env.VITE_AVATAR_CHAT_URL || 'https://localhost:8282/ui/index.html'

const interactionMode = ref('text')

const avatarUrl = computed(() => {
  const url = new URL(avatarBaseUrl, window.location.href)
  url.searchParams.set('embed', '1')
  url.searchParams.set('hide_camera', '1')
  url.searchParams.set('compact', '1')
  url.searchParams.set('asr', interactionMode.value === 'asr' ? '1' : '0')
  return url.toString()
})
</script>

<template>
  <section class="avatar-stage">
    <header class="avatar-stage__toolbar">
      <div>
        <p>景区数字人</p>
        <h1>智能讲解与互动咨询</h1>
      </div>

      <div class="avatar-stage__modes" aria-label="交互方式">
        <button
          type="button"
          :class="{ active: interactionMode === 'text' }"
          @click="interactionMode = 'text'"
        >
          文字提问
        </button>
        <button
          type="button"
          :class="{ active: interactionMode === 'asr' }"
          @click="interactionMode = 'asr'"
        >
          语音 ASR
        </button>
      </div>
    </header>

    <div class="avatar-stage__viewport">
      <iframe
        class="avatar-stage__iframe"
        :src="avatarUrl"
        title="景区数字人"
        allow="microphone; camera; autoplay; fullscreen; clipboard-read; clipboard-write"
      />
    </div>
  </section>
</template>

<style scoped>
.avatar-stage {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-height: 100vh;
  padding: 14px;
  color: #1e2b24;
  background:
    radial-gradient(circle at 18% 10%, rgba(178, 214, 181, 0.34), transparent 30%),
    linear-gradient(180deg, #f7f6ef 0%, #eef3eb 100%);
}

.avatar-stage__toolbar {
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 12px;
  padding: 12px 14px;
  border: 1px solid rgba(34, 64, 49, 0.1);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.68);
  box-shadow: 0 14px 42px rgba(47, 68, 56, 0.09);
  backdrop-filter: blur(16px);
}

.avatar-stage__toolbar p,
.avatar-stage__toolbar h1 {
  margin: 0;
}

.avatar-stage__toolbar p {
  color: #6e7f70;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.avatar-stage__toolbar h1 {
  margin-top: 2px;
  font-size: 20px;
  line-height: 1.2;
}

.avatar-stage__modes {
  display: inline-flex;
  gap: 6px;
  padding: 5px;
  border-radius: 999px;
  background: rgba(31, 53, 39, 0.08);
}

.avatar-stage__modes button {
  min-width: 88px;
  padding: 9px 12px;
  border: 0;
  border-radius: 999px;
  color: #526457;
  background: transparent;
  font-size: 14px;
  font-weight: 800;
}

.avatar-stage__modes button.active {
  color: #fff;
  background: #254f3a;
  box-shadow: 0 8px 18px rgba(37, 79, 58, 0.22);
}

.avatar-stage__viewport {
  min-height: 0;
  overflow: hidden;
  border: 1px solid rgba(34, 64, 49, 0.12);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.45);
  box-shadow: 0 24px 70px rgba(45, 62, 51, 0.14);
}

.avatar-stage__iframe {
  display: block;
  width: 100%;
  height: 100%;
  min-height: calc(100vh - 112px);
  border: 0;
  background: transparent;
}

@media (max-width: 720px) {
  .avatar-stage {
    padding: 10px;
  }

  .avatar-stage__toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .avatar-stage__modes {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
