"""Asignación exacta hijo→padre de la jerarquía de solicitudes (entrega 2026-06-26) por programación entera.
Restricciones: cada hijo tiene un padre; para cada padre y cada mes, la suma de las participaciones globales
de sus hijos iguala la del padre dentro del error de redondeo.
Objetivo: entre las asignaciones factibles, maximizar la correlación hijo-padre entre países (desempate).
Uso: python3 02_request_tree_milp.py <nivel_hijo: 1|0> <candidatos por hijo: all|k>"""
import pandas as pd, numpy as np, warnings, sys
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, vstack, csr_matrix
warnings.filterwarnings('ignore')
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv', dtype={'node_external_id':str})
names=d[d.category_name=='request'].drop_duplicates('node_external_id').set_index('node_external_id').node_name
r=d[(d.category_name=='request')&(d.metric_id=='pct')&(d.geo_level.isin(['country','subregion']))].copy()
r['g']=r.geo_id+'|'+r.date_start
glob=d[(d.category_name=='request')&(d.metric_id=='pct')&(d.geo_id=='GLOBAL')]
months=['2026-04-01','2026-05-01']
def solve(child_lvl, topk):
    P=r[r.hierarchy_level==child_lvl+1].pivot_table(index='node_external_id',columns='g',values='value')
    C=r[r.hierarchy_level==child_lvl].pivot_table(index='node_external_id',columns='g',values='value')
    gv={m:glob[(glob.date_start==m)] for m in months}
    kids=sorted(set(glob[glob.hierarchy_level==child_lvl].node_external_id))
    pars=sorted(set(glob[glob.hierarchy_level==child_lvl+1].node_external_id))
    cv={m:gv[m][gv[m].hierarchy_level==child_lvl].set_index('node_external_id').value for m in months}
    pv={m:gv[m][gv[m].hierarchy_level==child_lvl+1].set_index('node_external_id').value for m in months}
    Ca=C.reindex(kids); Pa=P.reindex(pars)
    # correlación por pares usando países-mes donde ambos están publicados
    X=Ca.values; Y=Pa.values
    rho=np.zeros((len(kids),len(pars)))
    for a in range(len(kids)):
        for b in range(len(pars)):
            m=~np.isnan(X[a])&~np.isnan(Y[b])
            if m.sum()>=8 and X[a][m].std()>0 and Y[b][m].std()>0: rho[a,b]=np.corrcoef(X[a][m],Y[b][m])[0,1]
    rho=pd.DataFrame(rho,index=kids,columns=pars)
    cand=[(j,k) for j in kids for k in (pars if topk is None else rho.loc[j].nlargest(topk).index)]
    idx={jk:i for i,jk in enumerate(cand)}; n=len(cand)
    A=[];lb=[];ub=[]
    for j in kids:
        row=np.zeros(n)
        for k in pars:
            if (j,k) in idx: row[idx[(j,k)]]=1
        A.append(row);lb.append(1);ub.append(1)
    for m in months:
        for k in pars:
            row=np.zeros(n)
            for j in kids:
                if (j,k) in idx: row[idx[(j,k)]]=cv[m].get(j,0.0)
            tol=0.06  # redondeo a 2 decimales de ~10-30 hijos más el padre
            A.append(row);lb.append(pv[m][k]-tol);ub.append(pv[m][k]+tol)
    # cota local: en cada país/subregión-mes, los hijos publicados de un padre no pueden sumar más que el padre
    Cg=Ca.reindex(columns=Pa.columns); G=list(Pa.columns)
    rows=[];ubl=[]
    for k in pars:
        kids_k=[j for j in kids if (j,k) in idx]
        for gi,g in enumerate(G):
            pk=Pa.loc[k,g]
            if np.isnan(pk): continue
            vals=[(idx[(j,k)],Cg.loc[j,g]) for j in kids_k if not np.isnan(Cg.loc[j,g])]
            if len(vals)<2: continue
            rows.append(vals); ubl.append(pk+0.005*(len(vals)+1))
    M=lil_matrix((len(rows),n))
    for i,vals in enumerate(rows):
        for c,v in vals: M[i,c]=v
    print('restricciones locales:',len(rows))
    A=vstack([csr_matrix(np.array(A)),M.tocsr()]); lb=list(lb)+[-np.inf]*len(rows); ub=list(ub)+ubl
    cobj=-np.array([rho.loc[j,k] for j,k in cand])
    res=milp(cobj,constraints=LinearConstraint(A,lb,ub),integrality=np.ones(n),bounds=Bounds(0,1),options={'time_limit':140})
    print('nivel',child_lvl,'estado',res.status,res.message)
    if res.x is None: return None
    sel=[cand[i] for i in range(n) if res.x[i]>0.5]
    out=pd.DataFrame(sel,columns=['child','parent'])
    out['level']=child_lvl; out['child_name']=out.child.map(names); out['parent_name']=out.parent.map(names)
    out['rho']=[rho.loc[j,k] for j,k in sel]
    for m in months: out['global_pct_'+m[:7]]=out.child.map(cv[m])
    chk=pd.DataFrame({m:out.groupby('parent')['global_pct_'+m[:7]].sum()-pd.Series(pv[m]) for m in months})
    print('máx |suma hijos - padre| por mes:',chk.abs().max().round(3).to_dict())
    return out
lvl=int(sys.argv[1]); topk=None if sys.argv[2]=='all' else int(sys.argv[2])
o=solve(lvl,topk)
if o is not None:
    o.to_csv(f'output/request_tree_level{lvl}.csv',index=False)
    print('rho de la asignación: mediana %.2f, RIC %.2f a %.2f'%(o.rho.median(),o.rho.quantile(.25),o.rho.quantile(.75)))
    if lvl==1:
        for p in ['Research & Intelligence','Education & Learning']:
            print('\n==',p); print(o[o.parent_name==p].sort_values('global_pct_2026-05',ascending=False)[['child_name','global_pct_2026-05','rho']].round(2).to_string(index=False))
