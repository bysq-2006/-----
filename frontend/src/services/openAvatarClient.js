const DEFAULT_BACKEND_ORIGIN = 'https://localhost:8282'

const isDev = import.meta.env.DEV
const backendOrigin = import.meta.env.VITE_OPEN_AVATAR_ORIGIN || DEFAULT_BACKEND_ORIGIN

const makeBackendUrl = (path) => {
  if (isDev && !import.meta.env.VITE_OPEN_AVATAR_ORIGIN) {
    return path
  }
  return `${backendOrigin}${path}`
}

const requestJson = async (path, options, errorPrefix) => {
  const response = await fetch(makeBackendUrl(path), options)
  if (!response.ok) {
    throw new Error(`${errorPrefix}：${response.status}`)
  }
  return response.json()
}

export const initOpenAvatarConfig = () =>
  requestJson('/openavatarchat/initconfig', undefined, '初始化数字人失败')

export const sendWebRtcOffer = (body) =>
  requestJson(
    '/webrtc/offer',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    },
    'WebRTC 连接失败'
  )
