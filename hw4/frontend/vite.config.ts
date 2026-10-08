import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// During development, send API and image requests to the FastAPI backend.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/images': 'http://localhost:8000',
    },
  },
})
