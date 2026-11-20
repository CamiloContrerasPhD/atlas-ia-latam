"""Perfil de solicitudes académicas y científicas por país (entrega 2026-06-26, nivel detallado de 'request').
Instrumento: scripts/scholarly_request_map.csv asigna cada categoría detallada a un flujo de trabajo del paper
de OpenAI (Liao, Shan y Chatterji, 2026). Las celdas no publicadas se tratan como no observadas (no como cero);
'cobertura' = fracción de la masa global del grupo cuyas categorías sí se publicaron para ese país."""
import pandas as pd, numpy as np
mp=pd.read_csv('scripts/scholarly_request_map.csv')
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv', dtype={'node_external_id':str})
q=d[(d.category_name=='request')&(d.metric_id=='pct')&(d.hierarchy_level==0)&(d.geo_level.isin(['global','country']))]
q=q[q.node_name.isin(mp.node_name)].merge(mp,on='node_name')
LAT6=['BRA','MEX','COL','ARG','CHL','PER']
rows=[]
for ds,qq in q.groupby('date_start'):
    W=qq.pivot_table(index='geo_id',columns='node_name',values='value')
    gl=W.loc['GLOBAL']
    for wf,names in mp.groupby('workflow_openai').node_name:
        names=[n for n in names if n in W.columns]
        s=W[names].sum(axis=1,min_count=1)
        cov=W[names].notna().mul(gl[names],axis=1).sum(axis=1)/gl[names].sum()
        for g in W.index: rows.append(dict(month=ds[:7],geo=g,workflow=wf,pct=s[g],coverage=cov[g]))
R=pd.DataFrame(rows); R.to_csv('output/scholarly_profile_by_country.csv',index=False)
# total académico excluyendo conceptos disciplinarios
tot=R[R.workflow!='Conceptos disciplinarios'].groupby(['month','geo']).agg(pct=('pct','sum'),cov=('coverage','mean')).reset_index()
for m in ['2026-04','2026-05']:
    t=tot[tot.month==m].set_index('geo')
    ctry=t.drop('GLOBAL')
    full=ctry[ctry['cov']>0.9]
    print(f'\n{m}: total académico (sin conceptos). GLOBAL {t.loc["GLOBAL","pct"]:.2f} | países con cobertura>0.9: n={len(full)}, mediana {full.pct.median():.2f}, RIC {full.pct.quantile(.25):.2f}-{full.pct.quantile(.75):.2f}')
    rk=full.pct.rank(ascending=False)
    for c in LAT6: print(f'  {c}: {t.loc[c,"pct"]:.2f} (cobertura {t.loc[c,"cov"]:.2f}, puesto {int(rk[c]) if c in rk else "NA"} de {len(full)})')
print('\nPor flujo, mayo 2026 (pct del uso total del país; cobertura entre paréntesis):')
P=R[R.month=='2026-05'].pivot_table(index='workflow',columns='geo',values='pct')
C=R[R.month=='2026-05'].pivot_table(index='workflow',columns='geo',values='coverage')
cols=['GLOBAL']+LAT6+['USA']
print(P[cols].round(2).to_string()); print(C[cols].round(2).to_string())
# composición: participación de cada flujo dentro del total académico
comp=P[cols].drop('Conceptos disciplinarios').div(P[cols].drop('Conceptos disciplinarios').sum())*100
print('\nComposición dentro del uso académico (%):'); print(comp.round(1).to_string())
