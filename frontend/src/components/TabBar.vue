<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const tabs = [
  {
    label: '数字人',
    path: '/avatar',
    icon: 'avatar',
  },
  {
    label: '地图',
    path: '/map',
    icon: 'map',
  },
  {
    label: '收藏',
    path: '/favorites',
    icon: 'bookmark',
  },
  {
    label: '我的',
    path: '/profile',
    icon: 'user',
  },
]

const activePath = computed(() => route.path)

const iconPaths = {
  avatar:
    'M12 3.75a5.25 5.25 0 0 0-5.25 5.25v2.25A2.25 2.25 0 0 0 4.5 13.5v1.5a2.25 2.25 0 0 0 2.25 2.25h.932a4.5 4.5 0 0 0 8.636 0h.932A2.25 2.25 0 0 0 19.5 15v-1.5a2.25 2.25 0 0 0-2.25-2.25V9A5.25 5.25 0 0 0 12 3.75z',
  map: 'M15.75 4.5 8.25 7.5 3 5.25v14.25l5.25 2.25 7.5-3 5.25 2.25V6.75zm0 0v14.25',
  bookmark:
    'M6 4.5h12a1.5 1.5 0 0 1 1.5 1.5V21L12 16.5 4.5 21V6A1.5 1.5 0 0 1 6 4.5z',
  user: 'M12 12a4.125 4.125 0 1 0 0-8.25 4.125 4.125 0 0 0 0 8.25M4.5 20.25a7.5 7.5 0 0 1 15 0',
}

const goTo = (path) => {
  if (path !== route.path) {
    router.push(path)
  }
}
</script>

<template>
  <nav class="tab-bar" aria-label="底部导航">
    <button
      v-for="tab in tabs"
      :key="tab.path"
      class="tab-bar__item"
      :class="{ 'tab-bar__item--active': activePath === tab.path }"
      type="button"
      @click="goTo(tab.path)"
    >
      <span class="tab-bar__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path :d="iconPaths[tab.icon]" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </span>
      <span class="tab-bar__label">{{ tab.label }}</span>
    </button>
  </nav>
</template>
