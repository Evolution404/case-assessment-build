#!/usr/bin/env python3
import json,re,subprocess,sys,zipfile
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
CITIES=['南京','苏州','无锡','常州','镇江','扬州','泰州','南通','盐城','淮安','宿迁','徐州','连云港']
FORBIDDEN=CITIES+['张宇熙','zhangyuxi','/Users/','longitude','latitude','pole_num','obj_id','raw_json']
def docx_text(p):
 with zipfile.ZipFile(p) as z:return '\n'.join(z.read(n).decode('utf-8','ignore') for n in z.namelist() if n.endswith('.xml'))
def pdf_text(p):return subprocess.run(['pdftotext',str(p),'-'],check=True,text=True,capture_output=True).stdout
files=[DIST/'案例考核报告-从人海作业到数智协同.docx',DIST/'答辩逐字稿-从人海作业到数智协同.docx',DIST/'课题答辩-从人海作业到数智协同.html',DIST/'课题答辩-从人海作业到数智协同.pdf'];errors=[]
for p in files:
 if not p.exists():errors.append(f'缺少文件：{p.name}');continue
 text=docx_text(p) if p.suffix=='.docx' else (pdf_text(p) if p.suffix=='.pdf' else p.read_text('utf-8','ignore'))
 for token in FORBIDDEN:
  if token.lower() in text.lower():errors.append(f'{p.name} 含禁用内容：{token}')
 if re.search(r'(?<!\d)(?:118|119|120|121)\.\d{4,}\s*[,，]\s*(?:30|31|32|33|34|35)\.\d{4,}(?!\d)',text):errors.append(f'{p.name} 疑似包含真实经纬度')
for p in (ROOT/'assets/images').glob('*.jpg'):
 with Image.open(p) as im:
  if im.getexif():errors.append(f'{p.name} 仍含 EXIF')
demo=json.loads((ROOT/'data/demo.json').read_text('utf-8'))
if any(k.lower() in {'lat','lon','lng','latitude','longitude','pole_num','line_name'} for k in re.findall(r'"([^"]+)"\s*:',json.dumps(demo,ensure_ascii=False))):errors.append('data/demo.json 含敏感字段名')
if errors:print('\n'.join('[privacy] ERROR '+e for e in errors));sys.exit(1)
print('[privacy] passed: no city, identity, production-field or exact-coordinate leakage')
