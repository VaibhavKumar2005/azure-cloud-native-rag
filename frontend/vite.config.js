import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite' // Ensure this is imported for v4

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(), // Tailwind v4 native Vite plugin
  ],
  server: {
    watch: {
      usePolling: true, // Forces updates even on OneDrive/Network drives
      interval: 100,    // Check every 100ms
    },
  },
})
