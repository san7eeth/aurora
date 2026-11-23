import { test, expect, Page } from '@playwright/test';

/**
 * Aurora E2E Tests – Main UI
 *
 * Assumes:
 *   - Backend running on http://localhost:8000
 *   - Frontend running on http://localhost:5173 (or AURORA_URL env var)
 *
 * Run: npx playwright test
 */

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function waitForAppReady(page: Page) {
  await page.goto('/');
  // Wait for the root element to hydrate
  await page.waitForSelector('#root', { timeout: 10_000 });
  // A short pause for React to finish rendering
  await page.waitForTimeout(500);
}

// ---------------------------------------------------------------------------
// Suite: Application loads
// ---------------------------------------------------------------------------

test.describe('Aurora – App loads', () => {
  test('page title is "Aurora"', async ({ page }) => {
    await waitForAppReady(page);
    await expect(page).toHaveTitle(/Aurora/i);
  });

  test('root container renders without errors', async ({ page }) => {
    await waitForAppReady(page);
    const root = page.locator('#root');
    await expect(root).toBeVisible();
  });

  test('no JavaScript errors on load', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (err) => errors.push(err.message));
    await waitForAppReady(page);
    expect(errors).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// Suite: Navigation
// ---------------------------------------------------------------------------

test.describe('Aurora – Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await waitForAppReady(page);
  });

  test('dashboard / home view is visible', async ({ page }) => {
    // Look for the main chat or dashboard container
    const main = page.locator('main, [data-testid="dashboard"], [data-testid="chat-view"]').first();
    await expect(main).toBeVisible({ timeout: 8_000 });
  });

  test('sidebar or nav links are present', async ({ page }) => {
    // Aurora uses a sidebar for navigation
    const nav = page.locator('nav, aside, [data-testid="sidebar"]').first();
    await expect(nav).toBeVisible({ timeout: 8_000 });
  });
});

// ---------------------------------------------------------------------------
// Suite: Chat functionality
// ---------------------------------------------------------------------------

test.describe('Aurora – Chat', () => {
  test.beforeEach(async ({ page }) => {
    await waitForAppReady(page);
  });

  test('chat input is present', async ({ page }) => {
    const input = page
      .locator('input[type="text"], textarea, [data-testid="chat-input"]')
      .first();
    await expect(input).toBeVisible({ timeout: 8_000 });
  });

  test('send button is present', async ({ page }) => {
    const btn = page
      .locator('button[type="submit"], [data-testid="send-btn"], [aria-label*="send" i]')
      .first();
    await expect(btn).toBeVisible({ timeout: 8_000 });
  });

  test('typing in chat input works', async ({ page }) => {
    const input = page
      .locator('input[type="text"], textarea, [data-testid="chat-input"]')
      .first();
    await input.click();
    await input.fill('Hello Aurora');
    await expect(input).toHaveValue('Hello Aurora');
  });
});

// ---------------------------------------------------------------------------
// Suite: Backend health (API smoke tests via Playwright fetch)
// ---------------------------------------------------------------------------

test.describe('Aurora – Backend health', () => {
  test('GET /health returns 200', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/health`);
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('status');
  });

  test('GET /api/models returns model list', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/models`);
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('models');
    expect(Array.isArray(body.models)).toBe(true);
  });
});
