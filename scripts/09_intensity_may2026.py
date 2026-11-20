"""Intensidad y propósito de uso, mayo 2026 (entrega 2026-06-26), con dos medidas de ingreso para el cociente
observado/esperado: PIB per cápita PPA (Banco Mundial, último año 2022-2024) y PIB nominal por persona en edad de
trabajar (FMI 2024, publicado por Anthropic en la entrega 2025-08). Propósito: trabajo, cursos, personal."""
import pandas as pd, numpy as np
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv',dtype={'node_external_id':str})
ov=d[(d.geo_level.isin(['country','global']))&(d.category_name=='overall')&(d.date_start=='2026-05-01')].pivot_table(index='geo_id',columns='metric_id',values='value')
wb=pd.read_csv('data/worldbank_gdp_pc_ppp_2022_2024.csv').sort_values('year').groupby('iso3').last().gdp_pc_ppp_current_intl
e=pd.read_csv('data/aei_enriched_claude_ai_2025-08-04_to_2025-08-11.csv',low_memory=False)
imf=e[(e.geography=='country')&(e.facet=='country')&(e.variable=='gdp_per_working_age_capita')].set_index('geo_id').value
aui=ov.usage_per_capita_index.drop('GLOBAL',errors='ignore').dropna(); aui=aui[aui>0]
LAT=['URY','CHL','CRI','ARG','COL','PER','BRA','PAN','MEX','ECU','DOM','BOL','SLV','PRY','GTM','HND']
out=pd.DataFrame({'aui':aui,'rank_aui':aui.rank(ascending=False).astype(int)})
for lab,g in [('ppa_bm',wb),('nominal_fmi',imf)]:
    s=aui[aui.index.isin(g.dropna().index)]; x=np.log(g[s.index]); y=np.log(s); b,a=np.polyfit(x,y,1); r=y-(a+b*x)
    out['obs_esp_'+lab]=np.exp(r)
    print(f'{lab}: n={len(s)} pendiente {b:.2f} R2 {1-(r**2).sum()/((y-y.mean())**2).sum():.2f} factor DE {np.exp(r.std(ddof=2)):.2f}')
print(f'AUI mundo: n={len(aui)} mediana {aui.median():.2f} RIC {aui.quantile(.25):.2f}-{aui.quantile(.75):.2f}')
print(out.loc[LAT].round(2).to_string())
U=ov[['use_case_work_pct','use_case_coursework_pct','use_case_personal_pct']]
W=U.drop('GLOBAL')
print('\nPropósito (porcentaje de conversaciones), mundo n='+str(len(W.dropna())))
for c in U.columns: print(f'  {c}: mediana {W[c].median():.1f} RIC {W[c].quantile(.25):.1f}-{W[c].quantile(.75):.1f} | GLOBAL {U.loc["GLOBAL",c]:.1f}')
print(U.loc[['BRA','MEX','COL','ARG','CHL','PER','USA']].round(1).to_string())
print('puesto de cursos (de mayor a menor):',W.use_case_coursework_pct.rank(ascending=False).loc[['BRA','MEX','COL','ARG','CHL','PER']].astype(int).to_dict())
out.join(U).to_csv('output/intensity_purpose_may2026.csv')
