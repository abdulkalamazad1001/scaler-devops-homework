import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const require = createRequire(new URL('../frontend/package.json', import.meta.url));
const { chromium } = require('playwright');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const browser = await chromium.launch();
const context = await browser.newContext({viewport:{width:1280,height:720},recordVideo:{dir:path.join(root,'evidence/local/video'),size:{width:1280,height:720}}});
const page = await context.newPage();
const video = page.video();
const hold = milliseconds => new Promise(resolve=>setTimeout(resolve,milliseconds));
const escape = text => text.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
function secret(namespace,name) {
  return Buffer.from(execFileSync('kubectl',['--context','kind-campusdesk','-n',namespace,'get','secret',name,'-o','jsonpath={.data.password}'],{encoding:'utf8'}).trim(),'base64').toString();
}
async function report(title, content, duration=6000) {
  await page.setContent(`<html><head><title>${escape(title)}</title></head><body style="margin:0;padding:32px;background:#f7f9f8;color:#1b342a;font-family:Arial"><h1 style="font-size:27px">${escape(title)}</h1><pre style="font-size:15px;line-height:1.45;white-space:pre-wrap">${escape(content)}</pre></body></html>`);
  await page.evaluate(() => {
    const transcript = document.querySelector('pre');
    transcript.style.overflowWrap = 'anywhere';
    let size = 15;
    while (document.documentElement.scrollHeight > innerHeight && size > 9) {
      size -= 0.5;
      transcript.style.fontSize = `${size}px`;
    }
    if (document.documentElement.scrollHeight > innerHeight) throw Error('Report does not fit recording viewport');
  });
  await hold(duration);
}
try {
  await report('CampusDesk | Local project walkthrough','T. Abdul Kalam Azad | 24BCS10053\n\nThis recording shows the working local application and real verification results.\nAWS provisioning and the complete narrated AWS walkthrough are pending.\nSlide deck followed by application, source, CI/CD, Kubernetes and monitoring.',6000);
  for(let i=1;i<=12;i++) {
    const bytes=await fs.readFile(path.join(root,`evidence/local/slides/slide-${String(i).padStart(2,'0')}.png`));
    await page.setContent(`<html><body style="margin:0;background:white"><img style="width:1280px;height:720px;object-fit:contain" src="data:image/png;base64,${bytes.toString('base64')}"/></body></html>`);
    await hold(4500);
  }
  console.log('Recorded slide presentation.');
  await page.goto('http://campusdesk.localhost:8088');
  await page.getByRole('button',{name:'New ticket',exact:true}).waitFor();
  await hold(3000);
  await page.getByRole('button',{name:'New ticket',exact:true}).click();
  await page.getByLabel('Subject',{exact:true}).fill('Walkthrough verification ticket');
  await page.getByLabel('Requester',{exact:true}).fill('Demo Presenter');
  await page.getByLabel('Location',{exact:true}).fill('Campus IT Lab');
  await page.getByRole('combobox',{name:'Priority',exact:true}).selectOption('high');
  await hold(3000);
  await page.getByRole('button',{name:'Create ticket',exact:true}).click();
  await page.getByRole('button',{name:'Walkthrough verification ticket',exact:true}).click();
  await page.getByRole('combobox',{name:'Status',exact:true}).selectOption('resolved');
  await page.getByLabel('Assigned to',{exact:true}).fill('Campus Support');
  await page.getByRole('button',{name:'Save changes',exact:true}).click();
  await page.getByText('Ticket updated',{exact:true}).waitFor();
  await hold(3500);
  await page.getByRole('button',{name:'Walkthrough verification ticket',exact:true}).click();
  await page.getByRole('button',{name:'Delete ticket',exact:true}).click();
  await page.locator('.delete-confirm').getByRole('button',{name:'Delete ticket',exact:true}).click();
  await page.getByText('Ticket deleted',{exact:true}).waitFor();
  console.log('Recorded real ticket CRUD.');
  const source = await fs.readFile(path.join(root,'backend/app/main.py'),'utf8');
  await report('Source excerpt | backend/app/main.py',source.split('\n').slice(0,45).join('\n'));
  await report('Captured command output | API tests',await fs.readFile(path.join(root,'evidence/pytest.txt'),'utf8'),8000);
  await page.goto(`https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/${process.env.CI_RUN_ID || '38639295103'}`);
  await page.getByText('CampusDesk CI/CD',{exact:false}).first().waitFor();
  await hold(7000);
  await page.screenshot({path:path.join(root,'evidence/github-actions.png'),fullPage:true});
  await report('Captured command output | Kubernetes and autoscaling',await fs.readFile(path.join(root,'evidence/kubernetes.txt'),'utf8'),8000);
  await report('Captured command output | Terraform validation',await fs.readFile(path.join(root,'evidence/terraform-validate.txt'),'utf8')+'\nAWS plan/apply/destroy are deferred. Validation does not prove deployment.',6000);
  await page.goto('http://argocd.localhost:8088');
  await page.getByRole('textbox',{name:'Username',exact:true}).fill('admin');
  await page.getByRole('textbox',{name:'Password',exact:true}).fill(secret('argocd','argocd-initial-admin-secret'));
  await page.getByRole('button',{name:'Sign In',exact:true}).click();
  await page.waitForURL('**/applications**');
  await page.goto('http://argocd.localhost:8088/applications/argocd/campusdesk');
  await page.getByText('APP HEALTH',{exact:true}).waitFor();
  await hold(7000);
  await page.goto('http://localhost:9090/targets');
  await page.getByText('campusdesk',{exact:false}).first().waitFor();
  await hold(6000);
  await page.goto('http://localhost:3001/login');
  await page.getByRole('textbox',{name:'Email or username'}).fill('admin');
  await page.getByRole('textbox',{name:'Password',exact:true}).fill(secret('campusdesk','campusdesk-grafana'));
  await page.getByRole('button',{name:'Log in',exact:true}).click();
  await page.waitForURL(url=>!url.pathname.startsWith('/login'));
  await page.goto('http://localhost:3001/d/campusdesk?orgId=1&from=now-30m&to=now&refresh=10s');
  await page.getByText('Healthy backend replicas',{exact:true}).waitFor();
  await page.waitForFunction(()=>document.querySelectorAll('canvas').length>0);
  await hold(8000);
  await report('Next required evidence','The local application and DevOps workflow have been demonstrated.\n\nThe final course video still needs:\n- Real AWS Terraform plan/apply and VPC/EKS console proof\n- Real destroy completion after evaluation\n- The student\'s narrated explanation and a live commit-to-deployment walkthrough\n\nSee SUBMISSION.md for the current evidence checklist.',6000);
  console.log('Recorded live CI page, Argo CD, Prometheus and Grafana.');
} finally { await context.close(); await browser.close(); }
const raw=await video.path();
const ffmpeg=execFileSync(path.join(root,'.venv/Scripts/python.exe'),['-c','import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())'],{encoding:'utf8'}).trim();
execFileSync(ffmpeg,['-y','-i',raw,'-c:v','libx264','-preset','fast','-crf','27','-pix_fmt','yuv420p','-movflags','+faststart',path.join(root,'demo/local-walkthrough.mp4')],{stdio:'ignore'});
console.log('Created demo/local-walkthrough.mp4');
