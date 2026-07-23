import react from '@vitejs/plugin-react';
import { defineConfig, type UserConfig } from 'vite';
import packageJson from './package.json';

type VitestConfig = UserConfig & {
  test: {
    globals: boolean;
    setupFiles: string;
    environment: string;
  };
};

const config = {
  plugins: [react()],
  define: {
    'import.meta.env.VITE_APP_VERSION': JSON.stringify(packageJson.version),
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  test: {
    globals: true,
    setupFiles: './tests/setup.ts',
    environment: 'jsdom',
  },
} satisfies VitestConfig;

export default defineConfig(config as UserConfig);
