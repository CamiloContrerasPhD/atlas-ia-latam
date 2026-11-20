"""Qué explica las diferencias entre países (mayo 2026).
Resultados: log índice de uso (AUI), peso de cursos (%), peso académico (tesis + literatura + metodología, % del uso).
Explicativas: log PIB per cápita PPA, log gasto en I+D (% PIB), log investigadores por millón, matrícula terciaria,
uso de internet (Banco Mundial, último dato 2015-2025) y dominio del inglés (EF EPI; promedio de Gemini y DeepSeek cuando
difieren ≤ 15 puntos). Métodos: Spearman con IC bootstrap, MCO estandarizado con errores HC3, regresión cuantílica
y gradient boosting con validación cruzada e importancia por permutación."""
import pandas as pd, numpy as np, re, warnings, statsmodels.formula.api as smf
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.inspection import permutation_importance
warnings.filterwarnings('ignore'); rng=np.random.default_rng(7)
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv',dtype={'node_external_id':str})
may=d[d.date_start=='2026-05-01']
ov=may[(may.geo_level=='country')&(may.category_name=='overall')].pivot_table(index='geo_id',columns='metric_id',values='value')
Y=pd.DataFrame({'laui':np.log(ov.usage_per_capita_index.where(ov.usage_per_capita_index>0)),'cursos':ov.use_case_coursework_pct,'trabajo':ov.use_case_work_pct})
q=may[(may.geo_level=='country')&(may.category_name=='request')&(may.metric_id=='pct')&(may.hierarchy_level==0)&(may.node_name.isin(['Thesis writing','Literature review','Research methodology']))]
A=q.pivot_table(index='geo_id',columns='node_name',values='value').dropna(); Y['academico']=A.sum(axis=1)
wb=pd.read_csv('data/worldbank_covariates.csv').pivot_table(index='iso3',columns='indicator',values='value')
gdp=pd.read_csv('data/worldbank_gdp_pc_ppp_2022_2024.csv').sort_values('year').groupby('iso3').last().gdp_pc_ppp_current_intl
def epi(fn):
    t=open(fn,encoding='utf-8',errors='ignore').read(); o={}
    for m in re.finditer(r'^\s*([A-Z]{3}),[^,\n]*,(\d{3}),',t,re.M): o[m.group(1)]=float(m.group(2))
    return pd.Series(o)
eg,ed=epi('data/delegated/epi_gemini.csv'),epi('data/delegated/epi_deepseek.csv')
E=pd.DataFrame({'g':eg,'d':ed}); E['epi']=np.where((E.g-E.d).abs()<=15,(E.g+E.d)/2,np.nan)
print('EPI: Gemini %d, DeepSeek %d, ambos %d, coinciden ≤15 %d, mediana |dif| %.1f'%(eg.size,ed.size,E.dropna(subset=['g','d']).shape[0],E.epi.notna().sum(),(E.g-E.d).abs().median()))
X=pd.DataFrame({'lgdp':np.log(gdp),'lrd':np.log(wb.rd_pct_gdp),'linv':np.log(wb.researchers_per_million),'terciaria':wb.tertiary_enrollment,'internet':wb.internet_pct,'epi':E.epi})
D=Y.join(X,how='left'); D=D[D.laui.notna()]; D.to_csv('output/covariates_panel.csv')
print('países:',len(D),'| datos por variable:',D.notna().sum().to_dict())
xs=['lgdp','lrd','linv','terciaria','internet','epi']
# 1. Spearman con IC bootstrap
print('\nSpearman (IC95 bootstrap):')
for yv in ['laui','cursos','academico']:
    line=[]
    for xv in xs:
        s=D[[yv,xv]].dropna(); r=s.corr('spearman').iloc[0,1]
        bs=[s.iloc[rng.integers(0,len(s),len(s))].corr('spearman').iloc[0,1] for _ in range(500)]
        line.append(f'{xv} {r:+.2f} [{np.percentile(bs,2.5):+.2f},{np.percentile(bs,97.5):+.2f}] n={len(s)}')
    print(f' {yv}: '+' | '.join(line))
# 2. MCO estandarizado, HC3
Z=D.copy()
for c in xs: Z[c]=(Z[c]-Z[c].mean())/Z[c].std()
print('\nMCO estandarizado (coeficiente por 1 DE, HC3):')
for yv,f in [('laui','lgdp + terciaria + internet + epi + linv'),('cursos','lgdp + terciaria + internet + epi + linv'),('academico','lgdp + terciaria + epi + linv')]:
    m=smf.ols(f'{yv} ~ {f}',Z).fit(cov_type='HC3'); ci=m.conf_int()
    print(f' {yv} (n={int(m.nobs)}, R2={m.rsquared:.2f}): '+' | '.join(f'{k} {m.params[k]:+.2f} [{ci.loc[k,0]:+.2f},{ci.loc[k,1]:+.2f}]' for k in m.params.index if k!='Intercept'))
# 3. Regresión cuantílica del log AUI sobre log PIB
print('\nCuantílica log AUI ~ log PIB (elasticidad):')
for qq in [0.25,0.5,0.75]:
    m=smf.quantreg('laui ~ lgdp',D).fit(q=qq); ci=m.conf_int().loc['lgdp']; print(f' q={qq}: {m.params.lgdp:.2f} [{ci[0]:.2f},{ci[1]:.2f}]')
# 4. Gradient boosting con validación cruzada (5 pliegues × 10 repeticiones), importancia por permutación
print('\nGradient boosting (R2 fuera de muestra, media ± DE):')
for yv in ['laui','cursos']:
    s=D[[yv]+xs].dropna(); Xm,ym=s[xs].values,s[yv].values
    gb=GradientBoostingRegressor(n_estimators=200,max_depth=2,learning_rate=0.05,subsample=0.8,random_state=0)
    sc=np.concatenate([cross_val_score(gb,Xm,ym,cv=KFold(5,shuffle=True,random_state=k),scoring='r2') for k in range(10)])
    base=np.concatenate([cross_val_score(GradientBoostingRegressor(n_estimators=200,max_depth=2,learning_rate=0.05,subsample=0.8,random_state=0),s[['lgdp']].values,ym,cv=KFold(5,shuffle=True,random_state=k),scoring='r2') for k in range(10)])
    gb.fit(Xm,ym); pi=permutation_importance(gb,Xm,ym,n_repeats=30,random_state=0)
    print(f' {yv} (n={len(s)}): todas {sc.mean():.2f} ± {sc.std():.2f} | solo PIB {base.mean():.2f} ± {base.std():.2f} | importancia: '+', '.join(f'{xs[i]} {pi.importances_mean[i]:.3f}' for i in np.argsort(-pi.importances_mean)))
