#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const source=path.join(root,'src/presentation.html');
const output=path.join(root,'dist/课题答辩-从人海作业到数智协同.html');
const caseData=JSON.parse(fs.readFileSync(path.join(root,'content/case.json'),'utf8'));
const defenseData=JSON.parse(fs.readFileSync(path.join(root,'content/defense.json'),'utf8'));
const referenceDemos=JSON.parse(fs.readFileSync(path.join(root,'data/reference_demos.json'),'utf8'));
const workorderZoom=JSON.parse(fs.readFileSync(path.join(root,'content/workorder_zoom.json'),'utf8'));
caseData.case_id=process.env.CASE_ID||caseData.case_id_default;

const m=caseData.metrics;
const speakerTokens={
  province_poles_wan1:`${(m.province_poles/10000).toFixed(1)}万`,
  province_lines_label:m.province_lines_report_label,
  alarm_photos_comma:m.alarm_photos.toLocaleString('zh-CN'),
  patrol_photos_wan0:`${Math.round(m.patrol_photos_monthly/10000)}万`,
  crossing_poles_comma:m.crossing_poles.toLocaleString('zh-CN'),
  crossing_lines:m.crossing_lines,
  crossing_records:m.crossing_existing_records,
  crossing_people:m.crossing_people_before,
  crossing_before:m.crossing_duration_before,
  crossing_after:m.crossing_duration_after,
  crossing_findings:m.crossing_additional_findings,
  fireworks_turnaround:m.fireworks_turnaround,
  alarm_candidates_comma:m.alarm_candidates.toLocaleString('zh-CN'),
  alarm_confirmed_comma:m.alarm_confirmed_pairs.toLocaleString('zh-CN'),
  alarm_different_comma:m.alarm_confirmed_different.toLocaleString('zh-CN'),
  alarm_pending_comma:m.alarm_pending.toLocaleString('zh-CN'),
  alarm_review_rate:`${m.alarm_candidate_hit_rate.toFixed(2)}%`,
  trial_total:m.province_trial_duplicate_issues,
  trial_alarm:m.province_trial_alarm_duplicate_issues,
  trial_patrol:m.province_trial_patrol_duplicate_issues,
  theoretical_pairs_wan_yi:`${(m.theoretical_pairs/1e12).toFixed(1)}万亿`,
  patrol_pairs_comma:m.patrol_duplicate_pairs.toLocaleString('zh-CN'),
  pairs_per_duplicate_yi:`${Math.round(m.pairs_per_duplicate/1e8)}亿`
};
for(const slide of defenseData.slides){
  slide.script=slide.script.replace(/\{\{([a-z0-9_]+)\}\}/g,(_match,key)=>String(speakerTokens[key]??`{{${key}}}`));
}

function uri(file){
  const p=path.isAbsolute(file)?file:path.join(root,file);
  const buffer=fs.readFileSync(p);
  let mime='image/jpeg';
  if(buffer.length>=12&&buffer.subarray(0,4).toString('ascii')==='RIFF'&&buffer.subarray(8,12).toString('ascii')==='WEBP')mime='image/webp';
  else if(buffer.length>=8&&buffer[0]===0x89&&buffer.subarray(1,4).toString('ascii')==='PNG')mime='image/png';
  else if(buffer.length>=2&&buffer[0]===0xff&&buffer[1]===0xd8)mime='image/jpeg';
  return `data:${mime};base64,${buffer.toString('base64')}`;
}
const referenceImageDir=path.join(root,'assets/images/reference-demos');
referenceDemos.pairs=referenceDemos.pairs.map(pair=>({
  ...pair,
  p1src:uri(path.join(referenceImageDir,pair.a)),
  p2src:uri(path.join(referenceImageDir,pair.b))
}));
referenceDemos.pairs.unshift({
  id:'S11',risk:'一般',yhlx:'线下钓鱼',watermark:'原始反馈照片',time:'原始画面',phash:6,clip:0.956655,
  sourcePair:269,sourceId:3213,
  p1src:uri(path.join(referenceImageDir,'feedback-0525.webp')),
  p2src:uri(path.join(referenceImageDir,'feedback-0522.webp'))
});
referenceDemos.orderProof={
  a:uri(path.join(referenceImageDir,'order-0522-workorder.webp')),
  b:uri(path.join(referenceImageDir,'order-0525-workorder.webp'))
};
referenceDemos.scenes={
  rail:uri(path.join(referenceImageDir,'scene-rail.jpg')),
  fireworks:uri(path.join(referenceImageDir,'scene-fireworks.jpg')),
  bird:uri(path.join(referenceImageDir,'scene-bird.jpg'))
};
referenceDemos.printMaps={
  rail:uri(path.join(referenceImageDir,'map-rail-print.jpg')),
  fireworks:uri(path.join(referenceImageDir,'map-fireworks-print.jpg')),
  bird:uri(path.join(referenceImageDir,'map-bird-print.jpg'))
};
let html=fs.readFileSync(source,'utf8')
  .replace('__CASE_DATA__',JSON.stringify(caseData).replaceAll('<','\\u003c'))
  .replace('__DEFENSE_DATA__',JSON.stringify(defenseData).replaceAll('<','\\u003c'))
  .replace('__REFERENCE_DEMOS__',JSON.stringify(referenceDemos).replaceAll('<','\\u003c'))
  .replace('__WORKORDER_ZOOM__',JSON.stringify(workorderZoom).replaceAll('<','\\u003c'));
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,html);
console.log(`[deck] ${defenseData.slides.length} slides -> ${output} (${(fs.statSync(output).size/1024/1024).toFixed(2)} MiB)`);
