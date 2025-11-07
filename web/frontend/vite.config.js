import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  // Build configuration
  build: {
    rollupOptions: {
      output: {
        // Ensure consistent file naming for better caching
        assetFileNames: 'assets/[name].[hash].[ext]'
      }
    }
  }
})

