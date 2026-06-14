<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth'

const props = defineProps({
  initialMode: {
    type: String,
    default: 'login',
  },
})

const emit = defineEmits(['close'])
const authStore = useAuthStore()
const mode = ref(props.initialMode)
const message = ref('')
const form = reactive({
  email: '',
  password: '',
  displayName: '',
})

const isRegister = computed(() => mode.value === 'register')
const title = computed(() => (isRegister.value ? '创建你的导览账号' : '欢迎回来'))
const subtitle = computed(() =>
  isRegister.value ? '保存讲解偏好、收藏景点和历史记录。' : '继续你的景区数字人导览体验。',
)
const passwordAutocomplete = computed(() => (isRegister.value ? 'new-password' : 'current-password'))

watch(
  () => props.initialMode,
  (value) => {
    mode.value = value
  },
)

const switchMode = () => {
  mode.value = isRegister.value ? 'login' : 'register'
  message.value = ''
}

const validateForm = () => {
  if (!form.email) return '请输入邮箱。'
  if (!form.email.includes('@')) return '邮箱格式不太对，请检查一下。'
  if (!form.password) return '请输入密码。'
  if (form.password.length < 8) return '密码至少需要 8 位。'
  return ''
}

const submit = async () => {
  message.value = validateForm()
  if (message.value) return

  try {
    if (isRegister.value) {
      await authStore.register(form)
    } else {
      await authStore.login(form)
    }
    emit('close')
  } catch (error) {
    message.value = error.message || '操作失败，请稍后再试。'
  }
}
</script>

<template>
  <section class="auth-screen">
    <button class="auth-screen__back" type="button" aria-label="返回" @click="emit('close')">←</button>

    <div class="auth-screen__visual" aria-hidden="true">
      <span></span>
      <span></span>
      <span></span>
    </div>

    <form class="auth-screen__form" @submit.prevent="submit">
      <div class="auth-card__head">
        <span class="auth-card__mark"></span>
        <h2>{{ title }}</h2>
        <p>{{ subtitle }}</p>
      </div>

      <label class="auth-field" v-if="isRegister">
        <span>昵称</span>
        <input v-model.trim="form.displayName" type="text" maxlength="30" placeholder="想让数字人怎么称呼你" />
      </label>

      <label class="auth-field">
        <span>邮箱</span>
        <input v-model.trim="form.email" type="email" autocomplete="email" placeholder="you@example.com" />
      </label>

      <label class="auth-field">
        <span>密码</span>
        <input
          v-model="form.password"
          type="password"
          :autocomplete="passwordAutocomplete"
          placeholder="至少 8 位密码"
        />
      </label>

      <p v-if="message" class="auth-card__error">{{ message }}</p>

      <button class="auth-card__submit" type="submit" :disabled="authStore.loading">
        {{ authStore.loading ? '处理中...' : isRegister ? '注册并登录' : '登录' }}
      </button>

      <button class="auth-card__switch" type="button" :disabled="authStore.loading" @click="switchMode">
        {{ isRegister ? '已有账号，去登录' : '还没有账号，去注册' }}
      </button>
    </form>
  </section>
</template>
