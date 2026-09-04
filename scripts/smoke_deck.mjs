#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const modules=process.env.NODE_MODULES;
if(!modules)throw new Error('NODE_MODULES is required');
const {chromium}=await import(pathToFileURL(path.join(modules,'playwright/index.mjs')).href);
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
try{
  const deckUrl=pathToFileURL(path.join(root,'dist/课题答辩-从人海作业到数智协同.html')).href;
  const page=await browser.newPage({viewport:{width:1280,height:720}});
  await page.goto(deckUrl,{waitUntil:'load'});
  await page.waitForFunction(()=>document.documentElement.dataset.ready==='1');
  if(await page.locator('.slide').count()!==13)throw new Error('slide count');
  if(await page.locator('.slide-no').count()!==13)throw new Error('slide number count');
  const structure=await page.locator('.slide .kicker').allTextContents();
  const expectedStructure=['个人案例答辩','管理矛盾','核心判断','增效｜任务筛选','增效｜三类专项','增效｜效率提升','提质｜案件入口','提质｜发现疑点','提质｜原图对照','提质｜算法识别','提质｜省级管理应用','机制沉淀','结论'];
  if(JSON.stringify(structure)!==JSON.stringify(expectedStructure))throw new Error(`presentation structure: ${JSON.stringify(structure)}`);
  const slideTopRules=await page.locator('.slide').evaluateAll(nodes=>nodes.map(node=>({before:getComputedStyle(node,'::before').content,after:getComputedStyle(node,'::after').content})));
  if(slideTopRules.some(rule=>!['none','normal'].includes(rule.before)||!['none','normal'].includes(rule.after)))throw new Error(`slide top rules returned: ${JSON.stringify(slideTopRules)}`);
  const directPage=await browser.newPage({viewport:{width:1280,height:720}});
  await directPage.goto(`${deckUrl}?=5`,{waitUntil:'load'});
  await directPage.waitForFunction(()=>document.documentElement.dataset.ready==='1');
  if(await directPage.locator('.slide.active').getAttribute('data-no')!=='05')throw new Error('direct page parameter ?=5');
  await directPage.goto(`${deckUrl}?p=5`,{waitUntil:'load'});
  await directPage.waitForFunction(()=>document.documentElement.dataset.ready==='1');
  if(await directPage.locator('.slide.active').getAttribute('data-no')!=='05')throw new Error('direct page parameter ?p=5');
  await directPage.goto(`${deckUrl}?=14`,{waitUntil:'load'});
  await directPage.waitForFunction(()=>document.documentElement.dataset.ready==='1');
  if(await directPage.locator('.slide.active').getAttribute('data-no')!=='01')throw new Error('out-of-range page parameter fallback');
  await directPage.close();
  if(await page.locator('.nav,.hint,.hud,#prev,#next').count())throw new Error('removed presentation controls returned');
  if(await page.locator('.pressure-x,.confluence-field,.people-cloud,.flow-map,.coordination-core,.signal-line').count())throw new Error('discarded cover composition returned');
  if(await page.locator('.evidence-field').count()!==1||await page.locator('.evidence-node').count()!==2||await page.locator('.evidence-core').count()!==1)throw new Error('restored cover evidence structure');
  const coverMotion=await page.locator('.evidence-core').evaluate(el=>getComputedStyle(el).animationName);
  if(coverMotion==='none')throw new Error('cover evidence animation');
  const coverAlignment=await page.evaluate(()=>{const core=document.querySelector('.evidence-core').getBoundingClientRect(),quality=document.querySelector('.evidence-node.q').getBoundingClientRect(),h=document.querySelector('.evidence-axis.h').getBoundingClientRect(),v=document.querySelector('.evidence-axis.v').getBoundingClientRect();return{dx:Math.abs(core.left+core.width/2-(v.left+v.width/2)),dy:Math.abs(core.top+core.height/2-(h.top+h.height/2)),qualityGap:quality.top-core.bottom}});
  if(coverAlignment.dx>1||coverAlignment.dy>1||coverAlignment.qualityGap<28)throw new Error(`cover alignment: ${JSON.stringify(coverAlignment)}`);
  const bannedCrossStructure=await page.locator('.slide').evaluateAll(nodes=>nodes.some(node=>node.textContent.includes('×')||/\s[xX]\s/.test(node.textContent)));
  if(bannedCrossStructure)throw new Error('deck contains banned A x B structure');
  await page.setViewportSize({width:1600,height:1000});
  await page.waitForTimeout(80);
  const letterbox=await page.evaluate(()=>{
    const slide=getComputedStyle(document.querySelector('.slide.active')).backgroundColor;
    const body=getComputedStyle(document.body).backgroundColor;
    const html=getComputedStyle(document.documentElement).backgroundColor;
    const rect=document.getElementById('stage').getBoundingClientRect();
    return {slide,body,html,top:rect.top,bottom:innerHeight-rect.bottom};
  });
  if(letterbox.body!==letterbox.slide||letterbox.html!==letterbox.slide||letterbox.top<1||letterbox.bottom<1){
    throw new Error(`fullscreen letterbox mismatch: ${JSON.stringify(letterbox)}`);
  }
  await page.setViewportSize({width:1280,height:720});
  const assertNoDecorativeEnglish=async(label,locator=page.locator('body'))=>{
    const visible=await locator.innerText();
    const hits=visible.match(/\b[A-Za-z]{2,}(?:[ \t/&-]+[A-Za-z]{2,})+\b/g)||[];
    if(hits.length)throw new Error(`${label} decorative English: ${hits.join(' | ')}`);
  };
  const assertNoProductionNotes=async(label,locator=page.locator('body'))=>{
    const visible=await locator.innerText();
    const forbidden=['原演示','交互保留','完整保留','点击右上角关闭','仅展示','不涉及具体单位','按要求','根据要求','用户要求','制作说明','验收口径','脱敏'];
    const hits=forbidden.filter(term=>visible.includes(term));
    if(hits.length)throw new Error(`${label} production notes leaked into presentation: ${hits.join(' | ')}`);
  };
  const internalFacingPhrases=['本人行动','演示证据','实际结果','责任边界','规模扩展','统计层级不同','照片关系层','管理问题层','管理变化：','实践一：','实践二：'];
  for(let index=0;index<13;index++){
    await page.evaluate(i=>show(i),index);
    await page.waitForTimeout(24);
    const active=page.locator('.slide.active');
    const negativeMetrics=await active.locator('[data-metric]').evaluateAll(nodes=>nodes.map(node=>node.textContent.trim()).filter(value=>/^\s*-/.test(value)));
    if(negativeMetrics.length)throw new Error(`slide ${index+1} metric animation emitted negative value: ${negativeMetrics.join(' | ')}`);
    const slideCopy=await active.innerText();
    const leaked=internalFacingPhrases.filter(term=>slideCopy.includes(term));
    if(leaked.length)throw new Error(`slide ${index+1} contains internal-facing presentation wording: ${leaked.join(' | ')}`);
    const standaloneInternalLabels=await active.locator('*').evaluateAll(nodes=>nodes.filter(el=>{const text=(el.textContent||'').trim();return text==='问题'||text==='本人行动';}).map(el=>({tag:el.tagName,cls:el.className,text:el.textContent.trim()})));
    if(standaloneInternalLabels.length)throw new Error(`slide ${index+1} contains internal-only labels: ${JSON.stringify(standaloneInternalLabels)}`);
    const tooSmall=await active.locator('*').evaluateAll(nodes=>nodes.filter(el=>{
      const cs=getComputedStyle(el),r=el.getBoundingClientRect();
      if(cs.display==='none'||cs.visibility==='hidden'||Number(cs.opacity)===0||r.width<=0||r.height<=0)return false;
      const direct=[...el.childNodes].some(node=>node.nodeType===Node.TEXT_NODE&&node.textContent.trim());
      return direct&&parseFloat(cs.fontSize)<16;
    }).map(el=>({tag:el.tagName,cls:el.className,text:(el.textContent||'').trim().slice(0,48),font:getComputedStyle(el).fontSize})));
    if(tooSmall.length)throw new Error(`slide ${index+1} contains text below 16px: ${JSON.stringify(tooSmall)}`);
    await assertNoDecorativeEnglish(`slide ${index+1}`);
    await assertNoProductionNotes(`slide ${index+1}`,active);
  }

  // Regression guards for the reviewed presentation pages.
  await page.evaluate(()=>show(2));
  const judgementAlignment=await page.evaluate(()=>{
    const sides=[...document.querySelectorAll('[data-no="03"] .thesis-side')].map(el=>el.getBoundingClientRect());
    const contributions=[...document.querySelectorAll('[data-no="03"] .contribution-strip > div')].map(el=>el.getBoundingClientRect());
    return {
      sideTopDelta:Math.abs(sides[0].top-sides[1].top),
      sideWidthDelta:Math.abs(sides[0].width-sides[1].width),
      contributionWidthSpread:Math.max(...contributions.map(x=>x.width))-Math.min(...contributions.map(x=>x.width))
    };
  });
  if(judgementAlignment.sideTopDelta>1||judgementAlignment.sideWidthDelta>1||judgementAlignment.contributionWidthSpread>1){
    throw new Error(`slide 03 alignment: ${JSON.stringify(judgementAlignment)}`);
  }

  await page.evaluate(()=>show(3));
  if(await page.locator('[data-no="04"] .footer-note').count())throw new Error('slide 04 confusing footer returned');
  if(await page.locator('[data-no="04"] .practice-panel').count()!==2)throw new Error('slide 04 task-screening panels missing');
  if(await page.locator('[data-no="04"] .rule-row').count()!==3)throw new Error('slide 04 three spatial rules missing');
  const spatialLabels=await page.locator('[data-no="04"] .rule-row .shape').allTextContents();
  const spatialNames=await page.locator('[data-no="04"] .rule-row b').allTextContents();
  if(JSON.stringify(spatialLabels)!==JSON.stringify(['点','线','面']))throw new Error(`slide 04 spatial classification must be point-line-area: ${JSON.stringify(spatialLabels)}`);
  if(JSON.stringify(spatialNames)!==JSON.stringify(['集中燃放点','交叉跨越','防鸟重点区域']))throw new Error(`slide 04 spatial mapping mismatch: ${JSON.stringify(spatialNames)}`);
  const slide04Text=await page.locator('[data-no="04"]').innerText();
  for(const forbidden of ['线—线','点—距','面—线'])if(slide04Text.includes(forbidden))throw new Error(`slide 04 forbidden technical relation promoted to classification: ${forbidden}`);

  await page.evaluate(()=>show(4));
  const launcherState=await page.evaluate(()=>({
    usesMapFinals:[...document.querySelectorAll('[data-no="05"] [data-scene]')].every(img=>img.src===DEMOS.printMaps[img.dataset.scene]),
    focusAnimation:getComputedStyle(document.querySelector('[data-no="05"] .demo-launch.is-selected .scan')).animationName,
    launcherCount:document.querySelectorAll('[data-no="05"] .demo-launch').length,
    forbiddenLabel:Object.values(DEMOS.maps).some(payload=>new TextDecoder().decode(Uint8Array.from(atob(payload),c=>c.charCodeAt(0))).includes('脱敏'))
  }));
  if(!launcherState.usesMapFinals||launcherState.launcherCount!==3||launcherState.focusAnimation==='none'||launcherState.forbiddenLabel){
    throw new Error(`slide 05 launcher regression: ${JSON.stringify(launcherState)}`);
  }

  const assertGrowingIntegers=async(index,selector,label)=>{
    await page.evaluate(i=>show(i),index);
    await page.waitForTimeout(90);
    const first=await page.locator(selector).evaluateAll(nodes=>nodes.map(node=>node.textContent.trim()));
    await page.waitForTimeout(240);
    const second=await page.locator(selector).evaluateAll(nodes=>nodes.map(node=>node.textContent.trim()));
    const toNumber=value=>Number(value.replace(/[^0-9]/g,''));
    if(first.some(value=>value.includes('.'))||second.some(value=>value.includes('.')))throw new Error(`${label} integer animation emitted decimals`);
    if(first.some((value,i)=>toNumber(second[i])<toNumber(value)))throw new Error(`${label} number animation decreased`);
  };
  await assertGrowingIntegers(5,'[data-no="06"] [data-metric]','slide 06');
  await assertGrowingIntegers(9,'[data-no="10"] [data-format="comma"]','slide 10');
  const photoPreview=await page.evaluate(()=>({
    figures:document.querySelectorAll('[data-no="08"] .evidence-photo-pair figure').length,
    imgs:document.querySelectorAll('[data-no="08"] .evidence-photo-pair img').length,
    allImgs:document.querySelectorAll('[data-no="08"] img').length,
    noExtraPanels:document.querySelectorAll('[data-no="08"] .quality-evidence,[data-no="08"] .photo-list,[data-no="08"] .photo-pair-item,[data-no="08"] .print-photo-proof').length===0,
    noWorkbenchTrigger:document.querySelectorAll('[data-no="08"] [data-open-photo],[data-no="08"] .workbench-launch,[data-no="08"] .open-label').length===0,
    filters:[...document.querySelectorAll('[data-no="08"] .evidence-photo-pair img')].map(img=>getComputedStyle(img).filter),
    title:document.querySelector('[data-no="08"] h2')?.textContent||''
  }));
  const zoomProof=await page.evaluate(()=>({boxes:document.querySelectorAll('[data-no="08"] .zoom-box,[data-no="08"] .order-zoom-box').length,marks:document.querySelectorAll('[data-no="08"] .zoom-mark,[data-no="08"] .order-zoom-mark').length}));
  if(photoPreview.figures!==2||photoPreview.imgs!==2||photoPreview.allImgs!==2||!photoPreview.noExtraPanels||!photoPreview.noWorkbenchTrigger||photoPreview.filters.some(filter=>filter!=='none')||!photoPreview.title.includes('相隔3天')||zoomProof.boxes!==0||zoomProof.marks!==0)throw new Error(`slide 08 must remain plain two-photo evidence without magnifier: ${JSON.stringify({photoPreview,zoomProof})}`);
  const caseEntry=await page.locator('[data-no="07"]').innerText();
  if(!caseEntry.includes('已完成')||!caseEntry.includes('照片已上传')||!caseEntry.includes('真的履职到位了吗')||caseEntry.includes('pHash')||caseEntry.includes('CLIP'))throw new Error(`slide 07 must be a non-algorithmic case entry: ${caseEntry}`);
  await page.waitForTimeout(520);
  const orderProof=await page.evaluate(()=>({
    figures:document.querySelectorAll('[data-no="09"] .workorder-photo-pair figure').length,
    imgs:document.querySelectorAll('[data-no="09"] .workorder-photo-pair img').length,
    triggers:document.querySelectorAll('[data-no="09"] [data-open-photo],[data-no="09"] .workbench-launch').length,
    text:document.querySelector('[data-no="09"]')?.innerText||'',
    srcs:[...document.querySelectorAll('[data-no="09"] .workorder-photo-pair img')].map(img=>img.src.slice(0,24)),
    zoomBoxes:document.querySelectorAll('[data-no="09"] .order-zoom-box').length,
    zoomMarks:document.querySelectorAll('[data-no="09"] .order-zoom-mark').length,
    zoomBackgrounds:[...document.querySelectorAll('[data-no="09"] .order-zoom-box')].map(el=>getComputedStyle(el).backgroundImage)
  }));
  if(orderProof.figures!==2||orderProof.imgs!==2||orderProof.triggers!==0||orderProof.zoomBoxes!==2||orderProof.zoomMarks!==2||orderProof.zoomBackgrounds.some(bg=>!bg.startsWith('url("data:image/webp;base64,'))||!orderProof.text.includes('5月22日有伞')||!orderProof.text.includes('5月25日无伞')||!orderProof.text.includes('规避人工审查')||!orderProof.srcs.every(src=>src.startsWith('data:image/webp;base64,')))throw new Error(`slide 09 must be static workorder-photo explanation with local magnifier: ${JSON.stringify(orderProof)}`);
  const slide10Text=await page.locator('[data-no="10"]').innerText();
  const slide10Expected=await page.evaluate(()=>({c:Number(CASE.metrics.alarm_candidates).toLocaleString('zh-CN'),d:Number(CASE.metrics.alarm_confirmed_pairs).toLocaleString('zh-CN')}));
  if(!slide10Text.includes('直接两两比较')||!slide10Text.includes('77.5万亿')||!slide10Text.includes('感知哈希')||!slide10Text.includes('语义特征')||!slide10Text.includes('系统候选')||!slide10Text.includes(slide10Expected.c)||!slide10Text.includes('核查确认重复')||!slide10Text.includes(slide10Expected.d)||!slide10Text.includes('进入照片查重工作台'))throw new Error(`slide 10 algorithm-to-effect-to-workbench chain missing: ${slide10Text}`);
  if(await page.locator('[data-no="10"] [data-open-photo]').count()!==1)throw new Error('slide 10 must contain exactly one workbench launch after algorithm/effect');
  if(slide10Text.includes('4,630')||slide10Text.includes('已人工复核')||await page.locator('[data-no="10"] [data-metric="alarm_reviewed"]').count())throw new Error(`slide 10 exposes forbidden intermediate review volume: ${slide10Text}`);
  const darkPanels=await page.locator('[data-no="07"] .human-boundary,[data-no="10"] .algorithm-method,[data-no="10"] .recognition-effect').evaluateAll(nodes=>nodes.map(el=>{
    const bg=getComputedStyle(el).backgroundColor,match=bg.match(/rgba?\(([^)]+)\)/);if(!match)return{cls:el.className,bg,dark:false};
    const values=match[1].split(',').map(x=>Number(x.trim())),[r,g,b,a=1]=values;
    return{cls:el.className,bg,dark:a>=.7&&Math.max(r,g,b)<180};
  }).filter(x=>x.dark));
  if(darkPanels.length)throw new Error(`large dark presentation panels are forbidden: ${JSON.stringify(darkPanels)}`);

  await page.evaluate(()=>show(10));
  await page.waitForTimeout(820);
  if((await page.locator('[data-no="11"]').innerText()).includes('只展示省级汇总，不涉及具体单位'))throw new Error('slide 11 deleted qualifier returned');
  if(await page.locator('[data-no="11"] .convergence-lines').count())throw new Error('slide 11 meaningless lines returned');
  if(await page.locator('[data-no="11"] .level-card').count()!==2)throw new Error('slide 11 result cards missing');
  const hierarchyText=await page.locator('[data-no="11"]').innerText();
  if(!hierarchyText.includes('348')||!hierarchyText.includes('55,411')||!hierarchyText.includes('19')||!hierarchyText.includes('查重结果经核查后进入管理通报'))throw new Error(`slide 11 business result chain missing: ${hierarchyText}`);
  if(hierarchyText.includes('77.5万亿'))throw new Error(`slide 11 must not show algorithm complexity value: ${hierarchyText}`);
  const unitScale=await page.evaluate(()=>{
    const total=document.querySelector('[data-no="11"] .issue-total');
    return {number:parseFloat(getComputedStyle(total.querySelector('b')).fontSize),unit:parseFloat(getComputedStyle(total.querySelector('em')).fontSize)};
  });
  if(unitScale.number<=unitScale.unit*3)throw new Error(`slide 11 number/unit hierarchy: ${JSON.stringify(unitScale)}`);

  await page.evaluate(()=>show(11));
  if(await page.locator('[data-no="12"] .method-row').count()!==2)throw new Error('slide 12 mirrored method rows missing');
  const methodColumns=await page.locator('[data-no="12"] .method-row').evaluateAll(rows=>rows.map(row=>[...row.children].map(el=>el.getBoundingClientRect().width)));
  if(methodColumns.some(row=>row.length!==6))throw new Error(`slide 11 method columns: ${JSON.stringify(methodColumns)}`);
  for(let i=0;i<6;i++){if(Math.abs(methodColumns[0][i]-methodColumns[1][i])>1)throw new Error(`slide 11 mirrored column ${i} width mismatch: ${JSON.stringify(methodColumns)}`);}

  const visualDir=path.join(root,'.build/defense-visual');
  fs.rmSync(visualDir,{recursive:true,force:true});
  fs.mkdirSync(visualDir,{recursive:true});
  const visualSelectors='h1,h2,h3,p,b,strong,em,.metric,.label,.small,.kicker,.slide-no,.practice-grid,.demo-launchers,.duration-compare,.impact-strip,.photo-launch-layout,.evidence-photo-pair,.workorder-photo-pair,.workorder-explain,.filter-layout,.scale-layout,.level-layout,.mirror-method,.shared-principle,.replication-route,.closing-copy';
  for(let index=0;index<13;index++){
    await page.evaluate(i=>show(i),index);
    await page.waitForTimeout(90);
    const visual=await page.locator('.slide.active').evaluate((slide,selectors)=>{
      const sr=slide.getBoundingClientRect();
      const visible=el=>{const cs=getComputedStyle(el);const r=el.getBoundingClientRect();return cs.display!=='none'&&cs.visibility!=='hidden'&&Number(cs.opacity)!==0&&r.width>0&&r.height>0};
      const overflow=[...slide.querySelectorAll(selectors)].filter(visible).filter(el=>{const r=el.getBoundingClientRect();return r.left<sr.left-1||r.right>sr.right+1||r.top<sr.top-1||r.bottom>sr.bottom+1}).map(el=>({tag:el.tagName,cls:el.className,text:(el.textContent||'').trim().slice(0,42),rect:[el.getBoundingClientRect().left,el.getBoundingClientRect().top,el.getBoundingClientRect().right,el.getBoundingClientRect().bottom]}));
      const clipped=[...slide.querySelectorAll('.practice-panel,.rule-matrix,.demo-launch,.contact-sheet,.photo-stage,.human-boundary,.scale-claim,.collapse-field,.workorder-photo-pair,.level-layout,.mirror-method,.closing-copy')].filter(visible).filter(el=>{const cs=getComputedStyle(el);const overflowMode=cs.overflow+cs.overflowX+cs.overflowY;return /(hidden|clip)/.test(overflowMode)&&(el.scrollWidth>el.clientWidth+2||el.scrollHeight>el.clientHeight+2)}).map(el=>({tag:el.tagName,cls:el.className,text:(el.textContent||'').trim().slice(0,42),scroll:[el.scrollWidth,el.scrollHeight],client:[el.clientWidth,el.clientHeight]}));
      return {overflow,clipped,slideScroll:[slide.scrollWidth,slide.scrollHeight],slideClient:[slide.clientWidth,slide.clientHeight]};
    },visualSelectors);
    if(visual.overflow.length||visual.clipped.length||visual.slideScroll[0]>visual.slideClient[0]+2||visual.slideScroll[1]>visual.slideClient[1]+2)throw new Error(`slide ${index+1} visual overflow: ${JSON.stringify(visual)}`);
    const shot=path.join(visualDir,`slide-${String(index+1).padStart(2,'0')}.png`);
    await page.locator('.slide.active').screenshot({path:shot,animations:'disabled'});
    if(fs.statSync(shot).size<12000)throw new Error(`slide ${index+1} visual screenshot unexpectedly small`);
  }
  console.log(`[visual] 13 rendered slides passed overflow/clipping checks -> ${visualDir}`);

  await page.evaluate(()=>show(0));
  await page.keyboard.press('ArrowRight');
  await page.waitForFunction(()=>document.querySelector('.slide.active')?.dataset.no==='02');

  await page.evaluate(()=>show(4));
  await page.locator('[data-demo="bird"]').click();
  await page.waitForSelector('#ovContent iframe');
  const frame=page.frames().at(-1);
  await frame.waitForSelector('canvas#map');
  if((await frame.title())!=='防鸟重点区域')throw new Error('original bird map not loaded');
  if((await frame.locator('body').innerText()).includes('脱敏'))throw new Error('bird map contains forbidden privacy wording');
  const birdGeometry=await frame.evaluate(()=>{
    const {minX,maxX,minY,maxY}=window.FN_DATA.bbox;
    const points=window.FN_DATA.hulls.flatMap(hull=>hull.polys.flat());
    return {points:points.length,outside:points.filter(([x,y])=>x<minX||x>maxX||y<minY||y>maxY).length};
  });
  if(!birdGeometry.points||birdGeometry.outside)throw new Error(`bird-area geometry outside map: ${JSON.stringify(birdGeometry)}`);
  await frame.waitForTimeout(120);
  const birdBefore=await frame.locator('canvas#map').evaluate(canvas=>canvas.toDataURL());
  await frame.locator('[data-c="0"]').check();
  await frame.waitForTimeout(120);
  const birdAfter=await frame.locator('canvas#map').evaluate(canvas=>canvas.toDataURL());
  if(birdBefore===birdAfter)throw new Error('bird-area layer toggle did not redraw the map');
  await assertNoDecorativeEnglish('bird map',frame.locator('body'));
  await assertNoProductionNotes('bird map',frame.locator('body'));
  const closeAlignment=await page.locator('#ovClose').evaluate(button=>{
    const glyph=button.querySelector('.close-glyph').getBoundingClientRect(),box=button.getBoundingClientRect(),style=getComputedStyle(button);
    return {
      dx:Math.abs(box.left+box.width/2-(glyph.left+glyph.width/2)),
      dy:Math.abs(box.top+box.height/2-(glyph.top+glyph.height/2)),
      square:Math.abs(box.width-box.height),
      radius:parseFloat(style.borderRadius),
      width:box.width
    };
  });
  if(closeAlignment.dx>.5||closeAlignment.dy>.5||closeAlignment.square>.5||closeAlignment.radius<closeAlignment.width/2-1){
    throw new Error(`overlay close alignment: ${JSON.stringify(closeAlignment)}`);
  }
  await page.locator('#ovClose').click();
  await page.waitForFunction(()=>!document.getElementById('overlay').classList.contains('open'));

  await page.evaluate(()=>show(9));
  await page.locator('[data-no="10"] [data-open-photo]').click();
  await assertNoDecorativeEnglish('photo workbench');
  await assertNoProductionNotes('photo workbench');
  const workbenchText=await page.locator('#ovContent').innerText();
  if(workbenchText.includes('4,630')||workbenchText.includes('已复核')||workbenchText.includes('人工复核量'))throw new Error(`photo workbench exposes forbidden intermediate review volume: ${workbenchText}`);
  if(!workbenchText.includes('系统候选')||!workbenchText.includes('5,472')||!workbenchText.includes('核查确认重复')||!workbenchText.includes('348'))throw new Error(`photo workbench missing candidate-to-confirmed result chain: ${workbenchText}`);
  const smallWorkbenchText=await page.locator('#ovContent *').evaluateAll(nodes=>nodes.filter(el=>{
    const cs=getComputedStyle(el),r=el.getBoundingClientRect();
    if(cs.display==='none'||cs.visibility==='hidden'||Number(cs.opacity)===0||r.width<=0||r.height<=0||el.classList.contains('handle'))return false;
    const direct=[...el.childNodes].some(node=>node.nodeType===Node.TEXT_NODE&&node.textContent.trim());
    return direct&&parseFloat(cs.fontSize)<16;
  }).map(el=>({tag:el.tagName,cls:el.className,text:(el.textContent||'').trim().slice(0,48),font:getComputedStyle(el).fontSize})));
  if(smallWorkbenchText.length)throw new Error(`photo workbench contains text below 16px: ${JSON.stringify(smallWorkbenchText)}`);
  const extraPair=await page.evaluate(()=>DEMOS.pairs.at(0));
  if(extraPair.id!=='S11'||extraPair.phash!==6||Math.abs(extraPair.clip-0.956655)>1e-9||!extraPair.p1src.startsWith('data:image/webp;base64,')||!extraPair.p2src.startsWith('data:image/webp;base64,'))throw new Error(`reference-material first pair mismatch: ${JSON.stringify({id:extraPair.id,phash:extraPair.phash,clip:extraPair.clip,p1:extraPair.p1src.slice(0,24),p2:extraPair.p2src.slice(0,24)})}`);
  if(!(await page.locator('#photoCaption').innerText()).includes('0.9567'))throw new Error('reference-material first pair is not default');
  await page.locator('#photoList [data-photo-index="3"]').click();
  await page.locator('[data-photo-mode="slider"]').click();
  const listViewport=await page.evaluate(()=>{
    const list=document.getElementById('photoList').getBoundingClientRect(),side=document.querySelector('.photo-side').getBoundingClientRect();
    const el=document.getElementById('photoList');
    return {bottomGap:Math.abs(side.bottom-list.bottom),height:list.height,scrollHeight:el.scrollHeight,clientHeight:el.clientHeight,sideOverflow:getComputedStyle(document.querySelector('.photo-side')).overflowY};
  });
  if(listViewport.bottomGap>1||listViewport.scrollHeight<=listViewport.clientHeight||listViewport.sideOverflow!=='hidden')throw new Error(`photo list should fill remaining sidebar and scroll: ${JSON.stringify(listViewport)}`);
  await page.setViewportSize({width:1280,height:1000});
  await page.waitForTimeout(80);
  const tallList=await page.evaluate(()=>{const list=document.getElementById('photoList').getBoundingClientRect(),side=document.querySelector('.photo-side').getBoundingClientRect();return{height:list.height,bottomGap:Math.abs(side.bottom-list.bottom)}});
  if(tallList.height<listViewport.height+100||tallList.bottomGap>1)throw new Error(`photo list should expand with available height: base=${JSON.stringify(listViewport)}, tall=${JSON.stringify(tallList)}`);
  await page.setViewportSize({width:1280,height:720});
  const stage=page.locator('#photoStage');
  await stage.click({position:{x:560,y:180}});
  const left=await page.locator('#photoSlider').evaluate(el=>parseFloat(el.style.left));
  if(!(left>55))throw new Error('photo slider');
  const photoPairCount=await page.locator('#photoList [data-photo-index]').count();
  if(photoPairCount!==11)throw new Error(`photo pair count: ${photoPairCount}`);
  const handleAnim=await page.locator('#photoSlider .handle').evaluate(el=>getComputedStyle(el).animationName);
  if(handleAnim==='none')throw new Error('slider loop animation');
  await page.keyboard.press('Escape');

  await page.keyboard.press('p');
  if(!await page.locator('#presenter').evaluate(el=>el.classList.contains('open')))throw new Error('presenter mode');
  if(!(await page.locator('#presenterTitle').textContent())?.includes('用算法从海量照片中筛出可核查线索'))throw new Error('presenter notes sync');
  await assertNoDecorativeEnglish('presenter mode');
  await assertNoProductionNotes('presenter mode');
  console.log('[interactive] navigation, centered map previews, bird-area layers, original photos, slider loop and presenter mode passed');
}finally{
  await browser.close();
}
