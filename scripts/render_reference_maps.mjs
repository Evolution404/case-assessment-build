#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const source=JSON.parse(fs.readFileSync(path.join(root,'data/reference_demos.json'),'utf8'));
const outputDir=path.join(root,'assets/images/reference-demos');
const modules=process.env.NODE_MODULES;
if(!modules)throw new Error('NODE_MODULES is required');
const {chromium}=await import(pathToFileURL(path.join(modules,'playwright/index.mjs')).href);
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
try{
  const page=await browser.newPage({viewport:{width:960,height:540},deviceScaleFactor:1});
  for(const key of ['rail','fireworks','bird']){
    const html=Buffer.from(source.maps[key],'base64').toString('utf8');
    await page.setContent(html,{waitUntil:'load'});
    if(key==='bird'){
      for(const selector of ['[data-c="0"]','[data-c="2"]','[data-c="3"]']){
        const control=page.locator(selector).first();
        if(await control.count()&&!await control.isChecked())await control.click();
      }
      for(const selector of ['.c.v220','.c.v110']){
        const control=page.locator(selector).first();
        if(await control.count())await control.click();
      }
    }
    await page.addStyleTag({content:'.panel,.stats,.legend,#tip{display:none!important}'});
    await page.waitForTimeout(450);
    await page.screenshot({path:path.join(outputDir,`map-${key}-print.jpg`),type:'jpeg',quality:86});
  }
}finally{
  await browser.close();
}
console.log(`[reference maps] print states -> ${outputDir}`);
