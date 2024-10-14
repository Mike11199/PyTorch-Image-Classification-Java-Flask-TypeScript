import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  server: {
    proxy: {
      //'/api-java-spring-boot':'http://localhost:5001', // express.js
      // '/api-java-spring-boot': {
      //   target: 'http://127.0.0.1:5000',  // python flask
      //   changeOrigin: true,
      // }
      '/api-java-spring-boot': {
        target: 'http://127.0.0.1:8080',  // java spring boot
        changeOrigin: true,
      }
    },
  },
  plugins: [react()],
});