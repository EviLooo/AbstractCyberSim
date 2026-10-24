import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    environmentOptions: { jsdom: { url: 'http://localhost/' } },
    // Keep the existing node:test suite on its own runner.
    include: ['tests/**/*.integration.test.tsx'],
    clearMocks: true,
    restoreMocks: true,
  },
});
