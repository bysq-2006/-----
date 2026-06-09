const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const errorMessages = {
  LOGIN_BAD_CREDENTIALS: '邮箱或密码不正确，请检查后再试。',
  LOGIN_USER_NOT_VERIFIED: '账号还没有完成验证，请先验证邮箱。',
  REGISTER_USER_ALREADY_EXISTS: '这个邮箱已经注册过了，可以直接登录。',
  REGISTER_INVALID_PASSWORD: '密码不符合要求，请换一个更安全的密码。',
  RESET_PASSWORD_BAD_TOKEN: '重置链接已失效，请重新获取。',
  VERIFY_USER_BAD_TOKEN: '验证链接已失效，请重新获取。',
}

const normalizeDetail = (detail) => {
  if (!detail) return ''

  if (typeof detail === 'string') {
    return errorMessages[detail] || detail
  }

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).filter(Boolean).join('；')
  }

  if (typeof detail === 'object') {
    const codeMessage = errorMessages[detail.code]
    const reason = detail.reason || detail.msg
    return [codeMessage, reason].filter(Boolean).join(' ')
  }

  return ''
}

const parseResponse = async (response) => {
  const text = await response.text()
  const data = text ? JSON.parse(text) : null

  if (!response.ok) {
    const message = normalizeDetail(data?.detail)
    throw new Error(message || `请求失败，状态码 ${response.status}`)
  }

  return data
}

const request = async (url, options) => {
  try {
    const response = await fetch(url, options)
    return parseResponse(response)
  } catch (error) {
    if (error instanceof SyntaxError) {
      throw new Error('服务器返回内容格式异常，请稍后再试。')
    }

    if (error instanceof TypeError) {
      throw new Error('无法连接后端服务，请确认后端已启动并且地址正确。')
    }

    throw error
  }
}

export const registerUser = ({ email, password, displayName }) =>
  request(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      password,
      display_name: displayName || null,
    }),
  })

export const loginUser = ({ email, password }) => {
  const form = new URLSearchParams()
  form.set('username', email)
  form.set('password', password)

  return request(`${API_BASE_URL}/auth/jwt/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  })
}

export const fetchCurrentUser = (token) =>
  request(`${API_BASE_URL}/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
