#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const html=path.join(root,'dist/课题答辩-从人海作业到数智协同.html');
const output=path.join(root,'dist/课题答辩-从人海作业到数智协同.pdf');
const modules=process.env.NODE_MODULES;
if(!modules)throw new Error('NODE_MODULES is required');
const {chromium}=await import(pathToFileURL(path.join(modules,'playwright/index.mjs')).href);
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
try{
  const page=await browser.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});
  await page.goto(`${pathToFileURL(html).href}?print=1`,{waitUntil:'load'});
  await page.emulateMedia({media:'print'});
  await page.waitForFunction(()=>document.documentElement.dataset.ready==='1');
  await page.pdf({path:output,width:'1280px',height:'720px',printBackground:true,preferCSSPageSize:true,tagged:true,outline:false,margin:{top:'0',right:'0',bottom:'0',left:'0'}});
  console.log(`[pdf] 15 pages -> ${output}`);
}finally{await browser.close()}
