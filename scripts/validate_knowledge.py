#!/usr/bin/env python3
"""Regression checks for audited tables, provenance, unsafe layouts and evidence dates."""
import datetime,importlib.util,json,re,sqlite3,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'assets/data'
def read(name):return json.loads((D/name).read_text())
def q(*args):
    r=subprocess.run([sys.executable,str(R/'scripts/query.py'),*args,'--json'],capture_output=True,text=True,check=True)
    return json.loads(r.stdout)
def main():
    m=read('manifest.json');assert m['schema_version']==2 and m['skill_version']=='2.0'
    chapters=read('chapter_analysis.json');boxes=read('boxes.json');figures=read('figures.json');heritage=read('heritage.json');sectors=read('sector_analysis.json')
    chunks={c['id']:c for c in map(json.loads,(D/'chunks.jsonl').read_text().splitlines())}
    pages={p['pdf_page']:p for p in map(json.loads,(D/'pages.jsonl').read_text().splitlines())}
    assert len(chapters)==62 and len(sectors)==16 and len(boxes)==23 and len(figures)==3 and len(heritage)==60
    assert sum(len(b['items']) for b in boxes[1:])==122
    assert '——' not in next(n['title'] for n in read('structure.json') if n['id']=='ch-02-s02')
    for c in chapters:
        assert c['classification']=='assistant_analysis_not_official'
        assert c['source_chunks']==[i for i,x in chunks.items() if x['chapter']==f"ch-{c['chapter']:02d}"]
        assert c['pdf_pages']==sorted({chunks[i]['pdf_page'] for i in c['source_chunks']})
        assert all(c[k].strip() for k in ['policy_summary','transmission_analysis','decision_applications','limits_and_counterpoints','monitoring_questions'])
    assert '逐步减少梯度层次和服务差异' in chapters[44]['policy_summary']
    for b in boxes:
        assert all(chunks[i]['box']==b['id'] for i in b['source_chunks'])
        assert b['pdf_pages']==sorted({chunks[i]['pdf_page'] for i in b['source_chunks']})
        if b['number']==1:continue
        assert [x['number'] for x in b['items']]==list(range(1,len(b['items'])+1))
        for item in b['items']:
            original=[]
            for span in item['line_ranges']:
                original += pages[span['pdf_page']]['lines'][span['line_start']-1:span['line_end']]
            assert original[0]['text']==f"{item['number']:02d}"
            j=1;title=[]
            while j<len(original) and 'FZKTK' in original[j]['font']:title.append(original[j]['text']);j+=1
            assert ''.join(title)==item['title'] and '\n'.join(l['text'] for l in original[j:])==item['text']
    assert boxes[4]['pdf_pages']==[25,26] and boxes[21]['pdf_pages']==[118]
    assert all(chunks[i]['box'] is None for f in figures for i in f['source_chunks'])
    assert {r['number']:r['title'] for r in heritage if r['number']>=57}=={57:'泰山',58:'黄山',59:'峨眉山-乐山大佛',60:'武夷山'}
    assert [len([h for h in heritage if h['category']==c]) for c in ['世界文化遗产','世界自然遗产','世界自然文化双遗产']]==[41,15,4]
    con=sqlite3.connect(D/'plan.sqlite')
    for t,rows,key in [('chapter_analysis',chapters,'chapter'),('boxes',boxes,'id'),('figures',figures,'id'),('heritage',heritage,'id'),('sector_analysis',sectors,'id')]:
        actual={k:json.loads(v) for k,v in con.execute(f'SELECT id,data_json FROM {t}')};assert actual=={str(r[key]):r for r in rows},t
    con.close()
    for i in [1,41,62]:assert q('--interpret',str(i))['results'][0]['chapter']==i
    assert len(q('--box','3')['results'][0]['items'])==10
    assert len(q('--sectors')['results'])==16 and q('--sector','trade')['mode']=='assistant_analysis'
    assert len(q('--figures')['results'])==3 and len(q('--heritage')['results'])==60
    assert q('--query','泰山')['results'][0]['number']==57
    assert q('--chunk','heritage-60')['results'][0]['title']=='武夷山'
    for args in [('--page','87'),('--chunk','p0087-c01'),('--chapter','34')]:
        bad=[x for x in q(*args)['results'] if x.get('pdf_page')==87];assert bad and all('reading_order_warning' in x for x in bad)
    ctx=q('--context','p0020-c02')['results'];assert [x['id'] for x in ctx]==['p0020-c01','p0020-c02','p0021-c01'] and ctx[1]['context_role']=='target'
    cross=q('--query','人工智能 就业','--all','--search-scope','chapter')['results'];assert any(x['chapter']==41 for x in cross)
    for args in [('--interpret','63'),('--box','24'),('--sector','missing'),('--context','missing'),('--query',' '),('--page','0')]:
        assert subprocess.run([sys.executable,str(R/'scripts/query.py'),*args],capture_output=True).returncode!=0,args
    # Link checks catch missing progressive-disclosure resources.
    for md in [R/'SKILL.md',*list((R/'references').glob('*.md'))]:
        for target in re.findall(r'\]\(([^)]+)\)',md.read_text()):
            if not target.startswith(('http','sandbox:','#')):assert (md.parent/target.split('#')[0]).exists(),(md,target)
    spec=importlib.util.spec_from_file_location('evidence',R/'scripts/evidence.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
    row=dict(ev.TEMPLATE,id='fixture',claim='synthetic validation fixture',title='fixture',publisher='fixture',url='https://example.org/fixture',retrieved_on='2026-10-23',jurisdiction='fixture',paraphrase='Not factual evidence',verification='full_text_checked',document_status='issued',effective_on='2026-11-01')
    errors,warnings=ev.validate([row],datetime.date(2026,10,23));assert not errors and any('not yet effective' in w for w in warnings)
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'evidence.json';path.write_text(json.dumps([row]));r=subprocess.run([sys.executable,str(R/'scripts/evidence.py'),'--validate',str(path),'--as-of','2026-10-23'],capture_output=True,text=True);assert r.returncode==0 and json.loads(r.stdout)['structurally_valid']
        row['retrieved_on']='2026-10-24';path.write_text(json.dumps([row]));r=subprocess.run([sys.executable,str(R/'scripts/evidence.py'),'--validate',str(path),'--as-of','2026-10-23'],capture_output=True);assert r.returncode!=0
    print('PASS: 62 cards, 23 boxes/122 project entries, 3 maps, 60 heritage pairs, 16 sector cards; source ranges, DB parity, CLI, unsafe layouts, links and evidence date handling.')
if __name__=='__main__':main()
