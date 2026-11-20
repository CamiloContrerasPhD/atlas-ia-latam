"""Trayectoria del índice de uso per cápita (AUI) y del uso relativo al ingreso, cuatro entregas del Economic Index.
AUI = participación del país en el uso / participación en la población de 15-64 años (países incluidos en la entrega).
2025-08: AUI publicado (se valida el cálculo propio contra él). 2025-11 y 2026-02: se calcula con la población en
edad de trabajar de la entrega 2025-08. 2026-04 y 2026-05: AUI publicado.
Ingreso: PIB por persona en edad de trabajar (FMI 2024), el que publica Anthropic en la entrega 2025-08.
Residuo: log(AUI) sobre log(PIB) por MCO en cada periodo; 'observado/esperado' = exp(residuo)."""
import pandas as pd, numpy as np, pycountry
def iso3(a2):
    try: return pycountry.countries.get(alpha_2=a2).alpha_3
    except Exception: return None
e=pd.read_csv('data/aei_enriched_claude_ai_2025-08-04_to_2025-08-11.csv',low_memory=False)
ec=e[(e.geography=='country')&(e.facet=='country')].pivot_table(index='geo_id',columns='variable',values='value')
pop=ec.working_age_pop; gdp=ec.gdp_per_working_age_capita
series={}
# 2025-08: publicado + validación
pub=ec.usage_per_capita_index.dropna(); pub=pub[pub>0]
inc=pub.index
mine=(ec.usage_pct[inc]/ec.usage_pct.sum())/(pop[inc]/pop.dropna().sum())  # denominadores: todos los países
print('validación 2025-08: países',len(inc),' corr(propio,publicado)=%.4f  máx|dif| relativa=%.3f'%(np.corrcoef(mine,pub[inc])[0,1],(mine/pub[inc]-1).abs().max()))
series['2025-08']=pub
for f,lab in [('aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv','2025-11'),('aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv','2026-02')]:
    r=pd.read_csv('data/'+f,low_memory=False)
    u=r[(r.geography=='country')&(r.facet=='country')&(r.variable=='usage_count')].set_index('geo_id').value
    tot=u.sum(); u.index=[iso3(x) for x in u.index]; u=u[pd.notna(u.index)]
    u=u[u.index.isin(pop.dropna().index)&(u>0)]
    series[lab]=(u/tot)/(pop[u.index]/pop.dropna().sum())  # misma regla que reproduce el AUI publicado de 2025-08
n=pd.read_csv('data/aei_claude_ai_2026-06-26.csv',dtype={'node_external_id':str})
n=n[(n.geo_level=='country')&(n.category_name=='overall')&(n.metric_id=='usage_per_capita_index')]
for ds,g in n.groupby('date_start'): s=g.set_index('geo_id').value; series[ds[:7]]=s[s>0]
A=pd.DataFrame(series); A=A[['2025-08','2025-11','2026-02','2026-04','2026-05']]
LAT=['URY','CHL','CRI','ARG','COL','PER','BRA','PAN','MEX','ECU','DOM','BOL','SLV','PRY','GTM','HND']
rows=[]
for p in A.columns:
    s=A[p].dropna(); s=s[s.index.isin(gdp.dropna().index)]
    x=np.log(gdp[s.index]); y=np.log(s); b,a=np.polyfit(x,y,1); e_=y-(a+b*x)
    r2=1-(e_**2).sum()/((y-y.mean())**2).sum(); sd=np.exp(e_.std(ddof=2))
    rkA=s.rank(ascending=False); rkE=e_.rank(ascending=False)
    print(f'{p}: n={len(s)} AUI mediana {s.median():.2f} RIC {s.quantile(.25):.2f}-{s.quantile(.75):.2f} | pendiente {b:.2f} R2 {r2:.2f} factor DE {sd:.2f}')
    for c in LAT:
        if c in s.index: rows.append(dict(periodo=p,pais=c,aui=s[c],rank_aui=int(rkA[c]),n=len(s),obs_esp=np.exp(e_[c]),rank_res=int(rkE[c])))
T=pd.DataFrame(rows); T.to_csv('output/trend_latam.csv',index=False)
print(T.pivot(index='pais',columns='periodo',values='aui').reindex(LAT).round(2).to_string())
print(T.pivot(index='pais',columns='periodo',values='rank_aui').reindex(LAT).to_string())
print(T.pivot(index='pais',columns='periodo',values='obs_esp').reindex(LAT).round(2).to_string())
# brecha frente a la mediana mundial y frente a EE. UU.
print((A.loc[LAT].median()/A.median()).round(2).rename('mediana LAT / mediana mundo').to_string())
