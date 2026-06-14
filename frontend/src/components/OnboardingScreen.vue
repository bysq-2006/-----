<script setup>
const emit = defineEmits(['login', 'register', 'enter'])
</script>

<template>
  <section class="onboarding-screen">
    <div class="onboarding-screen__stage" aria-hidden="true">
      <div class="onboarding-bubbles">
        <span class="onboarding-bubble onboarding-bubble--large"></span>
        <span class="onboarding-bubble onboarding-bubble--warm"></span>
        <span class="onboarding-bubble onboarding-bubble--small"></span>
        <span class="onboarding-bubble onboarding-bubble--tiny"></span>
      </div>
    </div>

    <div class="onboarding-screen__copy">
      <span>AI 景区导览</span>
      <h1>让数字人先认识你的旅行方式</h1>
      <p>登录后可保存偏好、收藏景点和对话历史；也可以先进入应用看看。</p>
    </div>

    <div class="onboarding-screen__actions">
      <button class="onboarding-action onboarding-action--primary" type="button" @click="emit('login')">登录</button>
      <button class="onboarding-action" type="button" @click="emit('register')">注册</button>
      <button class="onboarding-action onboarding-action--ghost" type="button" @click="emit('enter')">先逛逛</button>
    </div>
  </section>
</template>
