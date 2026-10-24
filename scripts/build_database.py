#!/usr/bin/env python3
"""Rebuild a page-grounded corpus from the bundled, immutable source PDF.
Build requires PyMuPDF. Querying requires only Python's standard library.
This parser is specific to this PDF's heading fonts; fail closed on structure drift.
"""
import collections, hashlib, json, re, sqlite3
from pathlib import Path
import fitz
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'assets/data'
SOURCE = ROOT / 'assets/source/plan-2026-2030.pdf'
URL = 'https://www.ndrc.gov.cn/fggz/fzzlgh/gjfzgh/202603/U020260317369114704096.pdf'
DOC = 'plan-15-2026-03'
def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def compact(s):
    return re.sub(r'\s+', '', s).lower()
def cnnum(s):
    n=0; digit=0
    for c in s:
        if c=='十': n+=(digit or 1)*10; digit=0
        elif c=='百': n+=(digit or 1)*100; digit=0
        else: digit='零一二三四五六七八九'.index(c)
    return n+digit

def main():
    DATA.mkdir(parents=True, exist_ok=True)
    pdf=fitz.open(SOURCE)
    pages=[]; nodes=[]; chunks=[]; chapter=part=section=box=None
    current={'part':None,'chapter':None,'section':None,'box':None}
    for pno,page in enumerate(pdf,1):
        lines=[]
        for block in page.get_text('dict')['blocks']:
            for ln in block.get('lines',[]):
                spans=ln['spans']; t=''.join(s['text'] for s in spans).strip()
                if t:
                    lines.append({'text':t,'font':spans[0]['font'],'size':round(spans[0]['size'],2),'bbox':[round(x,2) for x in ln['bbox']]})
        printed=None
        if pno>=6:
            footers=[i for i,l in enumerate(lines) if l['text']==str(pno-5) and l['bbox'][1]>750]
            assert len(footers)==1 or (pno==87 and len(footers)==0), (pno,footers)  # rotated page 82 visually checked
            printed=pno-5
            body=[l for i,l in enumerate(lines) if i not in footers]
        else: body=lines
        pages.append({'document_id':DOC,'pdf_page':pno,'printed_page':printed,'kind':'body' if pno>=6 else ('cover' if pno==1 else 'contents'),
                      'raw_text':page.get_text(),'text':'\n'.join(l['text'] for l in body),'lines':body,'embedded_images':len(page.get_images())})
        if pno<6: continue
        starts={}; skip=set()
        for i,line in enumerate(body):
            t=line['text']; m=re.fullmatch(r'第([一二三四五六七八九十百]+)([篇章节])',t); bm=re.fullmatch(r'专栏\s*(\d+)',t)
            if not m and not bm: continue
            kind={'篇':'part','章':'chapter','节':'section'}[m[2]] if m else 'box'
            number=cnnum(m[1]) if m else int(bm[1]); title=[]; j=i+1
            while j<len(body) and body[j]['font']==line['font'] and body[j]['size']==line['size'] and not body[j]['text'].startswith('——'):
                title.append(body[j]['text']); skip.add(j); j+=1
            assert title, (pno,t)
            starts[i]=(kind,number,t,''.join(title))
        # Each chunk is an exact contiguous range of extracted body lines.
        pending=[]; start=0; context=None; ordinal=0
        def flush():
            nonlocal pending,start,context,ordinal
            if not pending:return
            ordinal+=1
            text='\n'.join(l['text'] for l in pending)
            path=' / '.join(nodes_by_id[x]['label']+' '+nodes_by_id[x]['title'] for x in context.values() if x)
            chunks.append({'id':f'p{pno:04d}-c{ordinal:02d}','document_id':DOC,'pdf_page':pno,'printed_page':printed,
                'line_start':start+1,'line_end':start+len(pending),'path':path,**context,'text':text,
                'search_text':compact(text),'needs_visual_check':bool(context['box']) or bool(page.get_images())})
            pending=[]
        nodes_by_id={n['id']:n for n in nodes}
        for i,line in enumerate(body):
            if i in starts:
                flush()
                kind,num,label,title=starts[i]
                if kind=='part': current={'part':f'part-{num:02d}','chapter':None,'section':None,'box':None}
                elif kind=='chapter':current.update(chapter=f'ch-{num:02d}',section=None,box=None)
                elif kind=='section':current.update(section=f"{current['chapter']}-s{num:02d}",box=None)
                else:current['box']=f'box-{num:02d}'
                nid=current[kind]
                parent={'part':None,'chapter':current['part'],'section':current['chapter'],'box':current['chapter']}[kind]
                node={'id':nid,'kind':kind,'number':num,'label':label,'title':title,'parent':parent,'pdf_page':pno,'printed_page':printed,'line_start':i+1}
                nodes.append(node);nodes_by_id[nid]=node
            # Box prose uses smaller fonts. A normal body paragraph terminates a box.
            elif current['box'] and (re.match(r'^图\s*[0-9]+',line['text']) or (i not in skip and line['size']>=14.9 and 'FZFSK' in line['font'])):
                flush();current['box']=None
            if pending and sum(len(x['text']) for x in pending)>1000 and i not in skip:
                flush()
            if not pending:
                start=i;context=current.copy()
                if context['box']: context['section']=None
            pending.append(line)
        flush()
    counts=collections.Counter(n['kind'] for n in nodes)
    assert len(pdf)==140 and counts=={'part':18,'chapter':62,'section':171,'box':23},counts
    assert [n['number'] for n in nodes if n['kind']=='chapter']==list(range(1,63))
    for p in pages[5:]:
        pc=[c for c in chunks if c['pdf_page']==p['pdf_page']]
        assert '\n'.join(c['text'] for c in pc)==p['text'],p['pdf_page']
    dbtemp=DATA/'plan.sqlite.tmp'
    if dbtemp.exists(): dbtemp.unlink()
    con=sqlite3.connect(dbtemp)
    con.executescript('''
      CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
      CREATE TABLE pages(pdf_page INTEGER PRIMARY KEY,printed_page INTEGER,kind TEXT,text TEXT,raw_text TEXT,embedded_images INTEGER);
      CREATE TABLE nodes(id TEXT PRIMARY KEY,kind TEXT,number INTEGER,label TEXT,title TEXT,parent TEXT,pdf_page INTEGER,printed_page INTEGER,line_start INTEGER);
      CREATE TABLE chunks(id TEXT PRIMARY KEY,document_id TEXT,pdf_page INTEGER,printed_page INTEGER,line_start INTEGER,line_end INTEGER,path TEXT,part TEXT,chapter TEXT,section TEXT,box TEXT,text TEXT,search_text TEXT,needs_visual_check INTEGER);
      CREATE INDEX chunks_chapter ON chunks(chapter);
      CREATE INDEX chunks_page ON chunks(pdf_page);
      CREATE TABLE indicators(id INTEGER PRIMARY KEY,name TEXT,data_json TEXT);
    ''')
    for p in pages:
        con.execute('INSERT INTO pages VALUES (?,?,?,?,?,?)',tuple(p[k] for k in ['pdf_page','printed_page','kind','text','raw_text','embedded_images']))
    for n in nodes:
        con.execute('INSERT INTO nodes VALUES (?,?,?,?,?,?,?,?,?)',tuple(n[k] for k in ['id','kind','number','label','title','parent','pdf_page','printed_page','line_start']))
    for c in chunks:
        con.execute('INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',tuple(c[k] for k in ['id','document_id','pdf_page','printed_page','line_start','line_end','path','part','chapter','section','box','text','search_text','needs_visual_check']))
    fts=False
    try:
        con.execute("CREATE VIRTUAL TABLE chunk_fts USING fts5(id UNINDEXED, search_text, tokenize='trigram')")
        con.executemany('INSERT INTO chunk_fts VALUES (?,?)',[(c['id'],c['search_text']) for c in chunks]);fts=True
    except sqlite3.OperationalError: pass
    ip=DATA/'indicators.json'
    if ip.exists():
        for x in json.loads(ip.read_text())['indicators']:
            con.execute('INSERT INTO indicators VALUES (?,?,?)',(x['id'],x['name'],json.dumps(x,ensure_ascii=False)))
    manifest={'schema_version':2,'document_id':DOC,'title':'中华人民共和国国民经济和社会发展第十五个五年规划纲要','document_date':'2026-03','planning_period':[2026,2030],
       'source_file':'assets/source/plan-2026-2030.pdf','sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'bytes':SOURCE.stat().st_size,
       'official_url':URL,'provenance_check':{'date':'2026-10-22','method':'Official-domain search located same PDF filename and title; web open reported same byte length. No remote byte-hash comparison performed.'},
       'pages':len(pages),'body_pages':135,'structure':dict(counts),'chunks':len(chunks),'body_characters':sum(len(p['text']) for p in pages[5:]),
       'fts5_trigram':fts,'extractor':f'PyMuPDF {fitz.VersionBind}','page_mapping':'PDF page = printed Arabic page + 5; cover and four TOC pages have no Arabic printed page',
       'quality_scope':'All 140 pages extracted; structure and line-range coverage checked. All 23 boxes visually cross-checked on 2026-10-23. Figures visually inspected for titles, legends and use limits; spatial detail is not a GIS dataset. Page 87 multi-column raw order is unsafe: use the structured main-entry register. Preserve raw_text and per-line bboxes.',
       'live_evidence':'Not bundled; retrieve at decision time. Source snapshots of 2024/2025 values are not current statistics.'}
    con.executemany('INSERT INTO metadata VALUES (?,?)',[(k,json.dumps(v,ensure_ascii=False)) for k,v in manifest.items()])
    con.commit(); assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok';con.close()
    dbtemp.replace(DATA/'plan.sqlite')
    dump(DATA/'manifest.json',manifest)
    for name, rows in [('pages',pages),('chunks',chunks)]:
        (DATA/f'{name}.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf-8')
    dump(DATA/'structure.json',nodes)
    (ROOT/'references/fulltext.md').write_text('# 十五五规划原文（逐页提取）\n\n注意：表格阅读顺序以原PDF为准。正文纸面页码=PDF页码−5。\n\n'+'\n\n'.join(f"## PDF第{p['pdf_page']}页 / 印刷页{p['printed_page'] if p['printed_page'] else p['kind']}\n\n{('[阅读顺序警告：本页横版四列抽取混序，编号配对须读取assets/data/heritage.json或原PDF；不要连续引用。]'+chr(10)+chr(10)) if p['pdf_page']==87 else ''}{p['text']}" for p in pages),encoding='utf-8')
    (ROOT/'references/structure.md').write_text('# 原文章节导航\n\n|层级|编号及标题|PDF页|印刷页|检索ID|\n|---|---|---:|---:|---|\n'+'\n'.join(f"|{n['kind']}|{n['label']} {n['title']}|{n['pdf_page']}|{n['printed_page']}|{n['id']}|" for n in nodes)+'\n',encoding='utf-8')
    from compile_knowledge import main as compile_knowledge
    compile_knowledge()
    print((DATA/'manifest.json').read_text())
if __name__=='__main__':main()
