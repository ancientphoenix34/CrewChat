import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // Proxy API calls in dev so you don't have to hardcode the backend URL everywhere.
    // Node parallel: the "proxy" field in webpack devServer config, or http-proxy-middleware.
    // Any request to /api/... gets forwarded to FastAPI at :8000
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})

