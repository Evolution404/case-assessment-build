#!/usr/bin/env node
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const deck=path.join(root,'dist/课题答辩-从人海作业到数智协同.html');
const configPath=path.join(root,'content/workorder_zoom.json');
const host='127.0.0.1';
const port=4177;

function send(res,status,type,body){
  res.writeHead(status,{'content-type':type,'cache-control':'no-store'});
  res.end(body);
}
function validConfig(value){
  if(!value||typeof value!=='object')return false;
  if(!value.window||value.window.width!==220||value.window.height!==156)return false;
  for(const key of ['a','b']){
    const c=value[key];
    if(!c||![c.x,c.y,c.zoom].every(Number.isFinite))return false;
    if(c.x<0||c.x>1||c.y<0||c.y>1||c.zoom<2||c.zoom>12)return false;
  }
  return true;
}
const server=http.createServer((req,res)=>{
  const url=new URL(req.url,`http://${host}:${port}`);
  if(req.method==='GET'&&(url.pathname==='/'||url.pathname==='/index.html')){
    if(!fs.existsSync(deck))return send(res,500,'text/plain; charset=utf-8','请先构建答辩HTML。');
    return send(res,200,'text/html; charset=utf-8',fs.readFileSync(deck));
  }
  if(req.method==='GET'&&url.pathname==='/health')return send(res,200,'application/json; charset=utf-8',JSON.stringify({ok:true}));
  if(req.method==='GET'&&url.pathname==='/zoom-config')return send(res,200,'application/json; charset=utf-8',fs.readFileSync(configPath));
  if(req.method==='POST'&&url.pathname==='/save-zoom'){
    let body='';
    req.on('data',chunk=>{body+=chunk;if(body.length>100000)req.destroy()});
    req.on('end',()=>{
      try{
        const value=JSON.parse(body);
        if(!validConfig(value))return send(res,400,'text/plain; charset=utf-8','参数无效。');
        fs.writeFileSync(configPath,JSON.stringify(value,null,2)+'\n');
        return send(res,200,'application/json; charset=utf-8',JSON.stringify({ok:true,path:configPath}));
      }catch(error){
        return send(res,400,'text/plain; charset=utf-8',String(error.message||error));
      }
    });
    return;
  }
  send(res,404,'text/plain; charset=utf-8','Not found');
});
server.listen(port,host,()=>console.log(`[zoom-calibrator] http://${host}:${port}/?zoom-calibrate=1&p=9`));
