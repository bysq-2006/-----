<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { preferenceOptions, readUserPreferenceText, writeUserPreferenceText } from '../utils/preferences'

const authStore = useAuthStore()
const openAuth = inject('openAuth')
const preferenceText = ref('')
const editingText = ref('')
const showPreferenceEditor = ref(false)
const saved = ref(false)

const preferenceSummary = computed(() => preferenceText.value.trim() || '暂未设置')

const selectedOptionValues = computed(() =>
  preferenceOptions
    .filter((option) => editingText.value.includes(option.title))
    .map((option) => option.value),
)

const loadPreferences = () => {
  preferenceText.value = readUserPreferenceText(authStore.user?.id)
  saved.value = false
}

const openPreferenceEditor = () => {
  editingText.value = preferenceText.value
  saved.value = false
  showPreferenceEditor.value = true
}

const closePreferenceEditor = () => {
  showPreferenceEditor.value = false
}

const toggleOption = (option) => {
  saved.value = false
  const parts = editingText.value
    .split(/[、，,\n]/)
    .map((item) => item.trim())
    .filter(Boolean)

  editingText.value = parts.includes(option.title)
    ? parts.filter((item) => item !== option.title).join('、')
    : [...parts, option.title].join('、')
}

const savePreferences = () => {
  preferenceText.value = editingText.value.trim()
  writeUserPreferenceText(authStore.user?.id, preferenceText.value)
  saved.value = true
  showPreferenceEditor.value = false
}

watch(() => authStore.user?.id, loadPreferences, { immediate: true })
</script>

<template>
  <section class="screen profile-screen">
    <header class="profile-hero">
      <div>
        <span class="profile-hero__eyebrow">个人中心</span>
        <h1>{{ authStore.isLoggedIn ? authStore.displayName : '游客' }}</h1>
      </div>
      <div class="profile-hero__avatar">
        {{ authStore.displayName.slice(0, 1).toUpperCase() }}
      </div>
    </header>

    <div class="profile-panel">
      <template v-if="authStore.isLoggedIn">
        <div class="profile-row">
          <span>邮箱</span>
          <strong>{{ authStore.user.email }}</strong>
        </div>
        <div class="profile-row">
          <span>用户 ID</span>
          <strong>{{ authStore.user.id }}</strong>
        </div>

        <section class="profile-preferences">
          <div class="profile-preferences__head">
            <span>当前讲解偏好</span>
            <strong>{{ preferenceSummary }}</strong>
          </div>
          <button class="profile-action" type="button" @click="openPreferenceEditor">编辑偏好</button>
        </section>

        <button class="profile-action profile-action--ghost" type="button" @click="authStore.logout">退出登录</button>
      </template>

      <template v-else>
        <p class="profile-panel__text">登录后可以保存收藏景点、讲解偏好和历史记录。</p>
        <button class="profile-action" type="button" @click="openAuth?.('login')">登录 / 注册</button>
      </template>
    </div>

    <Teleport to="body">
      <div v-if="showPreferenceEditor" class="preference-editor" role="dialog" aria-modal="true">
        <button class="preference-editor__backdrop" type="button" aria-label="关闭偏好编辑" @click="closePreferenceEditor">
        </button>

        <section class="preference-editor__panel">
          <div class="preference-editor__head">
            <span>个人喜好</span>
            <button type="button" aria-label="关闭" @click="closePreferenceEditor">×</button>
          </div>

          <label class="preference-editor__field">
            <span>自由描述</span>
            <textarea
              v-model.trim="editingText"
              rows="4"
              placeholder="例如：我喜欢历史文化和自然风光，希望讲解简洁一点，也帮我规划少绕路的路线。"
            ></textarea>
          </label>

          <div class="profile-preference-grid">
            <button
              v-for="option in preferenceOptions"
              :key="option.value"
              class="preference-card"
              :class="{ 'preference-card--active': selectedOptionValues.includes(option.value) }"
              type="button"
              @click="toggleOption(option)"
            >
              <strong>{{ option.title }}</strong>
              <span>{{ option.text }}</span>
            </button>
          </div>

          <button class="profile-action" type="button" @click="savePreferences">
            {{ saved ? '已保存' : '保存偏好' }}
          </button>
        </section>
      </div>
    </Teleport>
  </section>
</template>
