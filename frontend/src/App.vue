<script setup>
import { computed, onMounted, provide, ref, watch } from 'vue'
import AuthModal from './components/AuthModal.vue'
import OnboardingScreen from './components/OnboardingScreen.vue'
import PreferenceScreen from './components/PreferenceScreen.vue'
import TabBar from './components/TabBar.vue'
import { useAuthStore } from './stores/auth'
import {
  getPreferenceKey,
  hasStoredPreferences,
  preferenceTextFromValues,
  writeUserPreferenceText,
} from './utils/preferences'

const authStore = useAuthStore()
const INTRO_KEY = 'scenic_avatar_intro_seen'

const introSeen = ref(localStorage.getItem(INTRO_KEY) === '1')
const authMode = ref('')
const hasPreferences = ref(true)

const preferenceKey = computed(() => getPreferenceKey(authStore.user?.id))
const showIntro = computed(() => !introSeen.value && !authStore.token)
const showPreferences = computed(
  () => authStore.isLoggedIn && !authMode.value && !showIntro.value && !hasPreferences.value,
)
const showApp = computed(() => !showIntro.value && !authMode.value && !showPreferences.value)

const refreshPreferences = () => {
  hasPreferences.value = !authStore.user?.id || hasStoredPreferences(authStore.user.id)
}

const finishIntro = () => {
  introSeen.value = true
  localStorage.setItem(INTRO_KEY, '1')
}

const openAuth = (mode = 'login') => {
  finishIntro()
  authMode.value = mode
}

const closeAuth = () => {
  authMode.value = ''
  refreshPreferences()
}

const savePreferences = (items) => {
  writeUserPreferenceText(authStore.user?.id, preferenceTextFromValues(items))
  refreshPreferences()
}

provide('openAuth', openAuth)

onMounted(() => {
  authStore.loadUser()
})

watch(preferenceKey, refreshPreferences, { immediate: true })
</script>

<template>
  <div class="app-shell">
    <OnboardingScreen
      v-if="showIntro"
      @login="openAuth('login')"
      @register="openAuth('register')"
      @enter="finishIntro"
    />

    <AuthModal v-else-if="authMode" :initial-mode="authMode" @close="closeAuth" />

    <PreferenceScreen v-else-if="showPreferences" @save="savePreferences" />

    <main v-if="showApp" class="app-shell__page">
      <RouterView v-slot="{ Component, route }">
        <KeepAlive>
          <component :is="Component" v-if="route.meta.keepAlive" />
        </KeepAlive>
        <component :is="Component" v-if="!route.meta.keepAlive" />
      </RouterView>
    </main>
    <TabBar v-if="showApp" />
  </div>
</template>
