#!/usr/bin/env node
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath,pathToFileURL} from 'node:url';
const {chromium}=await import(pathToFileURL(path.join(process.env.NODE_MODULES,'playwright/index.mjs')).href);
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));const build=path.join(root,'.build');const out=path.join(build,'visuals');fs.mkdirSync(out,{recursive:true});
const content=JSON.parse(fs.readFileSync(path.join(root,'content/case.json'),'utf8'));const demo=JSON.parse(fs.readFileSync(path.join(root,'data/demo.json'),'utf8'));
let html=fs.readFileSync(path.join(root,'src/visuals.html'),'utf8').replace('__CASE_DATA__',JSON.stringify(content).replaceAll('</','<\\/')).replace('__DEMO_DATA__',JSON.stringify(demo).replaceAll('</','<\\/'));
const built=path.join(build,'visuals.html');fs.writeFileSync(built,html);
const names=['dual-wheel','architecture','province-map','crossing','bird','fireworks','spatial-compare','dedup-funnel','photo-compare','scale','dedup-pipeline','outcomes'];
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});const page=await browser.newPage({viewport:{width:1200,height:675},deviceScaleFactor:2});
for(const name of names){await page.goto(pathToFileURL(built).href+'?v='+name,{waitUntil:'load'});await page.locator('#v-'+name).screenshot({path:path.join(out,name+'.png')});}
await browser.close();console.log(`[visuals] exported ${names.length} high-resolution figures`);
