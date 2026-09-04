#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath,pathToFileURL} from 'node:url';

const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const reference=path.resolve(root,'../../002授课考核/PDCA-Presentation-Build');
const sourceJs=path.join(reference,'data/big.js');
const output=path.join(root,'data/reference_demos.json');
const imageDir=path.join(root,'assets/images/reference-demos');
const modules=process.env.NODE_MODULES;
if(!modules)throw new Error('NODE_MODULES is required');
const {default:sharp}=await import(pathToFileURL(path.join(modules,'sharp/dist/index.mjs')).href);

const source=fs.readFileSync(sourceJs,'utf8');
const context={};
vm.createContext(context);
vm.runInContext(`${source};this.__export={EMBED_MAPS,PHOTO_PAIRS};`,context,{timeout:30000});
const {EMBED_MAPS,PHOTO_PAIRS}=context.__export;

const CITY_TOKENS=['南京','苏州','无锡','常州','镇江','扬州','泰州','南通','盐城','淮安','宿迁','徐州','连云港'];
const DISTRICT_TOKENS=['玄武区','秦淮区','建邺区','鼓楼区','浦口区','栖霞区','雨花台区','江宁区','六合区','溧水区','高淳区'];

function transformData(data){
  const {minX,maxX,minY,maxY}=data.bbox;
  const baseX=5600000,baseY=2300000;
  const tx=n=>Math.round((baseX+(n-minX)*0.82)/50)*50;
  const ty=n=>Math.round((baseY+(n-minY)*0.91)/50)*50;
  // Bird-area hulls use [x,y] point pairs rather than named x/y arrays.
  // Transform them explicitly so the filled regions stay aligned with the lines.
  (data.hulls||[]).forEach(hull=>{
    hull.polys=(hull.polys||[]).map(poly=>poly.map(point=>[tx(point[0]),ty(point[1])]));
  });
  const visit=(value,key='')=>{
    if(Array.isArray(value))return value.map(item=>visit(item,key));
    if(value&&typeof value==='object'){
      for(const k of Object.keys(value)){
        if(k==='lon'||k==='lat'||k==='longitude'||k==='latitude'){delete value[k];continue}
        value[k]=visit(value[k],k);
      }
      return value;
    }
    if(typeof value==='number'&&key==='x')return tx(value);
    if(typeof value==='number'&&key==='y')return ty(value);
    return value;
  };
  visit(data);
  data.bbox={minX:tx(minX),maxX:tx(maxX),minY:ty(minY),maxY:ty(maxY)};
  (data.districts||[]).forEach((item,index)=>{item.n=`区域${String(index+1).padStart(2,'0')}`});
  (data.lines||[]).forEach((item,index)=>{
    const prefix=item.v?`${item.v}kV`:'';
    item.n=`${prefix}示例线路${String(index+1).padStart(4,'0')}`;
    item.br=item.br?`${prefix}示例支线${String(index+1).padStart(4,'0')}`:'';
    if(Array.isArray(item.names))item.names=item.names.map((_,i)=>`T${String(i+1).padStart(3,'0')}`);
  });
  (data.rails||[]).forEach((item,index)=>{item.n=`铁路图层${String(index+1).padStart(4,'0')}`;item.e=''});
  (data.fireworks||[]).forEach((item,index)=>{item.id=`F${String(index+1).padStart(2,'0')}`;item.district='区域'});
  return data;
}

function sanitizeMap(encoded,key){
  let html=Buffer.from(encoded,'base64').toString('utf8');
  const match=html.match(/window\.([A-Z_]+)=/);
  if(!match)throw new Error(`map data assignment missing: ${key}`);
  const start=match.index+match[0].length;
  const end=html.indexOf(';</script>',start);
  if(end<0)throw new Error(`map data end missing: ${key}`);
  const data=transformData(JSON.parse(html.slice(start,end)));
  html=html.slice(0,start)+JSON.stringify(data)+html.slice(end);
  const titles={rail:'杆塔数字化交跨',fireworks:'燃放点空间筛查',bird:'防鸟重点区域'};
  html=html
    .replaceAll('南京杆塔数字化交跨交互图',titles.rail)
    .replaceAll('南京杆塔数字化交跨',titles.rail)
    .replaceAll('南京烟花燃放点空间筛查交互图',titles.fireworks)
    .replaceAll('烟花燃放点空间筛查',titles.fireworks)
    .replaceAll('南京防鸟重点区域交互图',titles.bird)
    .replaceAll('南京防鸟重点区域',titles.bird)
    .replaceAll('输入线路名，如 500kV东峰','输入线路编号，如 500kV示例线路0001')
    .replaceAll('线路搜索定位','线路定位')
    .replaceAll('点击交点联动','点击候选点联动');
  for(const token of [...CITY_TOKENS,...DISTRICT_TOKENS])html=html.replaceAll(token,'区域');
  html=html.replace('<body>','<body data-privacy="affine-quantized">');
  return Buffer.from(html).toString('base64');
}

function parseDataUri(uri){
  const match=String(uri).match(/^data:([^;]+);base64,(.+)$/s);
  if(!match)throw new Error('invalid photo data URI');
  return {mime:match[1],buffer:Buffer.from(match[2],'base64')};
}

function restoreOriginalPhoto(uri,destination){
  const {mime,buffer}=parseDataUri(uri);
  if(mime!=='image/jpeg')throw new Error(`unexpected original photo type: ${mime}`);
  fs.writeFileSync(destination,buffer);
}

fs.mkdirSync(imageDir,{recursive:true});
for(const [name,sourceName] of Object.entries({rail:'scene-railway.jpg',fireworks:'scene-fireworks.jpg',bird:'scene-bird.jpg'})){
  await sharp(path.join(reference,'assets/images',sourceName))
    .rotate()
    .jpeg({quality:90,chromaSubsampling:'4:4:4'})
    .toFile(path.join(imageDir,`scene-${name}.jpg`));
}

const pairs=[];
for(let index=0;index<PHOTO_PAIRS.length;index++){
  const sourcePair=PHOTO_PAIRS[index];
  const pairNo=String(index+1).padStart(2,'0');
  const aName=`pair-${pairNo}-a.jpg`,bName=`pair-${pairNo}-b.jpg`;
  restoreOriginalPhoto(sourcePair.p1src,path.join(imageDir,aName));
  restoreOriginalPhoto(sourcePair.p2src,path.join(imageDir,bName));
  pairs.push({
    id:`S${pairNo}`,
    risk:`样本${String.fromCharCode(65+(index%3))}`,
    yhlx:'现场作业场景',
    watermark:'原始反馈照片',
    time:'原始画面',
    phash:Number(sourcePair.phash),
    clip:Number(sourcePair.clip),
    a:aName,
    b:bName
  });
}

const result={
  maps:Object.fromEntries(Object.entries(EMBED_MAPS).map(([key,value])=>[key,sanitizeMap(value,key)])),
  pairs
};
fs.writeFileSync(output,JSON.stringify(result));
console.log(`[reference demos] 3 maps + ${pairs.length} photo pairs -> ${output}`);
