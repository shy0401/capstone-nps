import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'tests',timeout:120000,workers:1,reporter:[['list'],['junit',{outputFile:'../../test-results/browser.xml'}]],use:{baseURL:process.env.E2E_BASE_URL??'http://127.0.0.1:8080',headless:true,channel:process.platform==='win32'?'msedge':undefined,viewport:{width:1440,height:1000},screenshot:'only-on-failure'}});
