import { test, expect } from '@playwright/test';

/**
 * Aurora API-level E2E tests
 * Tests backend REST API endpoints directly (no browser UI needed)
 */

const BASE = process.env.BACKEND_URL || 'http://localhost:8000';

test.describe('Aurora API – Health & Models', () => {
  test('health endpoint returns ok status', async ({ request }) => {
    const res = await request.get(`${BASE}/health`);
    expect(res.ok()).toBeTruthy();
    const json = await res.json();
    expect(json.status).toBe('ok');
  });

  test('models endpoint returns active model', async ({ request }) => {
    const res = await request.get(`${BASE}/api/models`);
    expect(res.ok()).toBeTruthy();
    const json = await res.json();
    expect(json).toHaveProperty('active');
    expect(typeof json.active).toBe('string');
  });
});

test.describe('Aurora API – Chat', () => {
  test('POST /api/chat returns a response', async ({ request }) => {
    const res = await request.post(`${BASE}/api/chat`, {
      data: {
        message: 'Say hello in one word',
        session_id: 'playwright-test',
      },
      timeout: 60_000,  // AI response can take time
    });
    expect(res.ok()).toBeTruthy();
    const json = await res.json();
    // Response should have a reply field
    expect(json).toHaveProperty('response');
    expect(typeof json.response).toBe('string');
    expect(json.response.length).toBeGreaterThan(0);
  });
});
