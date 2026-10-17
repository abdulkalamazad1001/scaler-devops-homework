import { createRequire } from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const [url, screenshot] = process.argv.slice(2);
assert(url && screenshot, 'Usage: node review/check_demo_browser.mjs URL SCREENSHOT');
const browser = await chromium.launch({headless: true});
try {
  const page = await browser.newPage({viewport: {width: 1280, height: 800}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const response = await page.goto(url, {waitUntil: 'networkidle'});
  assert.equal(response.status(), 200);
  await page.getByText(/hello world/i).first().waitFor();
  assert.deepEqual(errors, []);
  await fs.mkdir(path.dirname(screenshot), {recursive: true});
  await page.screenshot({path: screenshot, fullPage: true});
  console.log(JSON.stringify({url, status: response.status(), text: await page.locator('body').innerText(), javascriptErrors: errors, screenshot}, null, 2));
} finally {
  await browser.close();
}
