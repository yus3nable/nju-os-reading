#!/usr/bin/env python3
"""Compare rendered article characters and code with the independent PDF text layer."""
import argparse, collections, difflib, json, pathlib, re
import fitz
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
def norm(s):return re.sub(r'\s+','',s)
def audit(source):
    reports=[]
    for metadata in sorted((ROOT/'maintenance').glob('lesson-*.json')):
        lesson=json.loads(metadata.read_text()); d=fitz.open(source/lesson['pdf']); started=False; original=[]; code=[]; images=0
        for p in d:
            code_rects=[x['rect'] for x in p.get_drawings() if x['fill'] and max(x['fill'])-min(x['fill'])>.005 and x['rect'].width>300 and x['rect'].height>12]
            lines=[]
            for b in p.get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)['blocks']:
                for ln in b.get('lines',[]):
                    ss=ln['spans'];size=max(s['size'] for s in ss);y=ss[0]['origin'][1];text=''.join(s['text'] for s in ss)
                    if size<=8 and y>570:continue
                    mono=(size<=10.5 and any('Menlo' in s['font'] for s in ss)) or any(r.contains(fitz.Point(ss[0]['origin'])) for r in code_rects)
                    lines.append((y,size,text,mono))
            lines.sort(key=lambda x:x[0])
            for y,size,text,mono in lines:
                if abs(size-24)<.1:started=True
                if started:
                    original.append(text)
                    if mono:code.append(text)
            if started:images+=len(p.get_image_info(xrefs=True))
        rendered=[];rendered_code=[];rendered_images=0
        for section in lesson['sections']:
            soup=BeautifulSoup((ROOT/'build'/section['route']).read_text(),'html.parser');prose=soup.select_one('.prose')
            rendered.append(prose.get_text('',strip=False))
            rendered_code.extend(x.get_text() for x in prose.select('pre code'))
            rendered_images+=len(prose.select('img'))
        a=norm(''.join(original));b=norm(''.join(rendered));b=b.replace('原片','') # timing labels are metadata, not prose
        # Source includes the same explicit 原片 label once per reading unit.
        a=a.replace('原片','')
        match=a==b
        code_original=[line.rstrip() for line in code if line.strip()]
        code_site=[line.rstrip() for block in rendered_code for line in block.splitlines() if line.strip()]
        r={'lesson':lesson['number'],'characters_match':match,'source_characters':len(a),'rendered_characters':len(b),'images_source':images,'images_site':rendered_images,'code_characters_match':code_original==code_site}
        if code_original!=code_site:
            k=next((i for i,(x,y) in enumerate(zip(code_original,code_site)) if x!=y),min(len(code_original),len(code_site)))
            r['code_first_difference']={'line':k,'source':code_original[max(0,k-2):k+3],'site':code_site[max(0,k-2):k+3]}
        if not match:
            pos=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)))
            r['first_difference']={'offset':pos,'source':a[max(0,pos-40):pos+120],'site':b[max(0,pos-40):pos+120]}
        reports.append(r)
    passed=all(r['characters_match'] and r['images_source']==r['images_site'] and r['code_characters_match'] for r in reports)
    result={'status':'passed' if passed else 'failed','scope':'All body characters (ignoring whitespace and timing prefix), native figure count, and code characters against the PDF text layer. This is conversion QA, not a fresh transcription review.','lessons':reports}
    (ROOT/'maintenance/content-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
    return passed
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('pdf_directory',type=pathlib.Path);args=p.parse_args();raise SystemExit(not audit(args.pdf_directory))
