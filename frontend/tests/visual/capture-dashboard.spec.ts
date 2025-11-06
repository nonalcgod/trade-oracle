import { test, expect } from '@playwright/test';

/**
 * Trade Oracle Visual Testing Suite
 * Captures screenshots for progressive UI refinement workflow
 *
 * Usage:
 * npm run test:visual:capture  (run in frontend directory)
 *
 * Outputs:
 * - screenshots/dashboard-full-{viewport}.png
 * - screenshots/portfolio-component.png
 * - screenshots/trades-component.png
 * - screenshots/positions-component.png
 * - screenshots/charts-component.png
 */

test.describe('Trade Oracle Dashboard Visual Capture', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/');

    // Wait for backend connection (or timeout after 10s)
    await page.waitForSelector('text=Backend:', { timeout: 10000 }).catch(() => {
      console.warn('Backend status indicator not found - proceeding with screenshot anyway');
    });

    // Wait for data to load (look for portfolio balance)
    await page.waitForSelector('text=/\\$/i', { timeout: 10000 }).catch(() => {
      console.warn('Portfolio balance not found - might be using mock data');
    });

    // Wait for any animations to complete
    await page.waitForTimeout(1000);
  });

  test('capture full page - desktop (MacBook Pro 14")', async ({ page }) => {
    // Set MacBook Pro 14" scaled resolution
    await page.setViewportSize({ width: 1512, height: 982 });

    await page.screenshot({
      path: 'tests/visual/screenshots/dashboard-full-desktop.png',
      fullPage: true,
      animations: 'disabled', // Disable animations for consistent screenshots
    });

    console.log('✅ Captured: dashboard-full-desktop.png');
  });

  test('capture full page - tablet (iPad)', async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 1366 });

    await page.screenshot({
      path: 'tests/visual/screenshots/dashboard-full-tablet.png',
      fullPage: true,
      animations: 'disabled',
    });

    console.log('✅ Captured: dashboard-full-tablet.png');
  });

  test('capture full page - mobile (iPhone 14 Pro)', async ({ page }) => {
    await page.setViewportSize({ width: 393, height: 852 });

    await page.screenshot({
      path: 'tests/visual/screenshots/dashboard-full-mobile.png',
      fullPage: true,
      animations: 'disabled',
    });

    console.log('✅ Captured: dashboard-full-mobile.png');
  });

  test('capture portfolio component', async ({ page }) => {
    // Look for portfolio section by identifying hero balance
    const portfolioSection = page.locator('section, div').filter({
      hasText: /portfolio|balance/i,
    }).first();

    if (await portfolioSection.count() > 0) {
      await portfolioSection.screenshot({
        path: 'tests/visual/screenshots/portfolio-component.png',
        animations: 'disabled',
      });
      console.log('✅ Captured: portfolio-component.png');
    } else {
      console.warn('⚠️  Portfolio component not found by text match');

      // Fallback: try to find by dollar sign (hero metric)
      const heroMetric = page.locator('text=/\\$[0-9,]+\\.?[0-9]*/').first();
      const parentSection = heroMetric.locator('xpath=ancestor::section[1]|ancestor::div[@class][1]').first();

      if (await parentSection.count() > 0) {
        await parentSection.screenshot({
          path: 'tests/visual/screenshots/portfolio-component.png',
          animations: 'disabled',
        });
        console.log('✅ Captured: portfolio-component.png (fallback method)');
      } else {
        console.error('❌ Could not locate portfolio component');
      }
    }
  });

  test('capture trades component', async ({ page }) => {
    // Look for trades section (table or card layout)
    const tradesSection = page.locator('section, div').filter({
      hasText: /trade|symbol|SPY|QQQ|entry|exit/i,
    }).first();

    if (await tradesSection.count() > 0) {
      await tradesSection.screenshot({
        path: 'tests/visual/screenshots/trades-component.png',
        animations: 'disabled',
      });
      console.log('✅ Captured: trades-component.png');
    } else {
      console.warn('⚠️  Trades component not found - might have zero trades');
    }
  });

  test('capture positions component', async ({ page }) => {
    // Look for positions section
    const positionsSection = page.locator('section, div').filter({
      hasText: /position|open|unrealized|p&l/i,
    }).first();

    if (await positionsSection.count() > 0) {
      await positionsSection.screenshot({
        path: 'tests/visual/screenshots/positions-component.png',
        animations: 'disabled',
      });
      console.log('✅ Captured: positions-component.png');
    } else {
      console.warn('⚠️  Positions component not found - might have zero open positions');
    }
  });

  test('capture charts component', async ({ page }) => {
    // Look for Recharts SVG elements
    const chartsSvg = page.locator('svg.recharts-surface').first();

    if (await chartsSvg.count() > 0) {
      // Get parent container of chart
      const chartsContainer = chartsSvg.locator('xpath=ancestor::div[@class][2]').first();

      await chartsContainer.screenshot({
        path: 'tests/visual/screenshots/charts-component.png',
        animations: 'disabled',
      });
      console.log('✅ Captured: charts-component.png');
    } else {
      console.warn('⚠️  Charts component not found - Recharts might not be rendering');
    }
  });

  test('capture with color samples', async ({ page }) => {
    // Capture screenshots with specific elements highlighted for color analysis
    await page.screenshot({
      path: 'tests/visual/screenshots/dashboard-color-analysis.png',
      fullPage: true,
      animations: 'disabled',
    });

    // Extract and log color samples from key elements
    const backgroundColor = await page.evaluate(() => {
      const body = document.body;
      return window.getComputedStyle(body).backgroundColor;
    });

    const cardColors = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll('[class*="rounded"]'));
      return cards.slice(0, 5).map(card => ({
        className: card.className,
        backgroundColor: window.getComputedStyle(card).backgroundColor,
        borderColor: window.getComputedStyle(card).borderColor,
        borderRadius: window.getComputedStyle(card).borderRadius,
      }));
    });

    console.log('\n📊 Color Analysis:');
    console.log('Page Background:', backgroundColor);
    console.log('Card Samples:', JSON.stringify(cardColors, null, 2));
  });
});

test.describe('Visual Regression Testing', () => {
  test('compare full page against baseline', async ({ page }) => {
    await page.setViewportSize({ width: 1512, height: 982 });

    // This will auto-create baseline on first run, compare on subsequent runs
    await expect(page).toHaveScreenshot('dashboard-baseline.png', {
      fullPage: true,
      maxDiffPixels: 100, // Allow up to 100 pixels difference (for dynamic content)
      animations: 'disabled',
      // Mask dynamic elements that change frequently
      mask: [
        page.locator('text=/updated.*ago/i'), // "Updated 3s ago" timestamp
        page.locator('text=/\\d{1,2}:\\d{2}:\\d{2}/'), // Time stamps
      ],
    });

    console.log('✅ Visual regression test passed');
  });
});
