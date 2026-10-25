#!/usr/bin/env python3
"""Build the portable static reader from editable Markdown and lesson metadata."""
import argparse, html, json, pathlib, re, shutil
import markdown
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
def e(s): return html.escape(str(s),quote=True)
def load_md(p):
    s=p.read_text(); _,meta,body=s.split('---',2); return json.loads(meta),body.strip()
def build(base):
    base='/'+base.strip('/')+'/' if base.strip('/') else '/'
    out=ROOT/'build';out.mkdir(exist_ok=True)
    lessons=[json.loads(p.read_text()) for p in sorted((ROOT/'maintenance').glob('lesson-*.json'))]
    for lesson in lessons:
        for section in lesson['sections']:
            meta,_=load_md(ROOT/section['path'])
            section.update(meta)
    units=[dict(s,lesson_title=l['title'],source=l['source']) for l in lessons for s in l['sections']]
    def url(s):return base+s
    def sidebar(current=None):
        rows=[]
        for l in lessons:
            active=current and current['lesson']==l['number']
            children=''.join(f'<a href="{url(s["route"])}"'+(' aria-current="page"' if current and current['route']==s['route'] else '')+f'><span>{s["section"]:02d}</span>{e(s["title"])}</a>' for s in l['sections']) if active else ''
            rows.append(f'<div class="nav-lesson"><div class="nav-row"><a href="{url(l["sections"][0]["route"])}"><span class="nav-number">{l["number"]:02d}</span><span>{e(l["title"])}</span></a><button class="expand" data-lesson="{l["number"]}" aria-expanded="{str(bool(active)).lower()}" aria-controls="nav-{l["number"]}" aria-label="展开第 {l["number"]} 课">⌄</button></div><div class="nav-sections" id="nav-{l["number"]}"'+('' if active else ' hidden')+'>'+children+'</div></div>')
        return '<aside id="sidebar" aria-label="课程目录"><a class="brand" href="'+base+'">南京大学<br><strong>操作系统原理</strong><small>2026 · 蒋炎岩</small></a><div class="nav-label">全部课程 <span>30</span></div><nav>'+''.join(rows)+'</nav></aside>'
    def shell(title,body,current=None):
        return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#f7f5ef"><title>{e(title)} · 操作系统原理</title><link rel="stylesheet" href="{url('assets/reader.css')}"><script defer src="{url('assets/reader.js')}"></script></head><body data-base="{base}" data-route="{e(current['route'] if current else '')}"><a class="skip" href="#main">跳至正文</a><div id="scroll-progress"></div><header class="toolbar"><button id="menu-toggle" aria-controls="sidebar" aria-expanded="false">☰ <span>目录</span></button><a class="mobile-brand" href="{base}">操作系统原理 <small>2026</small></a><div class="tools"><button id="font-down" aria-label="缩小字号">A−</button><button id="font-up" aria-label="放大字号">A+</button><button id="search-open">搜索 <span class="key">⌘ K</span></button></div></header><button id="drawer-shade" aria-label="关闭目录" hidden></button>{sidebar(current)}<main id="main">{body}<footer class="site-footer">南京大学操作系统原理 · 2026 · 蒋炎岩</footer></main><dialog id="search-dialog"><div class="search-header"><label for="search-input">搜索课程</label><button data-close="search-dialog" aria-label="关闭搜索">✕</button></div><input id="search-input" type="search" placeholder="输入中文、概念或代码，如：条件变量、fork" autocomplete="off"><p id="search-status" role="status">输入关键词，搜索全部 30 节课。</p><div id="search-results"></div></dialog><dialog id="image-dialog"><button data-close="image-dialog" aria-label="关闭图片">✕</button><div class="image-scroll"><img id="zoom-image" alt=""></div><p id="zoom-caption"></p></dialog></body></html>'''
    search=[]
    for i,u in enumerate(units):
        meta,body=load_md(ROOT/u['path'])
        body=body.replace('](/assets/',']('+base+'assets/')
        rendered=markdown.markdown(body,extensions=['fenced_code','tables','sane_lists'])
        soup=BeautifulSoup(rendered,'html.parser')
        for img in soup.find_all('img'):
            img['loading']='lazy';img['decoding']='async';img['tabindex']='0';img['role']='button';img['title']='点击放大'
            pic=ROOT/img['src'][len(base):]
            from PIL import Image
            with Image.open(pic) as im:img['width'],img['height']=im.size
            parent=img.parent
            if parent.name=='p' and parent.get_text().strip()=='':
                parent.name='figure'
                sibling=parent.find_next_sibling()
                if sibling and sibling.name=='p' and sibling.get_text().startswith(('图 ', '图\u3000')):
                    sibling.name='figcaption';parent.append(sibling.extract())
        text=soup.get_text(' ',strip=True)
        search.append({'route':u['route'],'lesson':u['lesson'],'lessonTitle':u['lesson_title'],'title':u['title'],'text':text})
        prev=units[i-1] if i else None; nxt=units[i+1] if i+1<len(units) else None
        pager='<nav class="pager" aria-label="连续阅读">'
        for direction,item,label in [('prev',prev,'← 上一节'),('next',nxt,'下一节 →')]:
            if item:pager+=f'<a rel="{direction}" href="{url(item["route"])}"><small>{label} · 第 {item["lesson"]:02d} 课</small><span>{e(item["title"])}</span></a>'
            else:pager+='<span></span>'
        pager+='</nav>'
        first=next(l['sections'][0]['route'] for l in lessons if l['number']==u['lesson'])
        bodyhtml=f'<article><div class="eyebrow"><a href="{url(first)}">第 {u["lesson"]:02d} 课 · {e(u["lesson_title"])}</a></div><div class="prose"><h1>{e(u["title"])}</h1><p class="timing">原片 {e(meta["time"])}</p>{soup}</div><div class="source-link"><a href="{e(u["source"])}" target="_blank" rel="noopener">观看本课视频 ↗</a><a href="https://jyywiki.cn/OS/2026/" target="_blank" rel="noopener">课程主页 ↗</a></div>{pager}</article>'
        target=out/u['route'];target.parent.mkdir(parents=True,exist_ok=True);target.write_text(shell(u['title'],bodyhtml,u))
    rows=''.join(f'<a class="lesson-link" href="{url(l["sections"][0]["route"])}"><span class="lesson-no">{l["number"]:02d}</span><span><strong>{e(l["title"])}</strong><small>{len(l["sections"])} 节 · {l["sections"][0]["time"].split("—")[0]}—{l["sections"][-1]["time"].split("—")[-1]}</small></span><span class="arrow">↗</span></a>' for l in lessons)
    home=f'<div class="home"><div class="eyebrow">NANJING UNIVERSITY · 2026</div><h1>操作系统原理</h1><p class="home-subtitle">Agentic AI 时代，重新理解计算机系统。</p><p class="intro">从程序、进程和系统调用出发，走过并发、处理器、输入输出、文件系统与安全，理解软件如何在硬件上运行。</p><div class="home-meta"><span>蒋炎岩 · 南京大学</span><span>30 节课 · {len(units)} 个阅读小节</span></div><div class="home-actions"><a class="primary" href="{url(units[0]["route"])}">从第一课开始 →</a><a id="continue-reading" hidden href="{url(units[0]["route"])}">继续上次阅读 →</a></div><p class="reading-tip">按课程顺序阅读，也可用目录定位主题。搜索支持中文与代码；课件图片可点击放大，正文下方可连续翻页。字号可在顶部调整。</p><div class="catalog-heading"><h2>课程目录</h2><span>按授课顺序</span></div><div class="lesson-list">{rows}</div></div>'
    (out/'index.html').write_text(shell('课程目录',home))
    (out/'assets').mkdir(exist_ok=True)
    for f in ['reader.css','reader.js']:shutil.copyfile(ROOT/'web'/f,out/'assets'/f)
    shutil.copytree(ROOT/'assets/images',out/'assets/images',dirs_exist_ok=True)
    (out/'assets/search.json').write_text(json.dumps(search,ensure_ascii=False,separators=(',',':')))
    (out/'assets/navigation.json').write_text(json.dumps(lessons,ensure_ascii=False,separators=(',',':')))
    (out/'.nojekyll').touch()
    (ROOT/'maintenance/reading-pages.json').write_text(json.dumps({'pages':[u['route'] for u in units]},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'lessons':len(lessons),'sections':len(units),'images':sum(l['images'] for l in lessons),'base':base},ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-path',default='/nju-os-reading/');a=p.parse_args();build(a.base_path)
