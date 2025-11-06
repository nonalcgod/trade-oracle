import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Trade Oracle visual testing
 * Optimized for progressive UI refinement workflow with benai-ui-critic/implementer agents
 */
export default defineConfig({
  testDir: './tests/visual',

  // Folder for test artifacts (screenshots, traces, etc.)
  outputDir: './test-results',

  // Snapshot path template for visual comparisons
  snapshotPathTemplate: '{testDir}/screenshots/{testFilePath}/{arg}{ext}',

  // Run tests in files in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Number of workers
  workers: process.env.CI ? 1 : undefined,

  // Reporter to use
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list']
  ],

  // Shared settings for all the projects below
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: 'http://localhost:3000',

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Screenshot settings
    screenshot: 'only-on-failure',

    // Video settings
    video: 'retain-on-failure',
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // MacBook Pro 14" scaled resolution (default viewport)
        viewport: { width: 1512, height: 982 }
      },
    },

    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1512, height: 982 }
      },
    },

    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        viewport: { width: 1512, height: 982 }
      },
    },

    // Mobile viewports
    {
      name: 'Mobile Chrome',
      use: {
        ...devices['iPhone 14 Pro'],
      },
    },

    {
      name: 'Mobile Safari',
      use: {
        ...devices['iPhone 14 Pro'],
      },
    },

    // Tablet viewport
    {
      name: 'iPad Pro',
      use: {
        ...devices['iPad Pro'],
      },
    },
  ],

  // Run your local dev server before starting the tests
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000, // 2 minutes for Vite to start
  },
});
