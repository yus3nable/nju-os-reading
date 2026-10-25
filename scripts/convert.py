#!/usr/bin/env python3
"""Recover course text, code and embedded figures without rasterizing PDF pages."""
import argparse, collections, html, io, json, pathlib, re
import fitz
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1]
def esc(s):
    s=html.escape(s,quote=False).replace('|','&#124;')
    return re.sub(r'([\\`*{}_\[\]#.!+\-])',r'\\\1',s)
def join(a,b):
    return a+(' ' if a and b and a[-1].isascii() and b[0].isascii() and a[-1].isalnum() and b[0].isalnum() else '')+b

def convert(pdf, replace=False, text_only=False):
    num=int(pdf.name[:2]); folder=ROOT/'chapters'/f'{num:02d}'
    if folder.exists() and not replace: raise RuntimeError(f'Existing editable chapter: {folder}')
    folder.mkdir(exist_ok=True); image_dir=ROOT/'assets/images'/f'{num:02d}'; image_dir.mkdir(exist_ok=True)
    doc=fitz.open(pdf); sections=[]; current=None; count=0; code_count=0; text_lines=0; source=''; toc_count=0
    for page_index,page in enumerate(doc):
        code_rects=[x['rect'] for x in page.get_drawings() if x['fill'] and max(x['fill'])-min(x['fill'])>.005 and x['rect'].width>300 and x['rect'].height>12]
        links=page.get_links()
        toc_count+=sum(x.get('nameddest','').startswith('chapter-') for x in links)
        for x in links:
            if 'bilibili.com/video/' in x.get('uri',''): source=x['uri']
        events=[]
        for b in page.get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)['blocks']:
            for line in b.get('lines',[]):
                spans=line['spans']; size=max(s['size'] for s in spans); baseline=spans[0]['origin'][1]
                if size<=8 and baseline>570: continue
                text=''.join(s['text'] for s in spans)
                if not text.strip(): continue
                code=(size<=10.5 and any('Menlo' in s['font'] for s in spans)) or any(r.contains(fitz.Point(spans[0]['origin'])) for r in code_rects)
                kind='heading' if abs(size-24)<.1 else 'time' if text.startswith('原片 ') else 'code' if code else 'subheading' if size>=13 else 'caption' if abs(size-9.375)<.1 else 'text'
                events.append({'y':baseline,'kind':kind,'text':text,'size':size,'page':page_index+1})
        if not current and not any(x['kind']=='heading' for x in events): continue
        for im in page.get_image_info(xrefs=True):
            events.append({'y':im['bbox'][1]+.1,'kind':'image','image':im,'page':page_index+1})
        events.sort(key=lambda x:x['y'])
        for ev in events:
            kind=ev['kind']
            if kind=='heading':
                if current and current['events'] and current['events'][-1]['kind']=='heading' and current['events'][-1]['page']==ev['page']:
                    current['title']=join(current['title'],ev['text']); current['events'].append(ev); continue
                current={'title':ev['text'],'events':[ev],'page_start':ev['page']}; sections.append(current)
            elif current:
                if kind=='image':
                    count+=1; im=ev['image']
                    name=f'{count:04d}.webp'
                    if text_only:
                        if not (image_dir/name).is_file(): raise RuntimeError(f'Missing existing image: {image_dir/name}')
                    else:
                        data=doc.extract_image(im['xref'])['image']
                        img=Image.open(io.BytesIO(data)).convert('RGB')
                        img.save(image_dir/name,'WEBP',quality=92,method=4)
                    ev['path']=f'/assets/images/{num:02d}/{name}'; ev['width'],ev['height']=im['width'],im['height']; del ev['image']
                else: text_lines+=1
                current['events'].append(ev)
    if len(sections)!=toc_count: raise RuntimeError(f'{num}: {len(sections)} sections != {toc_count} TOC links')
    records=[]
    for idx,section in enumerate(sections,1):
        events=section['events']; blocks=[]; pending=''; previous=None; codes=[]
        def flush_text():
            nonlocal pending
            if pending: blocks.append(pending); pending=''
        def flush_code():
            nonlocal codes,code_count
            if codes:
                fence='`'*max(3,1+max((len(m.group()) for m in re.finditer(r'`+', '\n'.join(codes))),default=0))
                blocks.append(fence+'\n'+'\n'.join(codes)+'\n'+fence); codes=[]; code_count+=1
        time=''
        for i,ev in enumerate(events):
            kind=ev['kind']; t=ev.get('text','')
            if kind in ('heading','time'):
                if kind=='time': time=t.removeprefix('原片 ')
                continue
            if kind=='code':
                flush_text()
                if codes and previous and ev['page']==previous['page'] and ev['y']-previous['y']>20: codes.append('')
                codes.append(t)
            else:
                flush_code()
                if kind=='image':
                    flush_text()
                    caption=next((x['text'] for x in events[i+1:i+4] if x.get('text','').startswith('图 ')),f'课堂画面 {ev["page"]} 页')
                    blocks.append('!['+esc(caption)+']('+ev['path']+')')
                elif kind=='subheading':
                    flush_text(); blocks.append('## '+esc(t))
                else:
                    new_para=not previous or previous['kind']!=kind or (ev['page']==previous['page'] and ev['y']-previous['y']>21) or t.startswith('图 ')
                    if new_para: flush_text()
                    pending=join(pending,esc(t))
            previous=ev
        flush_text();flush_code()
        meta={'lesson':num,'section':idx,'title':section['title'],'time':time,'source_pages':[section['page_start'],events[-1]['page']]}
        (folder/f'{idx:03d}.md').write_text('---\n'+json.dumps(meta,ensure_ascii=False)+'\n---\n\n'+'\n\n'.join(blocks)+'\n',encoding='utf-8')
        records.append(dict(meta,path=f'chapters/{num:02d}/{idx:03d}.md',route=f'lessons/{num:02d}/{idx:03d}.html'))
    title=re.sub(r' \[2026.*','',pdf.stem)
    title=re.sub(r'^\d+\s*(\(Aside\))?\s*-\s*',lambda m:'(Aside) ' if m[1] else '',title)
    result={'number':num,'title':title,'source':source,'pdf':pdf.name,'pdf_pages':len(doc),'images':count,'text_lines':text_lines,'code_blocks':code_count,'sections':records}
    (ROOT/'maintenance'/f'lesson-{num:02d}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f'{num:02d}: {len(sections)} sections, {count} images, {code_count} code blocks',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('pdfs',nargs='+',type=pathlib.Path);p.add_argument('--replace',action='store_true');p.add_argument('--text-only',action='store_true',help='Reuse existing extracted images when repairing text conversion.');args=p.parse_args()
    for pdf in args.pdfs: convert(pdf,args.replace,args.text_only)
