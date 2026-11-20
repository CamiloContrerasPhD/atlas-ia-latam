"""Comparación justa del perfil académico: solo categorías detalladas publicadas para TODOS los países comparados
(seis grandes de Latinoamérica y Estados Unidos) en ambos meses. Distribución mundial: países donde ese mismo
conjunto está completo. Reporta participación académica total y composición por flujo de trabajo (sin 'conceptos')."""
import pandas as pd, numpy as np
mp=pd.read_csv('scripts/scholarly_request_map.csv'); mp=mp[mp.workflow_openai!='Conceptos disciplinarios']
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv', dtype={'node_external_id':str})
q=d[(d.category_name=='request')&(d.metric_id=='pct')&(d.hierarchy_level==0)&(d.geo_level.isin(['global','country']))&(d.node_name.isin(mp.node_name))]
LAT6=['BRA','MEX','COL','ARG','CHL','PER']; REF=LAT6+['USA','GLOBAL']
W={m[:7]:g.pivot_table(index='geo_id',columns='node_name',values='value') for m,g in q.groupby('date_start')}
common=[n for n in mp.node_name if all(n in W[m].columns and W[m].loc[REF,n].notna().all() for m in W)]
print('categorías comunes:',common)
wf=mp.set_index('node_name').workflow_openai
out=[]
for m,X in W.items():
    X=X[common].dropna()            # países con el conjunto completo
    tot=X.sum(axis=1)
    comp=X.T.groupby(wf.reindex(common)).sum().T.div(tot,axis=0)*100
    ctry=tot.drop('GLOBAL')
    print(f'\n== {m}: países con el conjunto completo n={len(ctry)}')
    print(f'participación académica (% del uso total): mundo mediana {ctry.median():.2f} RIC {ctry.quantile(.25):.2f}-{ctry.quantile(.75):.2f} | GLOBAL agregado {tot["GLOBAL"]:.2f}')
    rk=ctry.rank(ascending=False).astype(int)
    print('  '+' '.join(f'{c}:{tot[c]:.2f}(#{rk[c]})' for c in LAT6+['USA']))
    cc=comp.drop('GLOBAL')
    for w in comp.columns:
        print(f'  {w}: mundo mediana {cc[w].median():.1f} RIC {cc[w].quantile(.25):.1f}-{cc[w].quantile(.75):.1f} | GLOBAL {comp.loc["GLOBAL",w]:.1f} | '+' '.join(f'{c}:{comp.loc[c,w]:.1f}' for c in LAT6+['USA']))
    comp.assign(total_pct=tot,month=m).to_csv(f'output/scholarly_common_items_{m}.csv')
# Contribuciones de cada categoría en mayo, para leer qué mueve el total
X=W['2026-05'][common]
print('\nMayo, categoría por país (% del uso total):'); print(X.loc[REF].T.round(2).to_string())
