#!/usr/bin/env python3
"""Check editorial revisions against the original protected Markdown structure."""
import argparse,json,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
FENCES=re.compile(r'(?m)^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$',re.S)
def parts(text):
    head,body=text.split('\n---\n\n',1)
    blocks=[m.group(0) for m in FENCES.finditer(body)]
    prose=FENCES.sub('',body)
    protected={
        'front_matter':head,
        'headings':re.findall(r'(?m)^#{1,6} .+$',prose),
        'code_blocks':blocks,
        'inline_code':re.findall(r'(?<!\\)(`+)([^`\n]+)\1',prose),
        'images':re.findall(r'(?m)^!\[.*?\]\([^\n]+\)$',prose),
        'captions':re.findall(r'(?m)^图\s*\d+[^\n]*$',prose),
        'link_targets':re.findall(r'\]\(([^\n]+?)\)',prose),
        'uncertain_markers':re.findall(r'［[^］]*(?:不清|不确定|未确认|未辨|缺失)[^］]*］',prose),
    }
    prose=re.sub(r'(?m)^(?:!\[|图\s*\d+|#{1,6} ).*$', '',prose)
    prose=re.sub(r'\\([\W_])',r'\1',prose)
    return protected,prose

def audit(base,lessons):
    reports=[]
    for number in lessons:
        for path in sorted((ROOT/'chapters'/f'{number:02d}').glob('*.md')):
            relative=path.relative_to(ROOT).as_posix()
            original=subprocess.run(['git','show',base+':'+relative],cwd=ROOT,check=True,capture_output=True,text=True).stdout
            old,op=parts(original);new,np=parts(path.read_text())
            errors=[name for name in old if old[name]!=new[name]]
            numeric=lambda s:set(re.findall(r'(?<![A-Za-z0-9])\d+(?:\.\d+)*(?:%|％)?',s))
            terms=lambda s:set(re.findall(r'(?<![A-Za-z0-9])[A-Za-z][A-Za-z0-9_+.-]{1,}',s))
            reports.append({'path':relative,'changed':original!=path.read_text(),'protected_errors':errors,'before_characters':len(re.sub(r'\s','',op)),'after_characters':len(re.sub(r'\s','',np)),'numbers_to_review':{'removed':sorted(numeric(op)-numeric(np)),'added':sorted(numeric(np)-numeric(op))},'terms_to_review':{'removed':sorted(terms(op)-terms(np)),'added':sorted(terms(np)-terms(op))}})
    return {'baseline':base,'status':'passed' if all(not r['protected_errors'] for r in reports) else 'failed','scope':'Exact front matter, headings, fenced and inline code, image references, captions, link targets and uncertainty markers. Number/term differences are review prompts; semantic fidelity requires paragraph review.','sections':reports}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-ref',default='90cd258a51d0e3be111d8aeb716a1f3fa2f67c07');p.add_argument('--lessons',nargs='+',type=int,default=list(range(1,31)));p.add_argument('--report',type=pathlib.Path);a=p.parse_args();report=audit(a.base_ref,a.lessons)
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'sections':len(report['sections']),'changed':sum(x['changed'] for x in report['sections']),'protected_errors':[{'path':x['path'],'errors':x['protected_errors']} for x in report['sections'] if x['protected_errors']],'review_prompts':sum(bool(x['numbers_to_review']['removed'] or x['numbers_to_review']['added'] or x['terms_to_review']['removed']) for x in report['sections'])},ensure_ascii=False))
    raise SystemExit(report['status']!='passed')
