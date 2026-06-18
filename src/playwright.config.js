import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [['html', { outputFolder: 'playwright-report', open: 'never' }], ['list']],

  use: {
    baseURL: 'http://localhost:8000',
    headless: true,
    screenshot: 'on',
    video: 'on',
    trace: 'on',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],

  webServer: {
    command: 'uvicorn backend.main:app --host 0.0.0.0 --port 8000',
    url: 'http://localhost:8000/api/v1/health',
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
    stdout: 'pipe',
    stderr: 'pipe',
  },
});
