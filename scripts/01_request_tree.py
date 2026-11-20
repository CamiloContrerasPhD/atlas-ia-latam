"""Reconstruye la jerarquía de categorías de solicitud (request) del Economic Index, entrega 2026-06-26.
El CSV publica cada nivel (2 = mayor, 1 = menor, 0 = detallado) sin decir qué hijo pertenece a qué padre.
Regla: cada hijo se asigna al padre con cuya participación más correlaciona entre países-mes;
validación: la suma de las participaciones globales de los hijos asignados debe igualar la del padre."""
import pandas as pd, numpy as np
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv', dtype={'node_external_id':str})
r=d[(d.category_name=='request')&(d.metric_id=='pct')&(d.geo_level.isin(['country','subregion']))].copy()
r['g']=r.geo_id+'|'+r.date_start
def mat(level):
    return r[r.hierarchy_level==level].pivot_table(index='node_external_id',columns='g',values='value')
glob=d[(d.category_name=='request')&(d.metric_id=='pct')&(d.geo_id=='GLOBAL')]
names=d[d.category_name=='request'].drop_duplicates('node_external_id').set_index('node_external_id').node_name
out=[]
for child_lvl,parent_lvl in [(1,2),(0,1)]:
    P=mat(parent_lvl); C=mat(child_lvl)
    gl_ids=set(glob[glob.hierarchy_level==child_lvl].node_external_id)
    for cid in gl_ids:
        best=(None,-2,0)
        if cid in C.index:
            c=C.loc[cid]
            for pid in P.index:
                m=c.notna()&P.loc[pid].notna()
                if m.sum()>=8:
                    rho=np.corrcoef(c[m],P.loc[pid][m])[0,1]
                    if rho>best[1]: best=(pid,rho,int(m.sum()))
        out.append(dict(level=child_lvl,child=cid,child_name=names.get(cid),parent=best[0],parent_name=names.get(best[0]),rho=best[1],n=best[2]))
a=pd.DataFrame(out); a.to_csv('output/request_tree_reconstructed.csv',index=False)
# validación por sumas globales
for lvl in [1,0]:
    for ds in ['2026-04-01','2026-05-01']:
        gc=glob[(glob.hierarchy_level==lvl)&(glob.date_start==ds)].set_index('node_external_id').value
        gp=glob[(glob.hierarchy_level==lvl+1)&(glob.date_start==ds)].set_index('node_external_id').value
        s=a[a.level==lvl].assign(v=lambda x:x.child.map(gc)).groupby('parent').v.agg(['sum','count'])
        s['parent_val']=s.index.map(gp); s['diff']=s['sum']-s['parent_val']
        unassigned=a[(a.level==lvl)&a.parent.isna()].child.map(gc).sum()
        print(f'nivel {lvl} {ds}: padres {len(s)}, |diff| mediana {s["diff"].abs().median():.3f}, max {s["diff"].abs().max():.2f}, hijos sin asignar suman {unassigned:.2f}')
        if lvl==1: print(s.assign(name=s.index.map(names)).sort_values('diff')[['name','count','sum','parent_val','diff']].round(2).to_string())
print(a.groupby('level').rho.describe())
