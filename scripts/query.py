#!/usr/bin/env python3
"""Read-only source and analysis lookup with exact provenance; no live data or semantic model."""
import argparse,json,re,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def norm(s):return re.sub(r'\s+','',s).lower()
def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for k in ['query','topic','chunk','context','sector']:g.add_argument('--'+k)
    for k in ['chapter','page','printed-page','interpret','box']:g.add_argument('--'+k,type=int)
    for k in ['toc','indicators','stats','figures','heritage','sectors']:g.add_argument('--'+k,action='store_true')
    p.add_argument('--limit',type=int,default=6);p.add_argument('--all',action='store_true',help='require all query keywords')
    p.add_argument('--search-scope',choices=['chunk','chapter'],default='chunk',help='chapter scope matches across chunks; read returned evidence chunks before quoting')
    p.add_argument('--json',action='store_true');a=p.parse_args()
    if not 1<=a.limit<=100:p.error('--limit must be 1..100')
    if a.search_scope!='chunk' and a.query is None and a.topic is None:p.error('--search-scope requires --query or --topic')
    con=sqlite3.connect((ROOT/'assets/data/plan.sqlite').as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
    info={k:json.loads(v) for k,v in con.execute('SELECT key,value FROM metadata')}
    def lookup(table,key=None):
        # table comes exclusively from constants below; values are bound.
        return [json.loads(r[0]) for r in con.execute(f'SELECT data_json FROM {table}'+(' WHERE id=?' if key is not None else ''),(() if key is None else (str(key),)))]
    mode='source_lookup';terms=[]
    if a.stats:result=info
    elif a.indicators:result=[json.loads(r[0]) for r in con.execute('SELECT data_json FROM indicators ORDER BY id')]
    elif a.toc:result=[dict(r) for r in con.execute('SELECT * FROM nodes ORDER BY pdf_page,line_start')]
    elif a.interpret is not None:
        if not 1<=a.interpret<=62:p.error('--interpret must be 1..62')
        mode='assistant_analysis';result=lookup('chapter_analysis',a.interpret)
    elif a.box is not None:
        if not 1<=a.box<=23:p.error('--box must be 1..23')
        mode='structured_source';result=lookup('boxes',f'box-{a.box:02d}')
    elif a.figures:mode='visual_description';result=lookup('figures')
    elif a.heritage:mode='visual_transcription';result=lookup('heritage')
    elif a.sectors or a.sector:
        mode='assistant_analysis';rows=lookup('sector_analysis')
        result=[{k:r[k] for k in ['id','title','chapters','classification']} for r in rows] if a.sectors else [r for r in rows if a.sector in [r['id'],r['title']]]
        if not result:p.error('unknown sector; use --sectors to list IDs')
    elif a.page is not None or a.printed_page is not None:
        page=a.page if a.page is not None else a.printed_page+5
        if not 1<=page<=info['pages'] or (a.printed_page is not None and a.printed_page<1):p.error('page out of range')
        result=[dict(r) for r in con.execute('SELECT * FROM pages WHERE pdf_page=?',(page,))]
    elif a.chapter is not None:
        if not 1<=a.chapter<=62:p.error('chapter must be 1..62')
        result=[dict(r) for r in con.execute('SELECT * FROM chunks WHERE chapter=? ORDER BY pdf_page,line_start',(f'ch-{a.chapter:02d}',))]
    elif a.chunk:
        result=lookup('heritage',a.chunk) if a.chunk.startswith('heritage-') else [dict(r) for r in con.execute('SELECT * FROM chunks WHERE id=?',(a.chunk,))]
    elif a.context:
        rows=[dict(r) for r in con.execute('SELECT * FROM chunks ORDER BY pdf_page,line_start')];indices=[i for i,r in enumerate(rows) if r['id']==a.context]
        if not indices:p.error('unknown chunk ID')
        i=indices[0];result=rows[max(0,i-1):i+2]
        for r in result:r['context_role']='target' if r['id']==a.context else 'adjacent_read_its_own_heading'
    else:
        mode='keyword';terms=re.split(r'[\s,，;；]+',a.query.strip()) if a.query is not None else []
        if a.topic:
            topics=json.loads((ROOT/'assets/data/topics.json').read_text())
            if a.topic not in topics:p.error('unknown topic; choose: '+', '.join(topics))
            terms=topics[a.topic]['terms'];mode='curated_topic'
        terms=list(dict.fromkeys(norm(t) for t in terms if norm(t)))
        if not terms:p.error('provide at least one keyword')
        if len(terms)>30 or any(len(t)>100 for t in terms):p.error('use at most 30 short keywords; split natural-language questions')
        rows=[dict(r) for r in con.execute('SELECT * FROM chunks WHERE pdf_page<>87')]
        # Unsafe multi-column raw extraction is never presented as a search hit.
        for r in lookup('heritage'):
            r.update(search_text=norm(r['text']),line_start=0,chapter='ch-34');rows.append(r)
        if a.search_scope=='chapter':
            mode+=':chapter';grouped={}
            for r in rows:
                if r.get('chapter'):grouped.setdefault(r['chapter'],[]).append(r)
            ranked=[]
            for cid,rs in grouped.items():
                hits=[t for t in terms if any(t in r['search_text'] or t in norm(r['path']) for r in rs)]
                if not hits or (a.all and len(hits)<len(terms)):continue
                n=dict(con.execute('SELECT * FROM nodes WHERE id=?',(cid,)).fetchone())
                ranked.append({'chapter':n['number'],'title':n['title'],'matched_terms':hits,'retrieval_score':len(hits),'evidence_chunks':[r['id'] for r in rs if any(t in r['search_text'] for t in terms)],'note':'关键词可分布在不同段落，不表示原文建立了因果联系。使用 --chapter 或 --chunk 读取原文。'})
            result=sorted(ranked,key=lambda r:(-r['retrieval_score'],r['chapter']))[:a.limit]
        else:
            ranked=[]
            for r in rows:
                hits=[t for t in terms if t in r['search_text'] or t in norm(r['path'])]
                if not hits or (a.all and len(hits)<len(terms)):continue
                bh=[t for t in hits if t in r['search_text']]
                score=10*len(bh)+3*(len(hits)-len(bh))+sum(min(r['search_text'].count(t),4) for t in bh)
                r.update(matched_terms=hits,body_matched_terms=bh,retrieval_score=score);ranked.append(r)
            result=sorted(ranked,key=lambda r:(-r['retrieval_score'],r['pdf_page'],r['line_start']))[:a.limit]
    note='关键词匹配不是语义理解或政策重要性评分；路径命中不等于正文证据。分析卡不是官方解读。没有检索实时执行数据。'
    if isinstance(result,list):
        for r in result:
            r.pop('search_text',None)
            if 'pdf_page' in r:
                r['citation']=f"《十五五规划纲要》{r.get('path',r.get('title',''))}，印刷第{r['printed_page']}页（PDF第{r['pdf_page']}页）" if r.get('printed_page') else f"《十五五规划纲要》PDF第{r['pdf_page']}页"
                r['source_url']=info['official_url']+f"#page={r['pdf_page']}"
            if r.get('pdf_page')==87 and r.get('classification')!='visually_transcribed_normalized':
                r['reading_order_warning']='本页横版四列原始文本混序，不能连续引用或据此配对编号。使用 --heritage 查看60个主条目；系列子项看原PDF。'
                r['raw_extracted_text']=r.pop('text','');r['text']='[原始文本阅读顺序不安全，已隐藏；主名录请用 --heritage。]'
                r.pop('raw_text',None)
            if r.get('pdf_page') in [27,86,119]:r['figure_note']='地图仅为示意；图例与边界说明见 --figures，精确地点和路线须查项目资料。'
    payload={'mode':mode,'terms':terms,'result_count':len(result),'results':result,'note':note}
    if a.json or not isinstance(result,list):print(json.dumps(payload,ensure_ascii=False,indent=2))
    else:
        print(note)
        if not result:print('未找到匹配项。请换同义词或查阅相关章节，不能据此断言规划未涉及。')
        for r in result:
            if 'text' in r:
                print('\n'+r.get('id','')+' '+r.get('citation',''))
                for key in ['reading_order_warning','figure_note','snapshot']:
                    if key in r:print('['+r[key]+']')
                if r.get('needs_visual_check'):print('[含专栏/图像；项目条目见 --box，图例见 --figures]')
                print(r['text'])
            else:print(json.dumps(r,ensure_ascii=False,indent=2))
    con.close()
if __name__=='__main__':main()
