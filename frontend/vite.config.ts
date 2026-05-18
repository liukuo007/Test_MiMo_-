import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3100,
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/ws': {
        target: process.env.VITE_PROXY_TARGET_WS || 'ws://127.0.0.1:8100',
        ws: true,
      },
    },
  },
})
