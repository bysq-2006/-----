import { sendWebRtcOffer } from '../services/openAvatarClient'

const MIC_CONSTRAINTS = { audio: true, video: false }

const stopOnce = (track, cleanup) => {
  const rawStop = track.stop.bind(track)
  let stopped = false

  track.stop = () => {
    if (stopped) return
    stopped = true
    rawStop()
    cleanup?.()
  }

  return track
}

const waitForDataChannelOpen = (dataChannel, timeoutMs = 90000) => {
  if (dataChannel.readyState === 'open') return Promise.resolve()

  return new Promise((resolve, reject) => {
    const timeoutId = window.setTimeout(() => {
      cleanup()
      reject(new Error('数字人数据通道连接超时'))
    }, timeoutMs)

    const cleanup = () => {
      window.clearTimeout(timeoutId)
      dataChannel.removeEventListener('open', handleOpen)
      dataChannel.removeEventListener('error', handleError)
      dataChannel.removeEventListener('close', handleClose)
    }

    const handleOpen = () => {
      cleanup()
      resolve()
    }

    const handleError = () => {
      cleanup()
      reject(new Error('数字人数据通道打开失败'))
    }

    const handleClose = () => {
      cleanup()
      reject(new Error('数字人数据通道提前关闭'))
    }

    dataChannel.addEventListener('open', handleOpen)
    dataChannel.addEventListener('error', handleError)
    dataChannel.addEventListener('close', handleClose)
  })
}

export const createSilentAudioTrack = () => {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext
  const audioContext = new AudioContextClass()
  const oscillator = audioContext.createOscillator()
  const gainNode = audioContext.createGain()
  const destination = audioContext.createMediaStreamDestination()

  oscillator.frequency.setValueAtTime(0, audioContext.currentTime)
  gainNode.gain.setValueAtTime(0, audioContext.currentTime)
  oscillator.connect(gainNode)
  gainNode.connect(destination)
  oscillator.start()

  const track = destination.stream.getAudioTracks()[0]
  return stopOnce(track, () => {
    if (audioContext.state !== 'closed') {
      audioContext.close().catch(() => {})
    }
  })
}

export const createBlankVideoTrack = () => {
  const canvas = document.createElement('canvas')
  canvas.width = 2
  canvas.height = 2
  const context = canvas.getContext('2d')
  context.fillStyle = '#ffffff'
  context.fillRect(0, 0, canvas.width, canvas.height)

  const stream = canvas.captureStream(10)
  return stopOnce(stream.getVideoTracks()[0], () => canvas.remove())
}

export const createLocalStream = async ({ useAsr }) => {
  return new MediaStream([await createInputAudioTrack(useAsr), createBlankVideoTrack()])
}

export const createInputAudioTrack = async (useAsr) => {
  if (!useAsr) return createSilentAudioTrack()

  try {
    const micStream = await navigator.mediaDevices.getUserMedia(MIC_CONSTRAINTS)
    return micStream.getAudioTracks()[0]
  } catch {
    throw new Error('无法访问麦克风，请检查浏览器权限。')
  }
}

export const replaceInputAudioTrack = async ({ peerConnection, stream, useAsr }) => {
  if (!peerConnection || !stream) return null

  const nextTrack = await createInputAudioTrack(useAsr)
  const currentTrack = stream.getAudioTracks()[0]
  const audioSender = peerConnection.getSenders().find((sender) => sender.track?.kind === 'audio')

  if (audioSender) {
    await audioSender.replaceTrack(nextTrack)
  }

  if (currentTrack) {
    stream.removeTrack(currentTrack)
    currentTrack.stop()
  }

  stream.addTrack(nextTrack)
  return nextTrack
}

export const playRemoteVideo = async (remoteVideo, { unmuteAfterPlay = false } = {}) => {
  if (!remoteVideo?.srcObject) return

  remoteVideo.autoplay = true
  remoteVideo.playsInline = true
  remoteVideo.muted = true
  await remoteVideo.play().catch(() => {})

  if (unmuteAfterPlay) {
    remoteVideo.muted = false
  }
}

const attachRemoteTrack = (remoteVideo, event) => {
  const remoteStream =
    event.streams[0] ||
    (remoteVideo.srcObject instanceof MediaStream ? remoteVideo.srcObject : new MediaStream())

  if (!remoteStream.getTracks().some((track) => track.id === event.track.id)) {
    remoteStream.addTrack(event.track)
  }

  remoteVideo.srcObject = remoteStream
  remoteVideo.volume = 1
}

export const setupAvatarWebRtc = async ({ stream, remoteVideo, rtcConfiguration }) => {
  const peerConnection = new RTCPeerConnection(rtcConfiguration)
  const dataChannel = peerConnection.createDataChannel('text')
  const webrtcId = Math.random().toString(36).slice(2)

  peerConnection.addEventListener('track', (event) => {
    attachRemoteTrack(remoteVideo, event)
    const play = () =>
      playRemoteVideo(remoteVideo, {
        unmuteAfterPlay: event.track.kind === 'audio',
      })
    play()
    event.track.addEventListener('unmute', play)
  })

  stream.getTracks().forEach((track) => {
    peerConnection.addTrack(track, stream)
  })

  peerConnection.onicecandidate = ({ candidate }) => {
    if (!candidate) return
    sendWebRtcOffer({
      candidate: candidate.toJSON(),
      webrtc_id: webrtcId,
      type: 'ice-candidate',
    }).catch((error) => console.error('发送 ICE candidate 失败', error))
  }

  const offer = await peerConnection.createOffer()
  await peerConnection.setLocalDescription(offer)

  const answer = await sendWebRtcOffer({
    sdp: offer.sdp,
    type: offer.type,
    webrtc_id: webrtcId,
  })

  await peerConnection.setRemoteDescription(answer)
  await waitForDataChannelOpen(dataChannel)

  dataChannel.send('handshake')
  dataChannel.send(JSON.stringify({ type: 'init' }))

  return {
    peerConnection,
    dataChannel,
    webrtcId,
  }
}

export const closeAvatarWebRtc = ({ peerConnection, stream }) => {
  const tracks = new Set(stream?.getTracks())
  peerConnection?.getSenders?.().forEach((sender) => {
    if (sender.track) tracks.add(sender.track)
  })
  tracks.forEach((track) => track.stop())

  peerConnection?.getTransceivers?.().forEach((transceiver) => {
    try {
      transceiver.stop?.()
    } catch {}
  })

  if (peerConnection && peerConnection.signalingState !== 'closed') {
    peerConnection.close?.()
  }
}
