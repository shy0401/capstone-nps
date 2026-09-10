import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve('../..');
const password=process.env.SEED_PASSWORD??fs.readFileSync(path.join(root,'.env'),'utf8').split(/\r?\n/).find(l=>l.startsWith('SEED_PASSWORD='))!.slice(14);

test('HWP and reviewer membership without media generation',async({page})=>{
  const errors:string[]=[];
  const mediaRequests:string[]=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(/\/generate-(ppt|video|images)$/.test(r.url()))mediaRequests.push(r.url());});
  async function login(username:string){
    await page.getByLabel('계정',{exact:true}).fill(username);
    await page.getByLabel('비밀번호',{exact:true}).fill(password);
    await page.getByRole('button',{name:'로그인 →'}).click();
  }
  await page.goto('/');
  await login('demo-user');
  const projectName=`Synthetic HWP UI ${Date.now()}`;
  await page.getByLabel('프로젝트 이름',{exact:true}).fill(projectName);
  await page.getByRole('button',{name:'만들기',exact:true}).click();
  await page.getByLabel('검토자 선택').selectOption({label:'demo-reviewer'});
  await page.getByRole('button',{name:'검토자 추가',exact:true}).click();
  await expect(page.getByRole('status')).toContainText('검토자를 프로젝트에 추가');
  await page.getByLabel('문서 업로드').setInputFiles(path.join(root,'tests/golden/fixtures/synthetic.hwp'));
  const document=page.getByRole('button').filter({hasText:'synthetic.hwp'}).last();
  await expect(document).toContainText('보안검사 완료',{timeout:45000});
  await document.click();
  await page.getByRole('button',{name:'분석 시작',exact:true}).click();
  await expect(page.getByRole('button',{name:'계획 보기'})).toBeVisible({timeout:60000});
  await page.getByRole('button',{name:'계획 보기'}).click();
  await expect(page.getByText('HWP 본문과 표 안의 글자를 추출했습니다.',{exact:false})).toBeVisible();
  await expect(page.getByRole('button',{name:'PPTX 생성',exact:true})).toBeDisabled();
  await page.getByTitle('로그아웃').click();
  await login('demo-reviewer');
  await page.getByLabel('프로젝트 선택').selectOption({label:projectName});
  await page.getByRole('button').filter({hasText:'synthetic.hwp'}).last().click();
  await page.getByRole('button',{name:'계획 승인',exact:true}).click();
  await expect(page.getByRole('button',{name:'PPTX 생성',exact:true})).toBeEnabled();
  expect(mediaRequests).toEqual([]);
  expect(errors).toEqual([]);
});
