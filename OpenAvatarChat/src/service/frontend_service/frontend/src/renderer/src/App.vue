<script setup lang="ts">
import { ConfigProvider } from 'ant-design-vue'
import { storeToRefs } from 'pinia'

import WebcamPermission from '@/components/WebcamPermission.vue'
import { antdLocale, locale } from '@/langs'
import VideoChat from '@/views/VideoChat/index.vue'
import WSVideoChat from './views/WSVideoChat/index.vue'
import { useAppStore } from './store/app'
import { useMediaStore } from './store/media'
import isElectron from './utils/isElectron'

const query = new URLSearchParams(window.location.search)
const embedded = query.get('embed') === '1' || query.get('compact') === '1'
const hideCamera = query.get('hide_camera') !== '0'
const asrEnabled = embedded ? query.get('asr') === '1' : true

const appState = useAppStore()
const mediaState = useMediaStore()
const { chatMode } = storeToRefs(appState)

mediaState.setInputMode({
  hideCameraInput: embedded && hideCamera,
  asrEnabled,
})

if (embedded) {
  appState.toolsVisible = false
  appState.inputVisible = true
}

appState.init()
</script>

<template>
  <ConfigProvider :locale="antdLocale[locale]">
    <div
      class="wrap"
      :class="{ 'wrap--embedded': embedded }"
      :style="{
        backgroundImage: isElectron || embedded ? 'none' : undefined,
      }"
    >
      <WebcamPermission
        v-if="!mediaState.webcamAccessed"
        :auto-access="embedded || isElectron"
      />
      <template v-if="chatMode === 'ws'">
        <WSVideoChat />
      </template>
      <template v-else>
        <VideoChat />
      </template>
    </div>
  </ConfigProvider>
</template>

<style lang="less" scoped>
.wrap {
  height: calc(max(80vh, 100%));
  background-image: url(@/assets/background.png);
  background-size: 100% 100%;
  background-repeat: no-repeat;
  position: relative;

  *::-webkit-scrollbar {
    display: none;
  }
}

.wrap--embedded {
  width: 100vw;
  height: 100vh;
  background: transparent;
}
</style>
