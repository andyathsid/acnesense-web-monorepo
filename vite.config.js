import { defineConfig } from 'vite';
import { resolve } from 'path';
import fullReload from 'vite-plugin-full-reload';

export default defineConfig({
  plugins: [
    fullReload(['views/**/*.ejs', 'server.js', 'routes/**/*.js'])
  ],
  root: resolve(import.meta.dirname, 'src'),
  publicDir: resolve(import.meta.dirname, 'public'),
  build: {
    outDir: resolve(import.meta.dirname, 'dist'),
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        main: resolve(import.meta.dirname, 'src/js/main.js'),
        deteksi: resolve(import.meta.dirname, 'src/js/deteksi.js')
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true
      },
      '/auth': {
        target: 'http://localhost:3000',
        changeOrigin: true
      },
      '/dashboard': {
        target: 'http://localhost:3000',
        changeOrigin: true
      },
      '/deteksi': {
        target: 'http://localhost:3000',
        changeOrigin: true
      },
      '/preview': {
        target: 'http://localhost:3000',
        changeOrigin: true
      },
      '/hasil': {
        target: 'http://localhost:3000',
        changeOrigin: true
      },
      '/riwayat': {
        target: 'http://localhost:3000',
        changeOrigin: true
      },
      '/chatbot': {
        target: 'http://localhost:3000',
        changeOrigin: true
      }
    }
  }
});
