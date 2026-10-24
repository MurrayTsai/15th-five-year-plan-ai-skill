#!/usr/bin/env python3
"""Create/validate task-local evidence records; never verifies factual truth or fetches URLs."""
import argparse,datetime,json,sys
TEMPLATE={'id':'replace-with-stable-id','claim':'','evidence_type':'official_rule','title':'','publisher':'','url':'','published_on':None,'data_period':None,'retrieved_on':None,'jurisdiction':'','document_status':'unknown','effective_on':None,'expires_on':None,'related_chapters':[],'paraphrase':'','limitations':'','verification':'not_checked','review_after':None,'supersedes':[]}
TYPES={'official_rule','official_plan','official_statistics','project_record','company_disclosure','job_posting','interview','research','other'}
STATUS={'draft','issued','in_force','expired','repealed','unknown','not_applicable'}
VERIFY={'full_text_checked','partial','not_checked'}
def validate(rows,asof):
    errors=[];warnings=[];seen=set()
    if not isinstance(rows,list):return ['top level must be an array'],[]
    for i,r in enumerate(rows):
        tag=f'record {i+1}'
        if not isinstance(r,dict):errors.append(tag+': expected object');continue
        missing=set(TEMPLATE)-set(r)
        if missing:errors.append(tag+': missing '+','.join(sorted(missing)))
        rid=r.get('id')
        if not isinstance(rid,str) or not rid or rid in seen:errors.append(tag+': invalid/duplicate ID')
        else:seen.add(rid)
        for k in ['claim','title','publisher','jurisdiction','paraphrase']:
            if not isinstance(r.get(k),str) or not r[k].strip():errors.append(tag+': required '+k)
        if r.get('evidence_type') not in TYPES:errors.append(tag+': invalid evidence_type')
        if r.get('document_status') not in STATUS:errors.append(tag+': invalid document_status')
        if r.get('verification') not in VERIFY:errors.append(tag+': invalid verification')
        if not isinstance(r.get('url'),str) or not r['url'].startswith(('https://','http://')):errors.append(tag+': source URL required')
        chapters=r.get('related_chapters')
        if not isinstance(chapters,list) or any(type(n) is not int or not 1<=n<=62 for n in chapters):errors.append(tag+': invalid chapters')
        dates={}
        for k in ['published_on','retrieved_on','effective_on','expires_on','review_after']:
            v=r.get(k)
            if v is None:continue
            try:dates[k]=datetime.date.fromisoformat(v)
            except (ValueError,TypeError):errors.append(tag+': invalid '+k)
        if 'retrieved_on' not in dates:warnings.append(tag+': retrieval date unknown')
        for k in ['published_on','retrieved_on']:
            if k in dates and dates[k]>asof:errors.append(tag+': '+k+' is after as-of date')
        if dates.get('effective_on',asof)>asof:warnings.append(tag+': not yet effective')
        if dates.get('expires_on',asof)<asof:warnings.append(tag+': stated validity expired')
        if dates.get('review_after',asof)>asof:pass
        elif 'review_after' in dates:warnings.append(tag+': review due; not automatically invalid')
        if 'effective_on' in dates and 'expires_on' in dates and dates['expires_on']<dates['effective_on']:errors.append(tag+': expires before effective')
        if r.get('verification')!='full_text_checked':warnings.append(tag+': full text not checked')
        if r.get('document_status') in ['draft','expired','repealed','unknown']:warnings.append(tag+': cannot assume presently applicable rule')
        if not isinstance(r.get('supersedes'),list) or any(not isinstance(x,str) for x in r.get('supersedes',[])):errors.append(tag+': supersedes must be ID list')
    return errors,warnings

def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--template',action='store_true');g.add_argument('--validate',type=str);p.add_argument('--as-of',type=datetime.date.fromisoformat)
    a=p.parse_args()
    if a.template:print(json.dumps([TEMPLATE],ensure_ascii=False,indent=2));return
    if not a.as_of:p.error('--as-of YYYY-MM-DD is required; use user/client date')
    try:
        with open(a.validate) as f:rows=json.load(f)
    except (OSError,ValueError) as e:p.error(str(e))
    errors,warnings=validate(rows,a.as_of)
    print(json.dumps({'structurally_valid':not errors,'errors':errors,'warnings':warnings,'note':'Only structural/date checks. This does not establish factual correctness or legal applicability.'},ensure_ascii=False,indent=2))
    sys.exit(1 if errors else 0)
if __name__=='__main__':main()
