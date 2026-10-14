import { createRequire } from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const require = createRequire(new URL('../frontend/package.json', import.meta.url));
const { chromium } = require('playwright');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const evidence = path.join(root, 'evidence');
const escape = text => text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
try {
  for (const name of ['pytest', 'kubernetes', 'helm', 'terraform-validate', 'commit-history', 'autoscaling', 'metrics', 'compose-build']) {
    const transcript = await fs.readFile(path.join(evidence, `${name}.txt`), 'utf8');
    await page.setContent(`<html><body style="margin:0;padding:32px;background:#f5f8f6;color:#183b2d;font-family:Arial"><h1 style="font-size:24px">CampusDesk | Captured command output: ${escape(name)}</h1><p>Original recorded output, rendered for readability. Environment: local Windows / Kind.</p><pre style="font:14px/1.55 monospace;white-space:pre-wrap;overflow-wrap:anywhere">${escape(transcript)}</pre></body></html>`);
    await page.screenshot({path:path.join(evidence,`${name}-output.png`),fullPage:true});
  }
  const run = process.env.CI_RUN_ID || '38639295103';
  for (const component of ['backend','frontend']) {
    const report = await fs.readFile(path.join(evidence,`ci-run-${run}/trivy-reports/${component}-trivy.txt`),'utf8');
    await page.setContent(`<html><body style="margin:0;padding:32px;background:#f5f8f6;color:#183b2d;font-family:Arial"><h1>Trivy | ${escape(component)} | HIGH / CRITICAL gate</h1><p>Original artifact from GitHub Actions run ${escape(run)}. Not a local scan.</p><pre style="font:12px/1.4 monospace;white-space:pre-wrap">${escape(report)}</pre></body></html>`);
    await page.screenshot({path:path.join(evidence,`trivy-${component}-output.png`),fullPage:true});
  }
  for (const name of ['backend','frontend']) {
    await page.goto(`https://github.com/users/abdulkalamazad1001/packages/container/package/campusdesk-${name}`);
    await page.getByRole('heading', { name: `campusdesk-${name}`, exact: false }).first().waitFor();
    await page.screenshot({path:path.join(evidence,`registry-${name}.png`),fullPage:true});
  }
  await page.goto('http://campusdesk.localhost:8088');
  await page.locator('.page-title').getByRole('button',{name:'New ticket',exact:true}).waitFor();
  await page.waitForFunction(()=>Array.from(document.images).every(image=>image.complete));
  await page.screenshot({path:path.join(evidence,'application-ingress.png'),fullPage:true});
  console.log('Captured actual transcripts, public packages and Ingress application.');
} finally {
  await browser.close();
}
