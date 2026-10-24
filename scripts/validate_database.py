#!/usr/bin/env python3
"""Verify source identity, lossless chunk coverage, references and query behavior."""
import hashlib,json,sqlite3,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'assets/data'
def check(ok,msg):
    if not ok:raise AssertionError(msg)
def query(*args):
    p=subprocess.run([sys.executable,str(ROOT/'scripts/query.py'),*args,'--json'],capture_output=True,text=True,check=True)
    return json.loads(p.stdout)['results']
def main():
    manifest=json.loads((D/'manifest.json').read_text())
    check(hashlib.sha256((ROOT/manifest['source_file']).read_bytes()).hexdigest()==manifest['sha256'],'source hash')
    con=sqlite3.connect(D/'plan.sqlite');con.row_factory=sqlite3.Row
    check(con.execute('PRAGMA integrity_check').fetchone()[0]=='ok','sqlite integrity')
    pages=[json.loads(s) for s in (D/'pages.jsonl').read_text().splitlines()]
    chunks=[json.loads(s) for s in (D/'chunks.jsonl').read_text().splitlines()]
    nodes=json.loads((D/'structure.json').read_text()); ids={n['id'] for n in nodes}
    check(len(pages)==140 and len(chunks)==manifest['chunks'],'page/chunk counts')
    check(len(ids)==274 and len(nodes)==274,'node uniqueness')
    check([n['number'] for n in nodes if n['kind']=='chapter']==list(range(1,63)),'chapter sequence')
    for p in pages:
        dbp=con.execute('SELECT text FROM pages WHERE pdf_page=?',(p['pdf_page'],)).fetchone()
        check(dbp[0]==p['text'],'db/json page mismatch')
        if p['pdf_page']<6:continue
        pc=[c for c in chunks if c['pdf_page']==p['pdf_page']]
        check('\n'.join(c['text'] for c in pc)==p['text'],f"page {p['pdf_page']} lost text")
        cursor=1
        for c in pc:
            check(c['line_start']==cursor,'line gap or overlap');cursor=c['line_end']+1
            check(c['text']=='\n'.join(x['text'] for x in p['lines'][c['line_start']-1:c['line_end']]),'line range mismatch')
            check(c['printed_page']==c['pdf_page']-5,'page mapping')
            for kind in ['part','chapter','section','box']:
                check(c[kind] is None or c[kind] in ids,'dangling node')
            if c['box']:check(c['needs_visual_check'] and c['section'] is None,'box citation boundary')
            if p['embedded_images']:check(c['needs_visual_check'],'image not flagged')
            dbc=dict(con.execute('SELECT * FROM chunks WHERE id=?',(c['id'],)).fetchone())
            for key in dbc:check(dbc[key]==c[key],'db/json chunk mismatch')
        check(cursor==len(p['lines'])+1,'page tail lost')
    checks=[(('人工智能 就业','--all'),101),(('对外投资',),62),(('养老',),98),(('核聚变',),19)]
    for args,page in checks:
        results=query('--query',*args,'--limit','100')
        check(any(r['pdf_page']==page for r in results),f'retrieval miss: {args}')
    check(query('--page','15')[0]['printed_page']==10,'PDF page lookup')
    check(query('--printed-page','82')[0]['pdf_page']==87,'rotated page lookup')
    check(all(x['chapter']=='ch-41' for x in query('--chapter','41')),'chapter lookup')
    check(query('--chunk','p0101-c03')[0]['pdf_page']==101,'chunk lookup')
    check(query('--query','不可能命中的验证字符串甲乙丙丁')==[],'empty search fabricated results')
    check(query('--query',"' OR 1=1 --")==[],'query literal handling')
    check(len(query('--topic','出海'))>0,'topic search')
    metrics=query('--indicators');check(len(metrics)==20,'metric count')
    check(metrics[0]['column_2030']=='—' and metrics[0]['column_2025']=='5','GDP columns')
    check(metrics[11]['unit']=='百分点' and metrics[11]['column_annual_or_cumulative']=='〔6〕','childcare units')
    check(metrics[13]['name']=='单位GDP二氧化碳排放降低' and metrics[13]['column_annual_or_cumulative']=='〔17〕','carbon intensity')
    check(metrics[5]['baseline_reference']==metrics[17]['baseline_reference']=='2024','baseline footnotes')
    check(len(metrics[9]['subindicators'])==2,'medical submetrics')
    bad=subprocess.run([sys.executable,str(ROOT/'scripts/query.py'),'--page','141'],capture_output=True)
    check(bad.returncode!=0,'invalid page silently accepted')
    con.close();print('PASS: source hash, 140 pages, all chunk lines, 274 nodes, page/citation boundaries, DB/JSON parity, Chinese/topic lookup, special page, 20 metrics and failure behavior.')
if __name__=='__main__':main()
