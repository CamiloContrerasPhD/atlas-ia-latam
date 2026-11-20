"""Involucramiento del usuario (análogo de las Fig. 9, 10 y 11 del paper de OpenAI).
El paper mide, por científico, la fracción de pedidos seguidos de aclaración, verificación o revisión del resultado.
El AEI no publica la secuencia de mensajes; publica, por categoría y por país, el patrón de colaboración de cada conversación.
Análogo usado:  Inv_k = task_iteration_k + feedback_loop_k + validation_k   (% de conversaciones de la categoría k)
  revisión ≈ task_iteration + feedback_loop ; verificación ≈ validation ; 'learning' (aprender) se reporta aparte.
Fig. 9: Inv por flujo = media de Inv_k ponderada por uso (pct_k) dentro del flujo; IC 95 % por bootstrap de categorías (2.000).
Fig. 10: dentro de cada flujo, categorías sobre y bajo la mediana de pericia (años de educación que exige la respuesta,
  ai_education_years) y de duración (horas que tomaría sin IA, human_only_time); diferencia de Inv.
  Además MCO: Inv_k = β1·z(pericia_k) + β2·z(log duración_k) + efectos fijos de flujo, errores HC3.
Fig. 11: por país, Inv en cada una de las 20 categorías amplias de solicitud y en el total; ANOVA de Welch entre regiones,
  p ajustados por Holm entre las 21 pruebas."""
import pandas as pd, numpy as np, sys, json
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.oneway import anova_oneway
from statsmodels.stats.multitest import multipletests
sys.path.insert(0,'scripts'); from regiones import REGION, LAT
MES='2026-05-01'; rng=np.random.default_rng(7)
d=pd.read_pickle('/tmp/aei.pkl') if __import__('os').path.exists('/tmp/aei.pkl') else pd.read_csv('data/aei_claude_ai_2026-06-26.csv')
d=d[d.date_start==MES]
import os; FUENTE=os.environ.get('FUENTE','acuerdo')
cl=pd.read_csv('output/clasificacion_flujos.csv')
if FUENTE!='acuerdo': cl['flujo']=cl['flujo_'+FUENTE]; cl['tarea']=cl['tarea_'+FUENTE]
sci=cl[cl.flujo.notna()&(cl.flujo!='Otro trabajo científico')].set_index('categoria')
g=d[(d.geo_level=='global')&(d.category_name=='request')&(d.hierarchy_level==0)].pivot_table(index='node_name',columns='metric_id',values='value')
g['inv']=g.collaboration_task_iteration_pct+g.collaboration_feedback_loop_pct+g.collaboration_validation_pct
g['revision']=g.collaboration_task_iteration_pct+g.collaboration_feedback_loop_pct
s=g.loc[g.index.intersection(sci.index)].copy(); s['flujo']=sci.flujo.reindex(s.index); s=s.dropna(subset=['inv','pct','ai_education_years_mean','human_only_time_mean'])
def wmean(x,w):
    w=np.asarray(w,float); return np.nan if w.sum()==0 else np.sum(np.asarray(x,float)*w)/w.sum()
rows=[]
for f,x in s.groupby('flujo'):
    m=wmean(x.inv,x.pct); bs=[]
    for _ in range(2000):
        i=rng.integers(0,len(x),len(x)); bs.append(wmean(x.inv.values[i],x.pct.values[i]))
    comp={k:wmean(x[c],x.pct) for k,c in [('revision','revision'),('verificacion','collaboration_validation_pct'),('aprender','collaboration_learning_pct'),('delegacion','collaboration_directive_pct')]}
    lo,hi=(np.nanpercentile(bs,2.5),np.nanpercentile(bs,97.5)) if len(x)>=5 else (np.nan,np.nan)   # con menos de 5 categorías no se reporta intervalo
    rows.append(dict(flujo=f,n_categorias=len(x),inv=m,ic_inf=lo,ic_sup=hi,de_categorias=x.inv.std(ddof=1),**comp))
F9=pd.DataFrame(rows).sort_values('inv',ascending=False)
tot=wmean(s.inv,s.pct)
print('Involucramiento medio en categorías científicas (ponderado por uso):',round(tot,1),'| todas las categorías:',round(wmean(g.inv,g.pct),1))
print(F9.round(1).to_string(index=False))
# Fig 10
s['logt']=np.log(s.human_only_time_mean)
def split(var):
    out=[]
    for f,x in s.groupby('flujo'):
        if len(x)<6: continue
        md=x[var].median(); hi=x[x[var]>md]; lo=x[x[var]<=md]
        out.append(dict(flujo=f,n=len(x),inv_alta=wmean(hi.inv,hi.pct),inv_baja=wmean(lo.inv,lo.pct)))
    o=pd.DataFrame(out); o['dif']=o.inv_alta-o.inv_baja; return o
P=split('ai_education_years_mean'); D=split('human_only_time_mean')
print('\nPericia: flujos con más involucramiento en la mitad de mayor pericia',int((P.dif>0).sum()),'de',len(P),'| diferencia media',round(P.dif.mean(),1),'pp (DE',round(P.dif.std(ddof=1),1),')')
print(P.round(1).to_string(index=False))
print('Duración: flujos con más involucramiento en la mitad más larga',int((D.dif>0).sum()),'de',len(D),'| diferencia media',round(D.dif.mean(),1),'pp (DE',round(D.dif.std(ddof=1),1),')')
print(D.round(1).to_string(index=False))
s['zp']=(s.ai_education_years_mean-s.ai_education_years_mean.mean())/s.ai_education_years_mean.std()
s['zt']=(s.logt-s.logt.mean())/s.logt.std()
mod=smf.wls('inv ~ zp + zt + C(flujo)',data=s,weights=s.pct).fit(cov_type='HC3')
mod_u=smf.ols('inv ~ zp + zt + C(flujo)',data=s).fit(cov_type='HC3')
ga=g.copy(); ga['zp']=(ga.ai_education_years_mean-ga.ai_education_years_mean.mean())/ga.ai_education_years_mean.std(); ga['logt']=np.log(ga.human_only_time_mean); ga['zt']=(ga.logt-ga.logt.mean())/ga.logt.std()
mod_all=smf.ols('inv ~ zp + zt',data=ga.dropna(subset=['inv','zp','zt'])).fit(cov_type='HC3')
for nm,m in [('científicas, ponderado',mod),('científicas, sin ponderar',mod_u),('todas las categorías (1.007)',mod_all)]:
    print(f'MCO {nm}: pericia {m.params.zp:.2f} (EE {m.bse.zp:.2f}, p {m.pvalues.zp:.3f}) | duración {m.params.zt:.2f} (EE {m.bse.zt:.2f}, p {m.pvalues.zt:.3f}) | n {int(m.nobs)}')
# Fig 11
c=d[(d.geo_level=='country')&(((d.category_name=='request')&(d.hierarchy_level==2))|(d.category_name=='overall'))]
c=c[c.metric_id.isin(['collaboration_task_iteration_pct','collaboration_feedback_loop_pct','collaboration_validation_pct'])]
c=c.assign(node_name=c.node_name.where(c.category_name!='overall','Total'))
I=c.groupby(['geo_id','node_name']).value.sum(min_count=3).unstack()
reg=pd.Series({k:REGION[k] for k in I.index})
out=[]
for col in I.columns:
    x=I[col].dropna(); r=reg[x.index]; keep=~r.str.startswith('Caribe'); x=x[keep]; r=r[keep]
    grp=[x[r==k].values for k in sorted(r.unique()) if (r==k).sum()>=3]
    if len(grp)<3: continue
    w=anova_oneway(grp,use_var='unequal',welch_correction=True)
    la=x[x.index.isin(LAT)]; re_=x[~x.index.isin(LAT)]
    tt=stats.ttest_ind(la,re_,equal_var=False)
    out.append(dict(t_AL_resto=tt.statistic,p_AL_resto=tt.pvalue,categoria=col,n=len(x),n_AL=len(la),media=x.mean(),de=x.std(ddof=1),media_AL=la.mean(),de_AL=la.std(ddof=1),media_resto=re_.mean(),de_resto=re_.std(ddof=1),welch_F=w.statistic,p=w.pvalue))
F11=pd.DataFrame(out); F11['p_holm']=multipletests(F11.p,method='holm')[1]; F11['p_AL_resto_holm']=multipletests(F11.p_AL_resto,method='holm')[1]
print('\n',F11.sort_values('p')[['categoria','n','n_AL','media','de','media_AL','de_AL','media_resto','de_resto','p_holm','p_AL_resto_holm']].round(3).to_string(index=False))
if FUENTE!='acuerdo': sys.exit()
F9.to_csv('output/involucramiento_flujos.csv',index=False); P.to_csv('output/involucramiento_pericia.csv',index=False); D.to_csv('output/involucramiento_duracion.csv',index=False)
F11.to_csv('output/involucramiento_paises.csv',index=False); I.assign(region=reg).to_csv('output/involucramiento_por_pais.csv')
s[['flujo','pct','inv','ai_education_years_mean','human_only_time_mean']].to_csv('output/involucramiento_categorias.csv')
json.dump({k:dict(coef_pericia=m.params.zp,ee_pericia=m.bse.zp,p_pericia=m.pvalues.zp,coef_duracion=m.params.zt,ee_duracion=m.bse.zt,p_duracion=m.pvalues.zt,n=int(m.nobs)) for k,m in [('ponderado',mod),('sin_ponderar',mod_u),('todas',mod_all)]},open('output/involucramiento_mco.json','w'))
