import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      'styled-components': path.resolve(__dirname, 'node_modules/styled-components'),
    },
  },
  optimizeDeps: {
    include: ['styled-components', '@kanaries/graphic-walker']
  },
  server: {
    port: 3000
  }
})
