import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve('../..');
const password=process.env.SEED_PASSWORD??fs.readFileSync(path.join(root,'.env'),'utf8').split(/\r?\n/).find(l=>l.startsWith('SEED_PASSWORD='))!.slice(14);

test('design library uploads a reference and persists project selection',async({page})=>{
 await page.goto('/');
 await page.getByLabel('계정',{exact:true}).fill('demo-user');
 await page.getByLabel('비밀번호',{exact:true}).fill(password);
 await page.getByRole('button',{name:'로그인 →'}).click();
 await page.getByLabel('프로젝트 이름',{exact:true}).fill(`Synthetic design UI ${Date.now()}`);
 await page.getByRole('button',{name:'만들기',exact:true}).click();
 await page.getByRole('button',{name:'◈ 디자인 참고실',exact:true}).click();
 await expect(page.locator('.theme-card').first()).toBeVisible();
 expect(await page.locator('.theme-card').count()).toBeGreaterThanOrEqual(22);
 await page.getByLabel('참고 PPT 업로드').setInputFiles(path.join(root,'test-results/design/synthetic-reference.pptx'));
 await expect(page.locator('.design-intro .job').first()).toContainText('작업 완료',{timeout:45000});
 const card=page.locator('.theme-card').filter({has:page.getByRole('heading',{name:'Warm Paper',exact:true})});
 await card.getByRole('button',{name:'이 디자인 사용'}).click();
 await expect(card.getByRole('button',{name:'사용 중'})).toBeVisible();
 await page.getByRole('button',{name:'▦ 프로젝트',exact:true}).click();
 await page.getByRole('button',{name:'◈ 디자인 참고실',exact:true}).click();
 await expect(card.getByRole('button',{name:'사용 중'})).toBeVisible();
 await page.screenshot({path:path.join(root,'test-results/design/library-browser.png'),fullPage:false});
});
