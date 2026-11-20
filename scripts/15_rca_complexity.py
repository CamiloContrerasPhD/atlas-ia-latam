"""Especialización relativa (RCA), complejidad (ECI) y cercanía entre usos, validadas entre entregas.
Unidad: grupo menor de ocupaciones SOC (p. ej. 15-12 'Computer occupations'), al que se lleva cada tarea O*NET por su
enunciado (si un enunciado aparece en varias ocupaciones, su peso se reparte). t0 = promedio ago-2025 y nov-2025;
t1 = promedio abr-2026 y may-2026. Dentro de cada país, las participaciones se renormalizan sobre lo publicado.
RCA_cp = participación del grupo p en el país c / participación del grupo en el total de países (Balassa).
Cercanía entre grupos (Hidalgo et al.): φ_pq = Σ_c M_cp·M_cq / max(k_p, k_q), con M = 1{RCA ≥ 1}.
Densidad_cp = Σ_q φ_pq·M_cq / Σ_q φ_pq. Prueba: ¿la densidad en t0 predice nuevas especializaciones en t1?"""
import pandas as pd, numpy as np, re, pycountry, warnings
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
warnings.filterwarnings('ignore'); rng=np.random.default_rng(3)
norm=lambda s: re.sub(r'\s+',' ',str(s).strip().lower()).rstrip('.')
T=pd.read_csv('data/onet_task_statements.csv',dtype=str); T['k']=T.Task.map(norm); T['grp']=T['O*NET-SOC Code'].str[:4]
w={k:g.value_counts(normalize=True).to_dict() for k,g in T.groupby('k').grp}
SOC=pd.read_csv('data/soc_structure.csv',dtype=str); minor=SOC.dropna(subset=['Minor Group']).set_index(SOC['Minor Group'].dropna().str[:4])['SOC or O*NET-SOC 2019 Title'].to_dict()
def iso3(a):
    if len(a)==3: return a
    try: return pycountry.countries.get(alpha_2=a).alpha_3
    except Exception: return None
def old(fn):
    r=pd.read_csv('data/'+fn,low_memory=False); t=r[(r.geography=='country')&(r.facet=='onet_task')&(r.variable=='onet_task_pct')]
    return pd.DataFrame({'geo':t.geo_id.map(iso3),'k':t.cluster_name.map(norm),'v':t.value})
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv',dtype={'node_external_id':str})
o=d[(d.category_name=='onet')&(d.hierarchy_level==0)&(d.metric_id=='pct')&(d.geo_level=='country')]
def new(ds): t=o[o.date_start==ds]; return pd.DataFrame({'geo':t.geo_id,'k':t.node_name.map(norm),'v':t.value})
def to_grp(df):
    rows=[]
    for g,k,v in df[['geo','k','v']].itertuples(index=False):
        for p,f in w.get(k,{}).items(): rows.append((g,p,v*f))
    M=pd.DataFrame(rows,columns=['geo','grp','v']).groupby(['geo','grp']).v.sum().unstack(fill_value=0)
    return M.div(M.sum(axis=1),axis=0)
src={'2025-08':old('aei_enriched_claude_ai_2025-08-04_to_2025-08-11.csv'),'2025-11':old('aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv'),'2026-04':new('2026-04-01'),'2026-05':new('2026-05-01')}
match={k:(v.k.isin(w)).mean() for k,v in src.items()}; print('tareas con ocupación encontrada:',{k:round(x,3) for k,x in match.items()})
S={k:to_grp(v) for k,v in src.items()}
ntask={k:v.groupby('geo').k.nunique() for k,v in src.items()}
def avg(a,b):
    idx=S[a].index.intersection(S[b].index); cols=S[a].columns.union(S[b].columns)
    return (S[a].reindex(index=idx,columns=cols,fill_value=0)+S[b].reindex(index=idx,columns=cols,fill_value=0))/2
t0,t1=avg('2025-08','2025-11'),avg('2026-04','2026-05')
# países con al menos 10 tareas publicadas en cada una de las cuatro mediciones
keep=set.intersection(*[set(ntask[k][ntask[k]>=10].index) for k in ntask])
cols=t0.columns.union(t1.columns); C=sorted(keep&set(t0.index)&set(t1.index))
t0=t0.reindex(index=C,columns=cols,fill_value=0); t1=t1.reindex(index=C,columns=cols,fill_value=0)
cols=[c for c in cols if t0[c].sum()>0 and t1[c].sum()>0]; t0,t1=t0[cols],t1[cols]
print('países:',len(C),'grupos:',len(cols))
def rca(S): return S.div(S.sum(axis=1),axis=0).div(S.sum(axis=0)/S.values.sum(),axis=1)
R0,R1=rca(t0),rca(t1); M0=(R0>=1).astype(int)
k=M0.sum(axis=0).values; U=M0.T.values@M0.values; phi=U/np.maximum.outer(k,k); np.fill_diagonal(phi,0)
dens=pd.DataFrame((M0.values@phi)/phi.sum(axis=0),index=C,columns=cols)
cand=(R0<1).stack(); y=((R1>=1)&(R0<1)).stack()[cand]; Dn=dens.stack()[cand]; lr0=np.log(R0.stack()[cand]+0.01)
dfv=pd.DataFrame({'y':y.astype(int),'dens':Dn,'lr0':lr0}); dfv['geo']=[i[0] for i in dfv.index]
print('candidatos (RCA<1 en t0):',len(dfv),'| nuevas especializaciones:',int(dfv.y.sum()))
def auc_ci(yv,sc):
    a=roc_auc_score(yv,sc); bs=[]
    for _ in range(300):
        i=rng.integers(0,len(yv),len(yv))
        if yv[i].min()!=yv[i].max(): bs.append(roc_auc_score(yv[i],sc[i]))
    return a,np.percentile(bs,2.5),np.percentile(bs,97.5)
yv=dfv.y.values
for lab,sc in [('densidad',dfv.dens.values),('RCA en t0',dfv.lr0.values)]:
    a,l,h=auc_ci(yv,sc); print(f'AUC {lab}: {a:.3f} [{l:.3f}, {h:.3f}]')
# logística con validación cruzada por país: RCA t0 sola vs RCA t0 + densidad
p_base=np.zeros(len(dfv)); p_full=np.zeros(len(dfv))
for tr,te in GroupKFold(5).split(dfv,groups=dfv.geo):
    for cols_,out in [(['lr0'],p_base),(['lr0','dens'],p_full)]:
        m=LogisticRegression().fit(dfv.iloc[tr][cols_],yv[tr]); out[te]=m.predict_proba(dfv.iloc[te][cols_])[:,1]
for lab,sc in [('logística RCA t0',p_base),('logística RCA t0 + densidad',p_full)]:
    a,l,h=auc_ci(yv,sc); print(f'AUC fuera de muestra {lab}: {a:.3f} [{l:.3f}, {h:.3f}]')
# Complejidad (ECI) en t1
M1=(R1>=1).astype(float); kc=M1.sum(axis=1); kp=M1.sum(axis=0)
Mt=(M1.div(kc,axis=0)).values@(M1.div(kp,axis=1)).values.T
ev,vec=np.linalg.eig(Mt); idx=np.argsort(-ev.real)[1]; eci=pd.Series(vec[:,idx].real,index=C)
if np.corrcoef(eci,kc)[0,1]<0: eci=-eci
eci=(eci-eci.mean())/eci.std()
gdp=pd.read_csv('data/worldbank_gdp_pc_ppp_2022_2024.csv').sort_values('year').groupby('iso3').last().gdp_pc_ppp_current_intl
Z=pd.DataFrame({'eci':eci,'diversidad':kc,'lgdp':np.log(gdp.reindex(C))}).dropna()
print('ECI vs log PIB: Spearman %.2f | ECI vs diversidad: %.2f'%(Z.eci.corr(Z.lgdp,method='spearman'),Z.eci.corr(Z.diversidad,method='spearman')))
b=np.polyfit(Z.lgdp,Z.eci,1); Z['eci_resid']=Z.eci-np.polyval(b,Z.lgdp)
LAT=['ARG','BOL','BRA','CHL','COL','CRI','DOM','ECU','GTM','HND','MEX','PAN','PER','PRY','SLV','URY']
rk=Z.eci.rank(ascending=False).astype(int)
print('ECI (puesto de %d) y residuo por ingreso:'%len(Z), {c:(round(Z.loc[c,'eci'],2),int(rk[c]),round(Z.loc[c,'eci_resid'],2)) for c in LAT if c in Z.index})
# especializaciones y próximos usos para Colombia, México y Brasil
out=[]
for c in ['COL','MEX','BRA','ARG','CHL','PER']:
    if c not in C: continue
    top=R1.loc[c].sort_values(ascending=False).head(5)
    nxt=dens.loc[c][R0.loc[c]<1].sort_values(ascending=False).head(5)
    print(f'\n{c} especializaciones t1:',' | '.join(f'{minor.get(p,p)} {v:.1f}' for p,v in top.items()))
    print(f'{c} mayor densidad sin especialización t0:',' | '.join(f'{minor.get(p,p)} {v:.2f}' for p,v in nxt.items()))
    for p,v in R1.loc[c].items(): out.append(dict(pais=c,grupo=p,nombre=minor.get(p,p),rca_t0=R0.loc[c,p],rca_t1=v,densidad_t0=dens.loc[c,p]))
pd.DataFrame(out).to_csv('output/rca_latam.csv',index=False); Z.to_csv('output/eci_t1.csv'); dfv.to_csv('output/rca_validation.csv')
# todos los países (para el sitio): RCA en t0 y t1 y densidad, formato largo
pd.DataFrame([dict(pais=c,grupo=p,nombre=minor.get(p,p),rca_t0=R0.loc[c,p],rca_t1=R1.loc[c,p],densidad_t0=dens.loc[c,p]) for c in C for p in cols]).to_csv('output/rca_todos.csv',index=False)
