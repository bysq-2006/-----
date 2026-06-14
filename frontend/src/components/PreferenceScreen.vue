<script setup>
import { ref } from 'vue'
import { preferenceOptions } from '../utils/preferences'

const emit = defineEmits(['save'])

const selected = ref([])

const toggle = (value) => {
  selected.value = selected.value.includes(value)
    ? selected.value.filter((item) => item !== value)
    : [...selected.value, value]
}

const save = () => {
  emit('save', selected.value)
}
</script>

<template>
  <section class="preference-screen">
    <div class="preference-screen__head">
      <span>讲解偏好</span>
      <h1>你更希望数字人怎么带你逛？</h1>
      <p>选几项就好，之后它会更懂你的导览重点。</p>
    </div>

    <div class="preference-grid">
      <button
        v-for="option in preferenceOptions"
        :key="option.value"
        class="preference-card"
        :class="{ 'preference-card--active': selected.includes(option.value) }"
        type="button"
        @click="toggle(option.value)"
      >
        <strong>{{ option.title }}</strong>
        <span>{{ option.text }}</span>
      </button>
    </div>

    <div class="preference-screen__actions">
      <button class="preference-submit" type="button" @click="save">
        {{ selected.length ? '保存偏好' : '暂时跳过' }}
      </button>
    </div>
  </section>
</template>
