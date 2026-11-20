"""Experimento natural del calendario académico.
Panel de 113 países × 5 mediciones (ago-2025, nov-2025, feb-2026, abr-2026, may-2026) del índice de uso (AUI).
Tratamiento: vacaciones universitarias o escolares en la ventana de medición (1 = vacaciones, 0,5 = mixto, 0 = clases),
según las tablas de Gemini y DeepSeek; versión principal = celdas en que ambos coinciden (desacuerdo = faltante).
Modelo: log(AUI) = efecto fijo país + efecto fijo periodo + b·vacaciones (+ interacción con el peso de cursos), errores
agrupados por país. b mide el cambio porcentual del uso cuando un país está en vacaciones frente a sus propios periodos de clases."""
import pandas as pd, numpy as np, runpy, io, contextlib, statsmodels.formula.api as smf, warnings
warnings.filterwarnings('ignore')
with contextlib.redirect_stdout(io.StringIO()):
    ns=runpy.run_path('scripts/07_trend.py')
A=ns['A']; F=A.dropna(); F=F[F.index.isin(ns['gdp'].dropna().index)]
P=list(F.columns); V={p:f'V{i+1}' for i,p in enumerate(P)}
val={'clases':0.0,'mixto':0.5,'vacaciones':1.0}
G=pd.read_csv('data/delegated/calendario_gemini.csv').set_index('iso3'); D=pd.read_csv('data/delegated/calendario_deepseek.csv').set_index('iso3')
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv',dtype={'node_external_id':str})
cw=d[(d.geo_level=='country')&(d.category_name=='overall')&(d.metric_id=='use_case_coursework_pct')].groupby('geo_id').value.mean()
rows=[]
for iso in F.index:
    for p in P:
        r=dict(iso=iso,periodo=p,laui=np.log(F.loc[iso,p]),cursos=cw.get(iso,np.nan))
        for lvl in ['uni','col']:
            g=G.loc[iso,f'{lvl}_{V[p]}'] if iso in G.index else None; k=D.loc[iso,f'{lvl}_{V[p]}'] if iso in D.index else None
            r[f'{lvl}_g']=val.get(g); r[f'{lvl}_d']=val.get(k); r[f'{lvl}_c']=val.get(g) if g==k else np.nan
        rows.append(r)
X=pd.DataFrame(rows); X['cursos_z']=(X.cursos-X.cursos.mean())/X.cursos.std()
X.to_csv('output/calendar_panel.csv',index=False)
def fit(f,data):
    data=data.dropna(subset=[c for c in data.columns if c in f])
    m=smf.ols(f,data).fit(cov_type='cluster',cov_kwds={'groups':data.iso})
    return m,len(data),data.iso.nunique()
res=[]
for lvl,name in [('uni','Universidades'),('col','Colegios')]:
    for src,lab in [('c','consenso'),('g','Gemini'),('d','DeepSeek')]:
        v=f'{lvl}_{src}'
        m,n,nc=fit(f'laui ~ {v} + C(iso) + C(periodo)',X)
        b=m.params[v]; lo,hi=m.conf_int().loc[v]
        m2,_,_=fit(f'laui ~ {v} + {v}:cursos_z + C(iso) + C(periodo)',X)
        bi=m2.params[f'{v}:cursos_z']; li,hi2=m2.conf_int().loc[f'{v}:cursos_z']
        tv=(X[v]==1).sum()
        res.append(dict(nivel=name,codificacion=lab,n_obs=n,n_paises=nc,celdas_vacaciones=int(tv),efecto_pct=100*(np.exp(b)-1),ic95_bajo=100*(np.exp(lo)-1),ic95_alto=100*(np.exp(hi)-1),p=m.pvalues[v],
                        interaccion_pp_por_DE_cursos=100*(np.exp(bi)-1),int_ic_bajo=100*(np.exp(li)-1),int_ic_alto=100*(np.exp(hi2)-1),p_int=m2.pvalues[f'{v}:cursos_z']))
R=pd.DataFrame(res); R.to_csv('output/calendar_experiment.csv',index=False)
pd.set_option('display.width',250); print(R.round(3).to_string(index=False))
# placebo: tratamiento asignado al azar dentro de periodo (200 permutaciones), consenso universidades
rng=np.random.default_rng(1); v='uni_c'; Y=X.dropna(subset=[v]).copy(); base=fit(f'laui ~ {v} + C(iso) + C(periodo)',Y)[0].params[v]
perm=[]
for k in range(200):
    Y['perm']=Y.groupby('periodo')[v].transform(lambda s: rng.permutation(s.values))
    perm.append(smf.ols('laui ~ perm + C(iso) + C(periodo)',Y).fit().params['perm'])
perm=np.array(perm); print('permutación (universidades, consenso): b observado %.3f | p empírico (|b_perm|>=|b|) = %.3f'%(base,(np.abs(perm)>=abs(base)).mean()))
