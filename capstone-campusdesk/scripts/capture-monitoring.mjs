import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const require = createRequire(new URL('../frontend/package.json', import.meta.url));
const { chromium } = require('playwright');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const browser = await chromium.launch();
function secret(namespace, name, key) {
  const value = execFileSync('kubectl', ['--context','kind-campusdesk','-n',namespace,'get','secret',name,'-o',`jsonpath={.data.${key}}`], {encoding:'utf8'});
  return Buffer.from(value.trim(),'base64').toString();
}
try {
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  await page.goto('http://localhost:9090/targets');
  await page.getByText('campusdesk',{exact:false}).first().waitFor();
  let targets;
  for (let attempt = 0; attempt < 18; attempt++) {
    targets = await (await fetch('http://localhost:9090/api/v1/targets')).json();
    if (targets.data.activeTargets.length && targets.data.activeTargets.every(t=>t.health==='up')) break;
    if (attempt === 17) throw Error('Prometheus still has unhealthy targets after discovery settled');
    await new Promise(resolve=>setTimeout(resolve,5000));
  }
  await page.reload();
  await page.getByText('campusdesk',{exact:false}).first().waitFor();
  await page.screenshot({path:path.join(root,'evidence/prometheus-targets.png'),fullPage:true});
  await fs.writeFile(path.join(root,'evidence/prometheus-targets.json'),JSON.stringify(targets,null,2));
  await page.goto('http://localhost:3001/login');
  await page.getByRole('textbox',{name:'Email or username'}).fill('admin');
  await page.getByRole('textbox',{name:'Password',exact:true}).fill(secret('campusdesk','campusdesk-grafana','password'));
  await page.getByRole('button',{name:'Log in',exact:true}).click();
  await page.waitForURL(url=>!url.pathname.startsWith('/login'));
  await page.goto('http://localhost:3001/d/campusdesk?orgId=1&from=now-30m&to=now&refresh=10s');
  await page.getByText('Healthy backend replicas',{exact:true}).waitFor();
  await page.waitForFunction(()=>document.querySelectorAll('canvas').length>0);
  await page.getByText('Cancel',{exact:true}).waitFor({state:'hidden',timeout:60000});
  await page.waitForTimeout(2000);
  await page.screenshot({path:path.join(root,'evidence/grafana-dashboard.png'),fullPage:true});
  const query = await (await fetch('http://localhost:9090/api/v1/query?query='+encodeURIComponent('sum(rate(campusdesk_http_requests_total[5m]))'))).json();
  if (!query.data.result.length || Number(query.data.result[0].value[1])<=0) throw Error('No live request metrics');
  await fs.writeFile(path.join(root,'evidence/live-metrics.json'),JSON.stringify(query,null,2));
  const argo = await browser.newPage({viewport:{width:1440,height:1000}});
  await argo.goto('http://argocd.localhost:8088');
  await argo.getByRole('textbox',{name:'Username',exact:true}).fill('admin');
  await argo.getByRole('textbox',{name:'Password',exact:true}).fill(secret('argocd','argocd-initial-admin-secret','password'));
  await argo.getByRole('button',{name:'Sign In',exact:true}).click();
  await argo.waitForURL('**/applications**');
  await argo.goto('http://argocd.localhost:8088/applications/argocd/campusdesk');
  await argo.getByText('APP HEALTH',{exact:true}).waitFor();
  await argo.getByText('Healthy',{exact:true}).first().waitFor({timeout:60000});
  await argo.screenshot({path:path.join(root,'evidence/argocd-application.png'),fullPage:true});
  console.log('Captured Prometheus, live Grafana dashboard and Argo CD application.');
} finally { await browser.close(); }
