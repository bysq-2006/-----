import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/openavatarchat': {
        target: 'https://localhost:8282',
        changeOrigin: true,
        secure: false,
      },
      '/webrtc/offer': {
        target: 'https://localhost:8282',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
