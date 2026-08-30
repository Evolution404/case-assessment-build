#!/usr/bin/env node
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url))),modules=process.env.NODE_MODULES;
if(!modules)throw new Error('NODE_MODULES is required');
const {chromium}=await import(pathToFileURL(path.join(modules,'playwright/index.mjs')).href);
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
try{
 const page=await browser.newPage({viewport:{width:1280,height:720}});await page.goto(pathToFileURL(path.join(root,'dist/课题答辩-从人海作业到数智协同.html')).href,{waitUntil:'load'});await page.waitForFunction(()=>document.documentElement.dataset.ready==='1');
 if(await page.locator('.slide').count()!==15)throw new Error('slide count');await page.keyboard.press('ArrowRight');if(await page.locator('.slide.active').getAttribute('data-no')!=='02')throw new Error('keyboard');
 await page.evaluate(()=>show(6));await page.locator('[data-mode="bird"]').click();if(await page.locator('#mapTitle').textContent()!=='防鸟重点区域')throw new Error('map tab');
 await page.evaluate(()=>show(10));await page.locator('[data-pair="3"]').click();await page.locator('#compareSlider').fill('72');if(await page.locator('#divider').evaluate(el=>el.style.left)!=='72%')throw new Error('photo slider');
 console.log('[interactive] keyboard, map tabs and photo comparator passed');
}finally{await browser.close()}
