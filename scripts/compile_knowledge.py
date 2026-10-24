#!/usr/bin/env python3
"""Compile audited knowledge separately from immutable source text. Standard library only."""
import json,re,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'assets/data'
def read(name):return json.loads((D/name).read_text())
def write(name,obj): (D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def norm(t):return re.sub(r'\s+','',t)
def main():
    pages={p['pdf_page']:p for p in map(json.loads,(D/'pages.jsonl').read_text().splitlines())}
    chunks=list(map(json.loads,(D/'chunks.jsonl').read_text().splitlines()))
    nodes=read('structure.json'); index={n['id']:n for n in nodes}
    audits=[json.loads(l) for f in sorted((ROOT/'assets/quality').glob('visual-audit-*.jsonl')) for l in f.read_text().splitlines()]
    ba={a['box_id']:a for a in audits if 'box_id' in a}
    chapters=read('chapter_analysis.json')
    assert [c['chapter'] for c in chapters]==list(range(1,63))
    for c in chapters:
        nid=f"ch-{c['chapter']:02d}";n=index[nid];cs=[x for x in chunks if x['chapter']==nid]
        c.update(title=n['title'],label=n['label'],source_chunks=[x['id'] for x in cs],pdf_pages=sorted({x['pdf_page'] for x in cs}),sections=[x for x in nodes if x['parent']==nid and x['kind']=='section'])
        c['printed_pages']=[p-5 for p in c['pdf_pages']]
        c['citation']=f"《十五五规划纲要》{n['label']}，印刷第{c['printed_pages'][0]}—{c['printed_pages'][-1]}页（PDF第{c['pdf_pages'][0]}—{c['pdf_pages'][-1]}页）"
        assert all(1<=k<=62 for k in c['related_chapters'])
    write('chapter_analysis.json',chapters)
    labels={'policy_summary':'规划内容转述','transmission_analysis':'传导分析','decision_applications':'候选应用','limits_and_counterpoints':'限制与反向证据','monitoring_questions':'后续观察'}
    for start,end in [(1,10),(11,20),(21,30),(31,40),(41,50),(51,62)]:
        selected=chapters[start-1:end]
        out=['# 第%d—%d章解读\n\n以下是辅助分析，不是官方解读；引文和数字回到原文核对。\n'%(start,end),'目录：'+'；'.join(f"{c['chapter']} {c['title']}" for c in selected)]
        for c in selected:
            out += [f"\n## {c['label']} {c['title']}\n",c['citation']+'。',*(f"\n**{v}**：{c[k]}" for k,v in labels.items()),'\n关联章节：'+','.join(map(str,c['related_chapters']))+'。原文检索：`python3 scripts/query.py --chapter '+str(c['chapter'])+'`。']
        (ROOT/f'references/chapters-{start:02d}-{end:02d}.md').write_text('\n'.join(out)+'\n')
    boxes=[]
    for n in [n for n in nodes if n['kind']=='box']:
        cs=[x for x in chunks if x['box']==n['id']]
        b={'id':n['id'],'number':n['number'],'title':n['title'],'chapter':int(n['parent'][3:]),'pdf_pages':sorted({x['pdf_page'] for x in cs}),'source_chunks':[x['id'] for x in cs],'classification':'source_transcription','visual_checked':'2026-10-23'}
        if n['number']==1:
            b['items']=read('indicators.json')['indicators'];b['item_type']='indicators'
        else:
            lines=[dict(l,pdf_page=c['pdf_page'],line_number=i+1,chunk_id=c['id']) for c in cs for i,l in enumerate(pages[c['pdf_page']]['lines']) if c['line_start']<=i+1<=c['line_end']]
            starts=[i for i,l in enumerate(lines) if re.fullmatch(r'\d{2}',l['text'])]
            items=[]
            for j,start in enumerate(starts):
                stop=starts[j+1] if j+1<len(starts) else len(lines); segment=lines[start:stop]
                k=1;title=[]
                while k<len(segment) and 'FZKTK' in segment[k]['font']:
                    title.append(segment[k]['text']);k+=1
                assert title,(n['id'],segment[:3])
                item={'id':n['id']+'-i'+segment[0]['text'],'number':int(segment[0]['text']),'title':''.join(title),'text':'\n'.join(l['text'] for l in segment[k:]),'pdf_pages':sorted({l['pdf_page'] for l in segment}),'source_chunks':list(dict.fromkeys(l['chunk_id'] for l in segment)),'line_ranges':[]}
                for p in item['pdf_pages']:
                    ls=[l['line_number'] for l in segment if l['pdf_page']==p];item['line_ranges'].append({'pdf_page':p,'line_start':min(ls),'line_end':max(ls)})
                item['stage_cues']=[word for word in ['研究论证','探索','试点','建设','建成','推进','实施'] if word in item['text']]
                item['stage_note']='仅为原文词语提示；同条不同子项目可能处于不同阶段，不代表实际进度。'
                items.append(item)
            expected=ba[n['id']]['item_titles']
            assert [norm(f"{x['number']:02d} {x['title']}") for x in items]==[norm(t) for t in expected],(n['id'],[x['title'] for x in items],expected)
            b['items']=items;b['item_type']='project_entries'
        b['printed_pages']=[p-5 for p in b['pdf_pages']]
        b['citation']=f"《十五五规划纲要》专栏{b['number']}，印刷第{'、'.join(map(str,b['printed_pages']))}页（PDF第{'、'.join(map(str,b['pdf_pages']))}页）"
        if b['item_type']=='project_entries':
            for item in b['items']:
                item['printed_pages']=[p-5 for p in item['pdf_pages']]
                item['citation']=f"《十五五规划纲要》专栏{b['number']}第{item['number']:02d}项，印刷第{'、'.join(map(str,item['printed_pages']))}页（PDF第{'、'.join(map(str,item['pdf_pages']))}页）"
        boxes.append(b)
    write('boxes.json',boxes)
    figures=[];heritage=[]
    for a in audits:
        if 'figure_id' not in a:continue
        if a['figure_id']=='figure-02-register':
            for title in a['item_titles']:
                no,name=title.split(' ',1);i=int(no)
                heritage.append({'id':f'heritage-{i:02d}','number':i,'title':name,'category':'世界文化遗产' if i<=41 else '世界自然遗产' if i<=56 else '世界自然文化双遗产','pdf_page':87,'printed_page':82,'path':'图2 中国世界遗产名录（主编号）','classification':'visually_transcribed_normalized','snapshot':'规划2026年3月版本，非当前名录','note':'主编号；系列子项须看原PDF，不能以子点数量代替独立遗产数量。','text':f'{i} {name}'})
        else:
            p=a['pdf_pages'][0]
            figures.append({'id':a['figure_id'],'title':a['item_titles'][0],'legend':[x.removeprefix('图例：') for x in a['item_titles'][1:]],'pdf_page':p,'printed_page':p-5,'scope':a['scope'],'source_chunks':[x['id'] for x in chunks if x['pdf_page']==p],'classification':'visual_description_not_geodata','visual_checked':'2026-10-23'})
    assert len(heritage)==60 and len(figures)==3
    write('figures.json',figures);write('heritage.json',heritage)
    (ROOT/'references/figures.md').write_text('# 地图与横版名录\n\n三张地图均为示意；不支持精确选址、行政边界、线路长度或项目数量推断。主名录为规划版本快照，不是当前世界遗产总数。\n\n'+'\n\n'.join(f"## {f['title']}\n\n印刷第{f['printed_page']}页，PDF第{f['pdf_page']}页。图例：{'；'.join(f['legend'])}。\n\n{f['scope']}" for f in figures)+'\n\n## 图2主名录\n\nPDF第87页横版四列，原始文本混序，禁止连续拼读引用。用 `--heritage` 或 `--query 名称` 读取已视觉配对的60个主条目；系列子项与编号请看原图。57泰山、58黄山、59峨眉山-乐山大佛、60武夷山为双遗产。160为含嘉仓仓窖编号，不是数量指标。\n')
    sectors=read('sector_analysis.json') if (D/'sector_analysis.json').exists() else []
    for s in sectors:
        assert all(1<=k<=62 for k in s['chapters'])
        s['source_chapters']=[{'chapter':k,'title':chapters[k-1]['title'],'citation':chapters[k-1]['citation']} for k in s['chapters']]
    if sectors:
        write('sector_analysis.json',sectors)
        fields={'transmission':'政策到任务的分析链','candidate_tasks':'候选任务','entry_conditions':'进入条件','current_evidence_needed':'必须补查','disconfirming_signals':'反向信号','low_cost_experiment':'低成本验证'}
        out=['# 行业决策路径\n\n目录：'+'；'.join(x['title'] for x in sectors)+'。\n\n全部为分析假设，不是官方职业推荐、已发生的市场机会或当前岗位清单。先按用户条件选少数路径，核对原文章节并补现实证据。行业次序不代表优先级。']
        for x in sectors:
            out += [f"\n## {x['title']}（{x['id']}）\n",'关联原文章节：'+','.join(map(str,x['chapters']))+'。',*(f"\n**{v}**：{x[k]}" for k,v in fields.items())]
        (ROOT/'references/industry-pathways.md').write_text('\n'.join(out)+'\n')
    con=sqlite3.connect(D/'plan.sqlite')
    for table,rows,key in [('chapter_analysis',chapters,'chapter'),('boxes',boxes,'id'),('figures',figures,'id'),('heritage',heritage,'id'),('sector_analysis',sectors,'id')]:
        con.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY,data_json TEXT NOT NULL)')
        con.execute(f'DELETE FROM {table}')
        con.executemany(f'INSERT INTO {table} VALUES (?,?)',[(str(r[key]),json.dumps(r,ensure_ascii=False)) for r in rows])
    m=read('manifest.json');m.update(skill_version='2.0',knowledge={'chapter_cards':len(chapters),'boxes':len(boxes),'project_entries':sum(len(b['items']) for b in boxes[1:]),'figures':len(figures),'heritage_main_entries':len(heritage),'sector_cards':len(sectors),'analysis_classification':'Assistant analysis, not official interpretation','visual_check_date':'2026-10-23'})
    write('manifest.json',m)
    con.executemany('INSERT OR REPLACE INTO metadata VALUES (?,?)',[(k,json.dumps(v,ensure_ascii=False)) for k,v in m.items()]);con.commit();con.close()
    print(json.dumps(m['knowledge'],ensure_ascii=False))
if __name__=='__main__':main()
