<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import TabBar from './components/TabBar.vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
const route = useRoute()

onMounted(() => {
  authStore.loadUser()
})
</script>

<template>
  <div class="app-shell">
    <main class="app-shell__page">
      <RouterView />
    </main>
    <TabBar v-if="route.path !== '/avatar'" />
  </div>
</template>
