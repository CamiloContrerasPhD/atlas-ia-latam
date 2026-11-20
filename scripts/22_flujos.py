"""Peso de los flujos de trabajo científicos por país (análogo de la Fig. 3A, Fig. 4 y Tabla 3 del paper de OpenAI).
Unidad = país (en el paper, el científico). Para el país c y el flujo w:
    s_cw = Σ_{k∈w} pct_ck / Σ_{k∈Ciencia} pct_ck        (k = categoría detallada de solicitud publicada para c)
Peso medio del flujo: s̄_w = (1/N) Σ_c s_cw, IC 95 % t: s̄_w ± t_{N-1}·sd_w/√N (cada país pesa igual).
Cobertura del país: fracción de la masa global de categorías científicas que el AEI publica para c; se usan países con
cobertura ≥ UMBRAL (las celdas no publicadas no son cero).
Diferencias regionales: ANOVA de Welch por flujo (varianzas distintas entre regiones), p ajustados por Holm entre los 10 flujos.
Tabla de tareas: peso medio de cada tarea y difusión = % de los 121 países donde la tarea alcanza el mínimo de publicación
del AEI, con IC de Wilson."""
import pandas as pd, numpy as np, json, sys
from scipy import stats
from statsmodels.stats.oneway import anova_oneway
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint
sys.path.insert(0,'scripts'); from regiones import REGION, LAT
UMBRAL=float(sys.argv[1]) if len(sys.argv)>1 else 0.8
MES=sys.argv[2] if len(sys.argv)>2 else '2026-05-01'
import os; FUENTE=os.environ.get('FUENTE','acuerdo')
cl=pd.read_csv('output/clasificacion_flujos.csv')
if FUENTE!='acuerdo': cl['flujo']=cl['flujo_'+FUENTE]; cl['tarea']=cl['tarea_'+FUENTE]
sci=cl[cl.flujo.notna()]
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv',usecols=['date_start','geo_id','geo_level','category_name','hierarchy_level','metric_id','value','node_name'])
q=d[(d.date_start==MES)&(d.category_name=='request')&(d.hierarchy_level==0)&(d.metric_id=='pct')&d.geo_level.isin(['country','global'])]
W=q.pivot_table(index='geo_id',columns='node_name',values='value')
G=W.loc['GLOBAL']; W=W.drop('GLOBAL')
PESO=os.environ.get('PESO','todo')
if PESO=='trabajo':   # solo la fracción de trabajo de cada categoría (use_case_work_pct global), aproxima al usuario profesional
    wk=d[(d.date_start==MES)&(d.category_name=='request')&(d.hierarchy_level==0)&(d.metric_id=='use_case_work_pct')&(d.geo_level=='global')].set_index('node_name').value/100
    W=W.mul(wk.reindex(W.columns),axis=1); G=G*wk.reindex(G.index)
cols=[c for c in sci.categoria if c in W.columns]
fl=sci.set_index('categoria').flujo; ta=sci.set_index('categoria').tarea
cov=W[cols].notna().mul(G[cols],axis=1).sum(axis=1)/G[cols].sum()
sci_share_total=W[cols].sum(axis=1)/W.sum(axis=1)
ok=cov[cov>=UMBRAL].index
den=W.loc[ok,cols].sum(axis=1)
S=W.loc[ok,cols].T.groupby(fl[cols]).sum().T.div(den,axis=0)*100
gl=G[cols].groupby(fl[cols]).sum()/G[cols].sum()*100
FL=[f for f in ['Lectura y adquisición de conocimiento','Ideación e hipótesis','Administración','Recolección de datos','Software y código de investigación','Análisis científico','Escritura y comunicación','Revisión por pares y servicio','Investigación autónoma de punta a punta','Mentoría y docencia'] if f in S.columns]
reg=pd.Series({c:REGION[c] for c in S.index}); test=reg[~reg.str.startswith('Caribe')]
vis_fl=W.loc[ok,cols].notna().T.groupby(fl[cols]).any().T.mean()   # fracción de países incluidos con al menos una categoría del flujo publicada
rows=[]
for f in FL:
    x=S[f]; n=len(x); m=x.mean(); sd=x.std(ddof=1); h=stats.t.ppf(.975,n-1)*sd/np.sqrt(n)
    groups=[S.loc[test.index[test==r],f].values for r in sorted(test.unique())]
    groups=[g for g in groups if len(g)>=3 and np.var(g)>0]
    wel=anova_oneway(groups,use_var='unequal',welch_correction=True) if len(groups)>=3 else type('w',(),{'statistic':np.nan,'pvalue':np.nan})
    la=x[x.index.isin(LAT)]; re_=x[~x.index.isin(LAT)]
    tt=stats.ttest_ind(la,re_,equal_var=False)
    rows.append(dict(flujo=f,publicado_en=vis_fl[f],media=m,de=sd,ic_inf=m-h,ic_sup=m+h,mediana=x.median(),p25=x.quantile(.25),p75=x.quantile(.75),global_agregado=gl.get(f,np.nan),
        media_AL=la.mean(),de_AL=la.std(ddof=1),n_AL=len(la),media_resto=re_.mean(),de_resto=re_.std(ddof=1),n_resto=len(re_),
        welch_F=wel.statistic,welch_p=wel.pvalue,t_AL_resto=tt.statistic,p_AL_resto=tt.pvalue))
R=pd.DataFrame(rows)
R.loc[R.publicado_en<0.9,['welch_p','p_AL_resto']]=np.nan   # flujo publicado en menos del 90 % de los países: la omisión domina, no se prueba
def holm(p):
    p=pd.Series(p); o=pd.Series(np.nan,index=p.index); m=p.notna()
    if m.any(): o[m]=multipletests(p[m],method='holm')[1]
    return o
R['welch_p_holm']=holm(R.welch_p); R['p_AL_resto_holm']=holm(R.p_AL_resto)
reg_means=S[FL].groupby(reg).agg(['mean','count'])
print(f'Mes {MES[:7]} | umbral cobertura {UMBRAL} | países {len(ok)} (AL {sum(ok.isin(LAT))}) | categorías científicas {len(cols)}')
print('Peso científico en el uso total (países incluidos): mediana', round(sci_share_total[ok].median()*100,2),'RIC',round(sci_share_total[ok].quantile(.25)*100,2),'-',round(sci_share_total[ok].quantile(.75)*100,2))
pd.set_option('display.width',250)
print(R[['flujo','publicado_en','media','de','ic_inf','ic_sup','global_agregado','media_AL','media_resto','welch_p_holm','p_AL_resto_holm']].round(3).to_string(index=False))
print(reg_means.xs('count',axis=1,level=1).iloc[:,0].to_string())
# tareas
tk=sci[sci.tarea!='mixta']; tcols=[c for c in tk.categoria if c in W.columns]
TS=W.loc[ok,tcols].T.groupby(ta[tcols]).sum().T.div(den,axis=0)*100
vis=W[tcols].notna().T.groupby(ta[tcols]).any().T
N=len(W); tab=[]
for t in TS.columns:
    k=int(vis[t].sum()); lo,hi=proportion_confint(k,N,method='wilson')
    x=TS[t]; tab.append(dict(tarea=t,flujo=sci[sci.tarea==t].flujo.iloc[0],peso=x.mean(),de=x.std(ddof=1),difusion=k/N*100,dif_inf=lo*100,dif_sup=hi*100,
                              peso_AL=x[x.index.isin(LAT)].mean(),peso_resto=x[~x.index.isin(LAT)].mean(),categorias='; '.join(tk[tk.tarea==t].categoria)))
TB=pd.DataFrame(tab).sort_values('peso',ascending=False)
print(TB.head(10)[['tarea','flujo','peso','de','difusion','dif_inf','dif_sup','peso_AL','peso_resto']].round(2).to_string(index=False))
sfx=f'_{MES[:7]}_c{int(UMBRAL*100)}_{FUENTE}_{PESO}'
R.to_csv(f'output/flujos_pesos{sfx}.csv',index=False); TB.to_csv(f'output/tareas_peso_difusion{sfx}.csv',index=False)
S.assign(region=reg,cobertura=cov[ok]).to_csv(f'output/flujos_por_pais{sfx}.csv')
