#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const source=path.join(root,'src/presentation.html');
const output=path.join(root,'dist/课题答辩-从人海作业到数智协同.html');
const caseData=JSON.parse(fs.readFileSync(path.join(root,'content/case.json'),'utf8'));
const demoData=JSON.parse(fs.readFileSync(path.join(root,'data/demo.json'),'utf8'));
caseData.case_id=process.env.CASE_ID||caseData.case_id_default;

function uri(name){
  const p=path.join(root,'assets/images',name);
  return `data:image/jpeg;base64,${fs.readFileSync(p).toString('base64')}`;
}
let html=fs.readFileSync(source,'utf8')
  .replace('__CASE_DATA__',JSON.stringify(caseData).replaceAll('<','\\u003c'))
  .replace('__DEMO_DATA__',JSON.stringify(demoData).replaceAll('<','\\u003c'));
for(let i=1;i<=4;i++)for(const side of ['a','b']){
  html=html.replace(`__PHOTO_${i}${side.toUpperCase()}__`,uri(`pair-${i}-${side}.jpg`));
}
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,html);
console.log(`[deck] 15 slides -> ${output} (${(fs.statSync(output).size/1024/1024).toFixed(2)} MiB)`);
