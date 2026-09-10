import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve('../..');
const password=process.env.SEED_PASSWORD??fs.readFileSync(path.join(root,'.env'),'utf8').split(/\r?\n/).find(l=>l.startsWith('SEED_PASSWORD='))!.slice(14);

test('prototype user generates and downloads real PPTX and MP4 without a reviewer',async({page})=>{
 test.setTimeout(240000);
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');
 await page.getByLabel('계정',{exact:true}).fill('demo-user');
 await page.getByLabel('비밀번호',{exact:true}).fill(password);
 await page.getByRole('button',{name:'로그인 →'}).click();
 await expect(page.getByText('프로토타입-검토패스 · 검토자 승인 없이',{exact:false})).toBeVisible();
 await page.getByLabel('프로젝트 이름',{exact:true}).fill(`Synthetic media ${Date.now()}`);
 await page.getByRole('button',{name:'만들기',exact:true}).click();
 await expect(page.getByLabel('검토자 선택')).toHaveCount(0);
 await page.locator('summary').filter({hasText:'프로젝트 설정'}).click();
 await page.getByLabel('프로젝트 설정 설명').fill('Synthetic browser settings and media acceptance');
 await page.getByLabel('프로젝트 보안등급').fill('synthetic-test');
 await page.getByRole('button',{name:'프로젝트 설정 저장'}).click();
 await expect(page.getByText('프로젝트 설정을 저장했습니다.')).toBeVisible();
 await page.getByLabel('문서 업로드').setInputFiles(path.join(root,'tests/golden/fixtures/synthetic.hwp'));
 const document=page.getByRole('button').filter({hasText:'synthetic.hwp'}).last();
 await expect(document).toContainText('보안검사 완료',{timeout:45000});
 await document.click();await page.getByRole('button',{name:'분석 시작',exact:true}).click();
 const generate=page.getByRole('button',{name:'PPTX + MP4 함께 생성',exact:true});
 await expect(generate).toBeEnabled({timeout:60000});
 await generate.click();
 const results:Record<string,number>={};
 for(const extension of ['pptx','mp4']) {
   const row=page.locator('.artifact-row').filter({has:page.locator('.file-type',{hasText:extension.toUpperCase()})});
   await expect(row).toContainText('QA PASS',{timeout:150000});
   const downloading=page.waitForEvent('download');
   await row.getByRole('button',{name:'다운로드 ↓'}).click();
   const download=await downloading;
   const filename=path.join(root,'test-results/samples',`prototype-browser.${extension}`);
   await download.saveAs(filename);results[extension]=fs.statSync(filename).size;
   expect(results[extension]).toBeGreaterThan(1000);
   if(extension==='mp4'){
     await row.getByRole('button',{name:'검토 / 이력'}).click();
     await expect.poll(()=>page.locator('video').evaluate((v:HTMLVideoElement)=>v.readyState),{timeout:15000}).toBeGreaterThanOrEqual(2);
     expect(await page.locator('video').evaluate((v:HTMLVideoElement)=>v.duration)).toBeGreaterThan(0);
     await page.getByRole('button',{name:'닫기 ×'}).click();
   }
 }
 expect(errors).toEqual([]);
 fs.writeFileSync(path.join(root,'test-results/prototype-generation.json'),JSON.stringify({status:'PASS',review_mode:'prototype-pass',reviewer_used:false,download_bytes:results,browser_video_decoded:true,synthetic_only:true},null,2));
});
