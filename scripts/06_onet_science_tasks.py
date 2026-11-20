"""Uso de Claude en tareas O*NET de ocupaciones científicas y de docencia universitaria (SOC 19-*, 25-1*, 15-2*),
entrega 2026-06-26. Se comparan solo las 12 tareas publicadas para los seis grandes de Latinoamérica, Estados Unidos
y el agregado global en ambos meses; el mapa a flujos del paper de OpenAI está en scripts/onet_science_task_map.csv.
O*NET asigna la conversación a la tarea por contenido, no por la ocupación de quien escribe."""
import pandas as pd
mp=pd.read_csv('scripts/onet_science_task_map.csv',dtype={'task_id':str}).set_index('task_id')
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv', dtype={'node_external_id':str})
o=d[(d.category_name=='onet')&(d.hierarchy_level==0)&(d.metric_id=='pct')&(d.geo_level.isin(['global','country']))&(d.node_external_id.isin(mp.index))]
LAT6=['BRA','MEX','COL','ARG','CHL','PER']
for m,g in o.groupby('date_start'):
    X=g.pivot_table(index='geo_id',columns='node_external_id',values='value')[mp.index].dropna()
    tot=X.sum(axis=1); comp=X.T.groupby(mp.workflow_openai).sum().T.div(tot,axis=0)*100
    c=tot.drop('GLOBAL'); rk=c.rank(ascending=False).astype(int)
    print(f'\n== {m[:7]}: países con las 12 tareas publicadas n={len(c)}; % del uso total: mediana {c.median():.2f} RIC {c.quantile(.25):.2f}-{c.quantile(.75):.2f} | GLOBAL {tot["GLOBAL"]:.2f}')
    print('  '+' '.join(f'{k}:{tot[k]:.2f}(#{rk[k]})' for k in LAT6+['USA']))
    cc=comp.drop('GLOBAL')
    for w in comp.columns:
        print(f'  {w}: mundo mediana {cc[w].median():.1f} RIC {cc[w].quantile(.25):.1f}-{cc[w].quantile(.75):.1f} | GLOBAL {comp.loc["GLOBAL",w]:.1f} | '+' '.join(f'{k}:{comp.loc[k,w]:.1f}' for k in LAT6+['USA']))
    comp.assign(total_pct=tot).to_csv(f'output/onet_science_tasks_{m[:7]}.csv')
