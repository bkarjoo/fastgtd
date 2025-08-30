// Simple Playwright smoke test for modular frontend wiring
// Skips if Playwright browsers are not installed.

const path = require('path');

async function run() {
  let chromium;
  try {
    // Prefer full playwright if available, fallback to core
    try { chromium = require('playwright').chromium; } catch { chromium = require('playwright-core').chromium; }
  } catch (e) {
    console.log('Playwright not available; skipping smoke test.');
    return;
  }

  const filePath = path.resolve(__dirname, '..', 'mobile_unified_nodes.html');
  const url = 'file://' + filePath;

  let browser;
  try {
    browser = await chromium.launch({ headless: true });
  } catch (e) {
    console.log('No Playwright browser installed; skipping smoke test.');
    return;
  }

  const ctx = await browser.newContext();
  const page = await ctx.newPage();

  // Ensure no auth token on first load, so login screen shows
  await page.addInitScript(() => localStorage.removeItem('authToken'));
  await page.goto(url);

  // 1) Login screen visible
  await page.waitForSelector('#loginScreen .login-title', { timeout: 5000 });

  // 2) Global functions are exposed
  const globals = await page.evaluate(() => ({
    hasLogin: typeof window.login === 'function',
    hasLogout: typeof window.logout === 'function',
    hasLoadNodes: typeof window.loadNodes === 'function',
    hasUpdateNav: typeof window.updateNavigation === 'function',
    hasToggleDark: typeof window.toggleDarkMode === 'function',
    hasFlagFns: [
      typeof window.enableModularNodes === 'function',
      typeof window.disableModularNodes === 'function',
      typeof window.useModNodes === 'function',
    ].every(Boolean)
  }));

  if (!globals.hasLogin || !globals.hasLogout || !globals.hasLoadNodes || !globals.hasUpdateNav || !globals.hasToggleDark || !globals.hasFlagFns) {
    throw new Error('Expected global handlers missing');
  }

  // 3) Force app view by setting auth and reloading
  await page.evaluate(() => localStorage.setItem('authToken', 'test-token'));
  await page.reload();
  await page.waitForSelector('#mainApp header.top-nav', { timeout: 5000 });

  // 4) Toggle dark mode and verify class changes
  const btn = page.locator('header.top-nav [title="Toggle Dark Mode"]');
  await btn.click();
  const isDark = await page.evaluate(() => document.body.classList.contains('dark-mode'));
  if (!isDark) throw new Error('Dark mode did not enable');

  await btn.click();
  const isDarkOff = await page.evaluate(() => !document.body.classList.contains('dark-mode'));
  if (!isDarkOff) throw new Error('Dark mode did not disable');

  await browser.close();
  console.log('Smoke test passed.');
}

run().catch(err => {
  console.error('Smoke test failed:', err.message);
  process.exit(1);
});

