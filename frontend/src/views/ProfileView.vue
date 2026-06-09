<script setup>
import { ref } from 'vue'
import AuthModal from '../components/AuthModal.vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const showAuthModal = ref(false)
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
        <button class="profile-action profile-action--ghost" type="button" @click="authStore.logout">退出登录</button>
      </template>

      <template v-else>
        <p class="profile-panel__text">登录后可以保存收藏景点、讲解偏好和历史记录。</p>
        <button class="profile-action" type="button" @click="showAuthModal = true">登录 / 注册</button>
      </template>
    </div>

    <AuthModal v-if="showAuthModal" @close="showAuthModal = false" />
  </section>
</template>
