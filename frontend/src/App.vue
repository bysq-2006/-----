<script setup>
import { onMounted } from 'vue'
import TabBar from './components/TabBar.vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  authStore.loadUser()
})
</script>

<template>
  <div class="app-shell">
    <main class="app-shell__page">
      <RouterView v-slot="{ Component, route }">
        <KeepAlive>
          <component :is="Component" v-if="route.meta.keepAlive" />
        </KeepAlive>
        <component :is="Component" v-if="!route.meta.keepAlive" />
      </RouterView>
    </main>
    <TabBar />
  </div>
</template>
