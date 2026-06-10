const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const parseResponse = async (response) => {
  const text = await response.text()
  const data = text ? JSON.parse(text) : null

  if (!response.ok) {
    throw new Error(data?.detail || `请求失败，状态码 ${response.status}`)
  }

  return data
}

export const sendChatCompletion = ({ token, messages }) =>
  fetch(`${API_BASE_URL}/v1/chat/completions`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages,
      stream: false,
    }),
  }).then(parseResponse)
