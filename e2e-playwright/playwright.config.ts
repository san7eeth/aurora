import { defineConfig, devices } from '@playwright/test';

/**
 * Aurora Playwright E2E Configuration
 * Docs: https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,       // Aurora has shared backend state — run sequentially
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['junit', { outputFile: 'playwright-results.xml' }],
    ['list'],
  ],
  use: {
    baseURL: process.env.AURORA_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  /* Start Aurora dev server automatically when running locally */
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:5173',
  //   cwd: '../frontend',
  //   reuseExistingServer: !process.env.CI,
  // },
});
