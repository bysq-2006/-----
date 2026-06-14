export const preferenceOptions = [
  { value: 'history', title: '历史文化', text: '古建、典故、人物故事讲细一点。' },
  { value: 'nature', title: '自然风光', text: '更关注景色、拍照点和季节看点。' },
  { value: 'route', title: '路线规划', text: '帮我少绕路，安排顺路的游览节奏。' },
  { value: 'short', title: '简洁讲解', text: '回答短一点，先给重点。' },
  { value: 'deep', title: '深度讲解', text: '可以展开背景和文化价值。' },
  { value: 'family', title: '轻松亲子', text: '讲得更好懂，也适合陪老人孩子游玩。' },
]

export const getPreferenceKey = (userId) => (userId ? `scenic_avatar_preferences:${userId}` : '')

export const preferenceTextFromValues = (values) =>
  preferenceOptions
    .filter((option) => values.includes(option.value))
    .map((option) => option.title)
    .join('、')

export const readUserPreferenceText = (userId) => {
  const raw = localStorage.getItem(getPreferenceKey(userId))
  if (!raw) return ''

  try {
    const value = JSON.parse(raw)
    return Array.isArray(value) ? preferenceTextFromValues(value) : String(value || '')
  } catch {
    return raw
  }
}

export const hasStoredPreferences = (userId) => Boolean(localStorage.getItem(getPreferenceKey(userId)))

export const writeUserPreferenceText = (userId, text) => {
  const key = getPreferenceKey(userId)
  if (key) {
    localStorage.setItem(key, text)
  }
}
