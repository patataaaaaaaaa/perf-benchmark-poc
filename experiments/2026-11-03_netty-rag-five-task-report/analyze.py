"""First five chronological JVM blocks only; paired descriptive statistics, no new runs."""
import json, math, statistics as st, hashlib, csv
from pathlib import Path
R=Path(__file__).resolve().parent
D=json.loads((R/'results/server-export.json').read_text())
assert D['verification']['passed']
def gm(a):return math.exp(st.mean(math.log(x) for x in a))
metrics={'cpu':'resource.cpu.ns.per.op','allocation':'gc.alloc.rate.norm','read':'resource.storage.read_bytes.per.op','write':'resource.storage.write_bytes.per.op'}
values={}; provenance=[]
for task,t in D['tasks'].items():
 for b in t['blocks']:
  rows={r['version']:r['rows'] for r in b['records']}
  for rec in b['records']:
   provenance.append({'task':task,'phase':b['phase'],'block':b['block'],'version':rec['version'],'marker_sha256':b['marker_sha256'],'files':rec['audit']['files'],'compiled_class_sha256':rec['audit']['primary']['compiled_class_sha256'],'audit_passed':rec['audit']['passed'],'four_metrics_complete':rec['audit']['full_four_categories'],'GC_per_iteration_complete':rec['audit']['GC_per_iteration_complete']})
  for v,rs in rows.items():
   for r,o in zip(rs,rows['original']):
    key=lambda x: json.dumps([x['benchmark'],x.get('params',{}),x['mode'],x['primaryMetric']['scoreUnit']],sort_keys=True)
    assert key(r)==key(o)
    if v=='original':continue
    sec={k.lstrip('·'):v['score'] for k,v in r['secondaryMetrics'].items()}; os={k.lstrip('·'):v['score'] for k,v in o['secondaryMetrics'].items()}
    speed=r['primaryMetric']['score']/o['primaryMetric']['score'] if r['mode']=='thrpt' else o['primaryMetric']['score']/r['primaryMetric']['score']
    vals={'block':b['block'],'primary':r['primaryMetric']['score'],'original_primary':o['primaryMetric']['score'],'speedup':speed}
    for k,m in metrics.items(): vals[k]=sec[m]; vals['original_'+k]=os[m]
    # developer appears in both b72 phases: keep phase separate.
    values.setdefault((task,b['phase'],v,key(r)),[]).append(vals)
rows=[]
for (task,phase,v,scene),vs in values.items():
 assert len(vs)==5 and sorted(x['block'] for x in vs)==list(range(5))
 logs=[math.log(x['speedup']) for x in vs]; center=st.mean(logs); half=2.7764451051977987*st.stdev(logs)/math.sqrt(5)
 s=gm([x['speedup'] for x in vs]);ci=[math.exp(center-half),math.exp(center+half)]
 state='faster' if s>1.05 and ci[0]>1 else 'slower' if s<1/1.05 and ci[1]<1 else 'uncertain'
 row={'task':task,'phase':phase,'version':v,'scenario':json.loads(scene),'n':5,'speedup':s,'speedup_CI95_unadjusted':ci,'exploratory_state':state,'per_block':sorted(vs,key=lambda x:x['block'])}
 for k in metrics:
  row[k+'_mean']=st.mean(x[k] for x in vs);row['original_'+k+'_mean']=st.mean(x['original_'+k] for x in vs)
  row[k+'_ratio']=gm([x[k]/x['original_'+k] for x in vs]) if all(x[k]>0 and x['original_'+k]>0 for x in vs) else None
 rows.append(row)
summary={'source_export_sha256':hashlib.sha256((R/'results/server-export.json').read_bytes()).hexdigest(),'captured_utc':D['captured_utc'],'scope':'five completed tasks, first numbered blocks 0..4, exploratory; no official unprofiled score claim','verification':D['verification'],'attempts':D['attempts'],'rows':rows,'tasks':{}}
for task,t in D['tasks'].items():
 entry={'description':t['metadata']['description'],'scenarios':len(t['blocks'][0]['records'][0]['rows']),'conditions':{}}
 for c in 'ABC':
  aa=[a for a in D['attempts'] if a['task']==task and a['condition']==c];rr=[r for r in rows if r['task']==task and r['version'].startswith(c+'-')]
  e={'attempts':len(aa),'functional_pass':sum(bool(a['functional_pass']) for a in aa),'measured_patch_scenarios':len(rr),'speedup_geomean':gm([r['speedup'] for r in rr]),'states':{s:sum(r['exploratory_state']==s for r in rr) for s in ['faster','slower','uncertain']}}
  for k in metrics:
   ratios=[r[k+'_ratio'] for r in rr if r[k+'_ratio'] is not None]; e[k+'_ratio_geomean']=gm(ratios) if ratios else None;e[k+'_ratio_available']=len(ratios);e[k+'_delta_mean']=st.mean(r[k+'_mean']-r['original_'+k+'_mean'] for r in rr)
  entry['conditions'][c]=e
 summary['tasks'][task]=entry
(R/'results/analysis.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(R/'results/verification-manifest.json').write_text(json.dumps({'verification':D['verification'],'records':provenance},ensure_ascii=False,indent=2)+'\n')
with (R/'results/paired-metrics.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['task','phase','version','scenario','speedup','CI95_low','CI95_high','state','CPU_ratio','allocation_ratio','read_delta_Bop','write_delta_Bop'])
 for r in rows:w.writerow([r['task'],r['phase'],r['version'],json.dumps(r['scenario'],ensure_ascii=False),r['speedup'],*r['speedup_CI95_unadjusted'],r['exploratory_state'],r['cpu_ratio'],r['allocation_ratio'],r['read_mean']-r['original_read_mean'],r['write_mean']-r['original_write_mean']])
print(json.dumps(summary['tasks'],ensure_ascii=False,indent=2))
