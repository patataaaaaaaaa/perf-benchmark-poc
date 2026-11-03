"""Read-only export of five completed tasks; run over SSH stdin. No model/measurement calls."""
import json, hashlib, datetime
from pathlib import Path
R=Path('/downloads/patataWJY/netty-cloud-evidence/netty-auto-large-rag-20261101T135052Z')
TASKS=['2791f0f','b72fea3','dd69a81','9abeaf1','feb804d']
def rd(p):return json.loads(p.read_bytes(),strict=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
out={'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tasks':{},'verification':{'files_checked':0,'failures':[]},'status':rd(R/'status.json'),'protocol':rd(R/'safe-five-protocol.json')}
compiled={}
for task in TASKS:
 c=next((R/'agent/fixtures').glob('*-'+task)); spec=rd(c/'inputs'/(task+'.json'))
 t={'metadata':spec['metadata'],'blocks':[]};out['tasks'][task]=t
 for phase in (['acceptance','remaining'] if task=='b72fea3' else ['formal']):
  for i in range(5):
   p=R/'blocks'/task/f'{phase}-{i}.json'; b=rd(p);assert b['accepted']
   dest={'phase':phase,'block':i,'marker_sha256':sha(p),'records':[]}
   for rec in b['records']:
    d=Path(rec['directory']);a=rec['audit']; assert a['passed'] and a['full_four_categories'] and a['GC_per_iteration_complete']
    for name,h in a['files'].items():
     out['verification']['files_checked']+=1
     if sha(d/name)!=h:out['verification']['failures'].append(str(d/name))
    key=(task,rec['version']);cl=a['primary']['compiled_class_sha256']
    if compiled.setdefault(key,cl)!=cl:out['verification']['failures'].append(str(key)+' bytecode changed')
    rows=rd(d/'jmh.json')
    assert all(len(v)==50 for row in rows for v in row['primaryMetric']['rawData'])
    dest['records'].append({'version':rec['version'],'directory':str(d),'audit':a,'rows':rows})
   t['blocks'].append(dest)
attempts=rd(R/'baseline-reuse.json')+[rd(p) for p in sorted((R/'attempts').glob('*.json'))]
out['attempts']=[]
for a in attempts:
 if a['task'] not in TASKS:continue
 ar=a.get('agent_result',{}); snap=a.get('snapshot')
 out['attempts'].append({k:a.get(k) for k in ['task','condition','replicate','version','functional_pass','stop_reason','context_ids','context_sha256','prompt_sha256','actual_request_context_verified']}|{'outcome':ar.get('outcome'),'error':ar.get('error'),'changed_files':ar.get('changed_files'),'patch_sha256':snap.get('patch_sha256') if snap else None})
 if snap:
  base=(Path('/downloads/patataWJY/netty-cloud-evidence/netty-rag-rigorous-20261030T040920Z/formal') if a['condition']=='A' else R/'agent')
  manifest=rd(base/'snapshots'/a['identity']/'manifest.json'); patch=base/'snapshots'/a['identity']/'agent.patch'
  if sha(patch)!=manifest['patch_sha256']:out['verification']['failures'].append(str(patch))
  c=next((R/'agent/fixtures').glob('*-'+a['task']))
  for name,h in manifest['source_sha256'].items():
   if sha(c/'sources'/a['task']/a['version']/name)!=h:out['verification']['failures'].append(a['identity']+name)
out['verification']['passed']=not out['verification']['failures']
print(json.dumps(out,ensure_ascii=False))
