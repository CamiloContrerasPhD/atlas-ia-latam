"""Tendencia con un conjunto fijo de países (presentes en las cinco mediciones) para que los cambios de cobertura
entre entregas no muevan los puestos. Métricas por periodo: percentil del AUI dentro del conjunto fijo y cociente
observado/esperado por ingreso (FMI, PIB por persona en edad de trabajar). Además: prueba de estacionalidad de
febrero (vacaciones de verano en el hemisferio sur) comparando el cambio noviembre→febrero por hemisferio."""
import pandas as pd, numpy as np, runpy, io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    ns=runpy.run_path('scripts/07_trend.py')
A=ns['A']; gdp=ns['gdp']; LAT=ns['LAT']
F=A.dropna(); F=F[F.index.isin(gdp.dropna().index)]
print('países en las cinco mediciones:',len(F))
pct=F.rank(pct=True)*100
res={}
for p in F.columns:
    x=np.log(gdp[F.index]); y=np.log(F[p]); b,a=np.polyfit(x,y,1); res[p]=np.exp(y-(a+b*x))
R=pd.DataFrame(res)
L=[c for c in LAT if c in F.index]
print('\nPercentil del AUI en el conjunto fijo (100 = mayor uso):'); print(pct.loc[L].round(0).astype(int).to_string())
print('\nObservado/esperado por ingreso, conjunto fijo:'); print(R.loc[L].round(2).to_string())
print('\nMediana LatAm del cociente obs/esp por periodo:',R.loc[L].median().round(2).to_dict())
print('Mediana LatAm del percentil:',pct.loc[L].median().round(0).to_dict())
# estacionalidad
south=['AUS','NZL','ZAF','ARG','CHL','URY','BRA','PER','PRY','BOL']
lc=np.log(F['2026-02']/F['2025-11'])
lc=lc-lc.median()   # cambio relativo al país mediano
s=lc[lc.index.isin(south)]; n=lc[~lc.index.isin(south)]
print('\nCambio log AUI nov-2025→feb-2026 relativo a la mediana: sur n=%d mediana %.2f RIC %.2f a %.2f | resto n=%d mediana %.2f RIC %.2f a %.2f'%(len(s),s.median(),s.quantile(.25),s.quantile(.75),len(n),n.median(),n.quantile(.25),n.quantile(.75)))
print('por país (sur):',np.exp(s).round(2).to_dict())
print('COL %.2f MEX %.2f USA %.2f GBR %.2f'%tuple(np.exp(lc[c]) for c in ['COL','MEX','USA','GBR']))
pd.concat({'percentil':pct,'obs_esp':R},axis=1).to_csv('output/trend_fixed_set.csv')
