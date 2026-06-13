const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function takeScreenshot(page, name, options = {}) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `${name}-${timestamp}.png`;
  const filepath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: filepath, fullPage: true, ...options });
  console.log(`Screenshot saved: ${filepath}`);
  return filepath;
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
  });
  const page = await context.newPage();

  try {
    // 1. Login Page
    console.log('Navigating to login page...');
    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle' });
    await takeScreenshot(page, '01-login-page');

    // Fill login form - click the credentials dropdown first
    console.log('Opening credentials login...');
    await page.click('summary:has-text("Development Credentials")');
    await page.waitForTimeout(500);
    await takeScreenshot(page, '02-login-credentials-open');

    console.log('Filling login form...');
    await page.fill('input[id="email"]', 'admin@bank.internal');
    await page.fill('input[id="password"]', 'password123');
    await takeScreenshot(page, '03-login-filled');

    // Submit login
    console.log('Submitting login...');
    await page.click('button[type="submit"]:has-text("Sign In with Credentials")');
    await page.waitForTimeout(3000);
    const currentUrl = page.url();
    console.log('Current URL after login:', currentUrl);
    await takeScreenshot(page, '04-after-login');

    // Navigate to dashboard manually if not redirected
    if (!currentUrl.includes('/chat') && !currentUrl.includes('/dashboard')) {
      console.log('Navigating to dashboard manually...');
      await page.goto('http://localhost:3000/chat', { waitUntil: 'networkidle' });
    }
    await page.waitForLoadState('networkidle');

    // 2. Dashboard Overview
    console.log('On dashboard...');
    await takeScreenshot(page, '03-dashboard-overview');

    // 3. Incidents Page
    console.log('Navigating to incidents...');
    await page.goto('http://localhost:3000/incidents', { waitUntil: 'networkidle' });
    await takeScreenshot(page, '04-incidents-list');

    // 4. Incidents Detail (click first incident)
    console.log('Opening incident detail...');
    const firstIncidentLink = page.locator('a[href^="/incidents/"]').first();
    if (await firstIncidentLink.count() > 0) {
      await firstIncidentLink.click();
      await page.waitForLoadState('networkidle');
      await takeScreenshot(page, '05-incident-detail');
    }

    // 5. Chat/Copilot Page
    console.log('Navigating to chat...');
    await page.goto('http://localhost:3000/chat', { waitUntil: 'networkidle' });
    await takeScreenshot(page, '06-chat-page');

    // Send a message in chat
    console.log('Sending chat message...');
    const chatInput = page.locator('textarea[placeholder*="message" i], input[placeholder*="message" i]').first();
    if (await chatInput.count() > 0) {
      await chatInput.fill('Show me the current system status and active incidents');
      await takeScreenshot(page, '07-chat-with-message');
      await chatInput.press('Enter');
      await page.waitForTimeout(2000);
      await takeScreenshot(page, '08-chat-response');
    }

    // 6. Metrics/Monitoring Page
    console.log('Navigating to metrics...');
    await page.goto('http://localhost:3000/metrics', { waitUntil: 'networkidle' });
    await takeScreenshot(page, '09-metrics-page');

    // 7. Settings Page
    console.log('Navigating to settings...');
    await page.goto('http://localhost:3000/settings', { waitUntil: 'networkidle' });
    await takeScreenshot(page, '10-settings-page');

    // 8. Runbooks Page
    console.log('Navigating to runbooks...');
    await page.goto('http://localhost:3000/runbooks', { waitUntil: 'networkidle' });
    await takeScreenshot(page, '11-runbooks-page');

    // 9. RCA Page
    console.log('Navigating to RCA...');
    await page.goto('http://localhost:3000/rca', { waitUntil: 'networkidle' });
    await takeScreenshot(page, '12-rca-page');

    // 10. Mobile view
    console.log('Taking mobile view screenshot...');
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('http://localhost:3000/dashboard', { waitUntil: 'networkidle' });
    await takeScreenshot(page, '13-dashboard-mobile');

    console.log('\n✅ All screenshots captured successfully!');
    console.log(`📁 Screenshots saved to: ${SCREENSHOT_DIR}`);

  } catch (error) {
    console.error('Error during screenshot capture:', error);
    await takeScreenshot(page, 'error-state');
  } finally {
    await browser.close();
  }
}

main().catch(console.error);