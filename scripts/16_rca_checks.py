"""Pruebas de robustez de 15_rca_complexity.py:
(a) AUC de la densidad dentro de cada grupo ocupacional (compara países en el mismo grupo; descarta que la densidad solo
    capture grupos que crecen en todas partes), promedio ponderado por número de casos;
(b) ECI frente al tamaño del país (participación en el uso mundial) y ECI con el tamaño descontado;
(c) especializaciones estables: RCA ≥ 1,5 en t0 y en t1."""
import pandas as pd, numpy as np, runpy, io, contextlib
from sklearn.metrics import roc_auc_score
with contextlib.redirect_stdout(io.StringIO()):
    ns=runpy.run_path('scripts/15_rca_complexity.py')
v=pd.read_csv('output/rca_validation.csv'); v['grp']=v.iloc[:,1]
a=[];n=[]
for g,s in v.groupby('grp'):
    if s.y.nunique()==2 and len(s)>=10: a.append(roc_auc_score(s.y,s.dens)); n.append(len(s))
print('(a) AUC densidad dentro de grupo: promedio ponderado %.3f, mediana %.3f, RIC %.3f-%.3f, grupos %d'%(np.average(a,weights=n),np.median(a),np.percentile(a,25),np.percentile(a,75),len(a)))
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv',dtype={'node_external_id':str})
u=d[(d.geo_level=='country')&(d.category_name=='overall')&(d.metric_id=='usage_pct')].groupby('geo_id').value.mean()
Z=pd.read_csv('output/eci_t1.csv',index_col=0); Z['lsize']=np.log(u.reindex(Z.index))
print('(b) Spearman ECI vs log tamaño: %.2f | diversidad vs log tamaño: %.2f'%(Z.eci.corr(Z.lsize,method='spearman'),Z.diversidad.corr(Z.lsize,method='spearman')))
X=np.column_stack([np.ones(len(Z)),Z.lsize,Z.lgdp]); b=np.linalg.lstsq(X,Z.eci,rcond=None)[0]; Z['eci_sin_tamano']=Z.eci-X@b
LAT=['ARG','BOL','BRA','CHL','COL','CRI','DOM','ECU','MEX','PER']
rk=Z.eci_sin_tamano.rank(ascending=False).astype(int)
print('    ECI descontando tamaño e ingreso (puesto de %d):'%len(Z),{c:(round(Z.loc[c,'eci_sin_tamano'],2),int(rk[c])) for c in LAT if c in Z.index})
Z.to_csv('output/eci_t1.csv')
R=pd.read_csv('output/rca_latam.csv'); st=R[(R.rca_t0>=1.5)&(R.rca_t1>=1.5)].sort_values(['pais','rca_t1'],ascending=[True,False])
print('(c) especializaciones estables (RCA ≥ 1,5 en t0 y t1):')
for c,s in st.groupby('pais'): print('   ',c,' | '.join(f'{r.nombre} ({r.rca_t0:.1f}→{r.rca_t1:.1f})' for r in s.itertuples()))
