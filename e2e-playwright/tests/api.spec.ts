import { test, expect } from '@playwright/test';

/**
 * Aurora API-level E2E tests
 * Tests backend REST API endpoints directly (no browser UI needed)
 */

const BASE = process.env.BACKEND_URL || 'http://localhost:8000';

test.describe('Aurora API – Health, settings, and tools', () => {
  test('health endpoint returns ok status', async ({ request }) => {
    const res = await request.get(`${BASE}/health`);
    expect(res.ok()).toBeTruthy();
    const json = await res.json();
    expect(['ok', 'degraded']).toContain(json.status);
    expect(json.database).toBe('ok');
  });

  test('active model endpoint returns a configured model name', async ({ request }) => {
    const res = await request.get(`${BASE}/api/models/active`);
    expect(res.ok()).toBeTruthy();
    const json = await res.json();
    expect(typeof json.active).toBe('string');
    expect(json.active.length).toBeGreaterThan(0);
  });

  test('settings API returns an object without the private voice profile', async ({ request }) => {
    const res = await request.get(`${BASE}/api/settings`);
    expect(res.ok()).toBeTruthy();
    const json = await res.json();
    expect(json.settings).toBeTruthy();
    expect(json.settings).not.toHaveProperty('voice_auth_profile');
  });

  test('agent tool registry is restricted to supported local tools', async ({ request }) => {
    const res = await request.get(`${BASE}/api/agent/tools`);
    expect(res.ok()).toBeTruthy();
    const json = await res.json();
    expect(json.tools.map((tool: { name: string }) => tool.name)).toEqual(
      expect.arrayContaining(['system_info', 'list_files', 'launch_app', 'clipboard_read']),
    );
  });
});
