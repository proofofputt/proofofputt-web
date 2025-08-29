import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    rollupOptions: {
      external: [
        '@tauri-apps/api/tauri',
        '@tauri-apps/api/window',
        '@tauri-apps/api/path',
        '@tauri-apps/api/fs'
      ]
    }
  }
})