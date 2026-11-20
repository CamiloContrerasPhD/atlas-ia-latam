"""Datos del sitio «Uso de Claude por país» (todas las cifras por país, sin agregados regionales salvo donde se dice).
Escribe output/sitio/*.json con {rows, meta}; meta lleva el código de este script y de los scripts de análisis que usa.
Ejecutar después de 13, 15, 17, 18, 20, 21, 22, 23 (ver README)."""
import pandas as pd, numpy as np, json, os, sys, gettext, pycountry
from scipy import stats
from statsmodels.stats.proportion import proportion_confint
sys.path.insert(0,'scripts'); from regiones import LAT
os.makedirs('output/sitio',exist_ok=True)
es=gettext.translation('iso3166-1',pycountry.LOCALES_DIR,languages=['es'])
CORTO={'USA':'Estados Unidos','BOL':'Bolivia','GBR':'Reino Unido','KOR':'Corea del Sur','TZA':'Tanzania','VNM':'Vietnam','MDA':'Moldavia','TWN':'Taiwán','CZE':'Chequia','PSE':'Palestina','MKD':'Macedonia del Norte'}
def nom(i):
    c=pycountry.countries.get(alpha_3=i); return CORTO.get(i, es.gettext(c.name) if c else i)
def code(*fs): return [{'label':f,'value':open('scripts/'+f).read(),'type':'code','lang':'python'} for f in fs]
SRC={'label':'Datos','value':'Anthropic Economic Index (Hugging Face, entrega 2026-06-26 y anteriores), Banco Mundial'}
def dump(name,rows,meta):
    df=pd.DataFrame(rows).replace({np.nan:None})
    json.dump({'rows':json.loads(df.to_json(orient='records',double_precision=4)),'meta':meta+[SRC]},open(f'output/sitio/{name}.json','w'),ensure_ascii=False)
    print(name,len(df))
REG={'LCN':'América Latina y el Caribe','NAC':'Norteamérica','ECS':'Europa y Asia Central','EAS':'Asia Oriental y el Pacífico','SAS':'Asia Meridional','MEA':'Oriente Medio y Norte de África','SSF':'África Subsahariana'}
from regiones import R as RG
reg_of={c:r for r,cs in RG.items() for c in cs}
WBREG={'América Latina':'América Latina y el Caribe','Caribe (fuera de pruebas)':'América Latina y el Caribe','Norteamérica':'Norteamérica','Europa y Asia Central':'Europa y Asia Central','Asia Oriental y Pacífico':'Asia Oriental y el Pacífico','Asia del Sur':'Asia Meridional','Oriente Medio y Norte de África':'Oriente Medio y Norte de África','África Subsahariana':'África Subsahariana'}
ING={'HIC':'Ingreso alto','UMC':'Ingreso mediano alto','LMC':'Ingreso mediano bajo','LIC':'Ingreso bajo'}
inc=pd.read_csv('data/worldbank_income_level.csv').set_index('iso3').ingreso
d=pd.read_pickle('/tmp/aei.pkl') if os.path.exists('/tmp/aei.pkl') else pd.read_csv('data/aei_claude_ai_2026-06-26.csv')
C=sorted(d[d.geo_level=='country'].geo_id.unique())
P=pd.DataFrame([dict(iso=c,pais=nom(c),region=WBREG[reg_of[c]],ingreso=ING[inc[c]],latam=c in LAT) for c in C])
dump('paises',P,code('25_sitio_datos.py','regiones.py')+[{'label':'Grupo de ingreso','value':'Clasificación del Banco Mundial (API api.worldbank.org/v2/country, consultada el 2026-11-20); Taiwán no figura en la API y se toma como ingreso alto según la tabla CLASS del Banco Mundial'}])
# 1. Mundo: índice de uso, ingreso y uso frente a lo esperado, abril y mayo
wb=pd.read_csv('data/worldbank_gdp_pc_ppp_2022_2024.csv').sort_values('year').groupby('iso3').last().gdp_pc_ppp_current_intl
rows=[];fits=[]
for ds in ['2026-04-01','2026-05-01']:
    ov=d[(d.date_start==ds)&(d.geo_level=='country')&(d.category_name=='overall')].pivot_table(index='geo_id',columns='metric_id',values='value')
    a=ov.usage_per_capita_index.dropna(); a=a[a>0]; ok=a.index.intersection(wb.index)
    b1,b0=np.polyfit(np.log(wb[ok]),np.log(a[ok]),1); fits.append(f'{ds[:7]}: log(índice) = {b0:.3f} + {b1:.3f}·log(PIB PPA), n = {len(ok)}')
    pct=a.rank(pct=True)*100
    for c in a.index:
        e=float(np.exp(b0+b1*np.log(wb[c]))) if c in wb.index else None
        rows.append(dict(id=f'{c}|{ds[:7]}',iso=c,mes=ds[:7],aui=float(a[c]),uso_pct=float(ov.usage_pct.get(c,np.nan)),percentil=float(pct[c]),pib_ppa=float(wb[c]) if c in wb.index else None,aui_esperado=e,obs_esp=float(a[c]/e) if e else None,
                         trabajo=float(ov.use_case_work_pct.get(c,np.nan)),cursos=float(ov.use_case_coursework_pct.get(c,np.nan)),personal=float(ov.use_case_personal_pct.get(c,np.nan))))
M=pd.DataFrame(rows)
for m,g in M.groupby('mes'):
    M.loc[g.index,'puesto_cursos']=g.cursos.rank(ascending=False,method='min')
dump('mundo',M,code('25_sitio_datos.py')+[{'label':'Ajuste por ingreso','value':' | '.join(fits)}])
# 2. Concentración: Lorenz por grupo de países (mundo y cada región) y subnacional
def lorenz(u,pop):
    df=pd.DataFrame({'u':u,'p':pop}).dropna(); df=df[df.p>0]; df['r']=df.u/df.p; df=df.sort_values('r',ascending=False)
    x=np.r_[0,(df.p.cumsum()/df.p.sum()).values]; y=np.r_[0,(df.u.cumsum()/df.u.sum()).values]
    return x,y,2*np.trapezoid(y-x,x),float(np.interp(0.1,x,y))
mm=M[M.mes=='2026-05'].set_index('iso'); mm['pop']=mm.uso_pct/mm.aui; mm['region']=P.set_index('iso').region
cur=[];gin=[]
grupos=[('Mundo',mm)]+[(r,mm[mm.region==r]) for r in sorted(mm.region.unique())]
s=pd.read_csv('output/subnational_may2026.csv').dropna(subset=['pob','usage_pct'])
grupos+= [(f'{nom(c3)} (subnacional)',g.set_index('geo_id').rename(columns={'usage_pct':'uso_pct','pob':'pop'})) for c2,c3,g in [(c2,{'BR':'BRA','CO':'COL','MX':'MEX'}[c2],g) for c2,g in s.groupby('pais')]]
for nm,g in grupos:
    if len(g)<3: continue
    x,y,gi,t10=lorenz(g.uso_pct,g['pop']); cur+=[dict(serie=nm,x=a*100,y=b*100) for a,b in zip(x,y)]; gin.append(dict(id=nm,serie=nm,gini=gi,top10=t10*100,n=len(g)))
dump('lorenz',cur,code('25_sitio_datos.py','20_concentracion.py')); dump('gini',gin,code('25_sitio_datos.py','20_concentracion.py'))
# 3. Ciencia: peso de cada flujo por país (todos los países, con cobertura) y tareas
cl=pd.read_csv('output/clasificacion_flujos.csv'); sci=cl[cl.flujo.notna()]
q=d[(d.date_start=='2026-05-01')&(d.category_name=='request')&(d.hierarchy_level==0)&(d.geo_level.isin(['country','global']))]
W=q[q.metric_id=='pct'].pivot_table(index='geo_id',columns='node_name',values='value'); G=W.loc['GLOBAL']; W=W.drop('GLOBAL')
wk=q[(q.metric_id=='use_case_work_pct')&(q.geo_id=='GLOBAL')].set_index('node_name').value/100
cols=[c for c in sci.categoria if c in W.columns]; fl=sci.set_index('categoria').flujo; ta=sci.set_index('categoria').tarea
CORTOF={'Lectura y adquisición de conocimiento':'Lectura','Ideación e hipótesis':'Ideación','Administración':'Administración','Recolección de datos':'Recolección de datos','Software y código de investigación':'Software','Análisis científico':'Análisis científico','Escritura y comunicación':'Escritura','Revisión por pares y servicio':'Revisión por pares','Mentoría y docencia':'Mentoría y docencia','Otro trabajo científico':'Otro trabajo científico'}
rows=[];trows=[];cob=[]
for ver,Wv,Gv in [('todo',W,G),('trabajo',W.mul(wk.reindex(W.columns),axis=1),G*wk.reindex(G.index))]:
    cov=Wv[cols].notna().mul(Gv[cols],axis=1).sum(axis=1)/Gv[cols].sum()
    den=Wv[cols].sum(axis=1)
    S=Wv[cols].T.groupby(fl[cols]).sum().T.div(den,axis=0)*100
    visf=Wv[cols].notna().T.groupby(fl[cols]).any().T
    tk=[c for c in cols if ta[c]!='mixta']; TS=Wv[tk].T.groupby(ta[tk]).sum().T.div(den,axis=0)*100; visT=Wv[tk].notna().T.groupby(ta[tk]).any().T; TS=TS.where(visT)
    for c in Wv.index:
        cob.append(dict(id=f'{c}|{ver}',iso=c,version=ver,cobertura=cov[c]*100,suficiente=bool(cov[c]>=0.7),peso_cientifico=float(den[c]/Wv.loc[c].sum()*100) if Wv.loc[c].sum()>0 else None))
        if cov[c]<0.7: continue
        for f in S.columns:
            if f=='Otro trabajo científico': continue
            rows.append(dict(id=f'{c}|{ver}|{CORTOF[f]}',iso=c,version=ver,flujo=CORTOF[f],peso=float(S.loc[c,f]) if visf.loc[c,f] else None,publicado=bool(visf.loc[c,f])))   # sin categorías publicadas: dato ausente, no cero
        for t in TS.columns: trows.append(dict(id=f'{c}|{ver}|{t}',iso=c,version=ver,tarea=t,peso=None if pd.isna(TS.loc[c,t]) else float(TS.loc[c,t])))
dump('ciencia_cobertura',cob,code('25_sitio_datos.py','21_clasificacion.py','22_flujos.py'))
dump('ciencia_flujos',rows,code('25_sitio_datos.py','21_clasificacion.py','22_flujos.py'))
TR=pd.DataFrame(trows); top=TR[TR.version=='todo'].fillna({'peso':0}).groupby('tarea').peso.mean().sort_values(ascending=False).head(12).index
TR=TR[TR.tarea.isin(top)]
dump('ciencia_tareas',TR,code('25_sitio_datos.py','22_flujos.py'))
# resumen de tareas: peso medio, DE y difusión (Wilson) entre los 121 países
vis=W[[c for c in cols if ta[c]!='mixta']].notna().T.groupby(ta[[c for c in cols if ta[c]!='mixta']]).any().T
summ=[]
for ver in ['todo','trabajo']:
    x=TR[TR.version==ver]
    for t,g in x.groupby('tarea'):
        k=int(vis[t].sum()); lo,hi=proportion_confint(k,len(W),method='wilson')
        gp=g.peso.fillna(0)   # en el peso medio, una tarea no publicada cuenta como peso 0 dentro del uso científico visible
        summ.append(dict(id=f'{ver}|{t}',version=ver,tarea=t,flujo=CORTOF[sci[sci.tarea==t].flujo.iloc[0]],peso_medio=gp.mean(),de=gp.std(ddof=1),n_paises=len(g),difusion=k/len(W)*100,dif_inf=lo*100,dif_sup=hi*100))
dump('ciencia_tareas_resumen',summ,code('25_sitio_datos.py','22_flujos.py'))
# pruebas entre regiones (ANOVA de Welch, Holm), de 22_flujos.py
pr=[]
for ver in ['todo','trabajo']:
    R=pd.read_csv(f'output/flujos_pesos_2026-05_c70_acuerdo_{ver}.csv')
    for _,r in R.iterrows(): pr.append(dict(id=f'{ver}|{CORTOF[r.flujo]}',version=ver,flujo=CORTOF[r.flujo],publicado_en=r.publicado_en*100,p_regiones=r.welch_p_holm if r.publicado_en>=0.9 else None))
dump('ciencia_pruebas',pr,code('22_flujos.py','25_sitio_datos.py'))
# 4. Involucramiento por país en cada categoría amplia y en el total (mayo)
TRC={'Total':'Total','Software Development':'Desarrollo de software','Content Creation & Copywriting':'Creación de contenido y redacción','Hobbies & Lifestyle':'Pasatiempos y estilo de vida','Education & Learning':'Educación y aprendizaje','Business Process & Operations':'Procesos y operaciones de negocio','Document Processing & Extraction':'Procesamiento de documentos','DevOps & Infrastructure Operations':'DevOps e infraestructura','Data Analysis & Business Intelligence':'Análisis de datos e inteligencia de negocio','Other / Unclear':'Otro o poco claro','Research & Intelligence':'Investigación e inteligencia','Knowledge Retrieval & Enterprise Search':'Búsqueda de conocimiento','Existential, Relational, and Emotional Support':'Apoyo emocional y relacional','Sales & Revenue Operations':'Ventas','Conversation & Meeting Intelligence':'Conversaciones y reuniones','Cybersecurity & Threat Detection':'Ciberseguridad','Companionship & General Conversation':'Compañía y conversación general','Personal AI Assistant':'Asistente personal','Customer Support & Service Operations':'Atención al cliente','Compliance & Regulatory':'Cumplimiento y regulación','Trust & Safety / Platform Integrity':'Confianza y seguridad'}
c=d[(d.date_start=='2026-05-01')&(d.geo_level=='country')&(((d.category_name=='request')&(d.hierarchy_level==2))|(d.category_name=='overall'))]
c=c.assign(node_name=c.node_name.where(c.category_name!='overall','Total'))
I=c[c.metric_id.str.startswith('collaboration_')&~c.metric_id.str.contains('bucket')].pivot_table(index=['geo_id','node_name'],columns='metric_id',values='value').dropna(subset=['collaboration_task_iteration_pct'])
rows=[dict(id=f'{g}|{n}',iso=g,categoria=TRC.get(n,n),inv=r.collaboration_task_iteration_pct+r.collaboration_feedback_loop_pct+r.collaboration_validation_pct,
           revision=r.collaboration_task_iteration_pct+r.collaboration_feedback_loop_pct,verificacion=r.collaboration_validation_pct,aprender=r.collaboration_learning_pct,delegacion=r.collaboration_directive_pct) for (g,n),r in I.iterrows()]
dump('involucramiento_pais',rows,code('25_sitio_datos.py','23_involucramiento.py'))
# 5. Trayectoria: percentil del índice en las cinco mediciones (países presentes en las cinco)
T=pd.read_csv('output/trend_fixed_set.csv',header=[0,1],index_col=0)
rows=[dict(id=f'{i}|{p}',iso=i,periodo=p,percentil=float(T.loc[i,('percentil',p)]),obs_esp=float(T.loc[i,('obs_esp',p)])) for i in T.index for p in T['percentil'].columns]
dump('trayectoria',rows,code('08_trend_fixed_set.py','25_sitio_datos.py'))
# 6. Especialización: RCA de todos los países con datos suficientes
r=pd.read_csv('output/rca_todos.csv'); r['id']=r.pais+'|'+r.grupo.astype(str)
dump('rca',r.rename(columns={'pais':'iso'})[['id','iso','grupo','nombre','rca_t0','rca_t1','densidad_t0']],code('15_rca_complexity.py','25_sitio_datos.py')+[{'label':'Nombres de grupo','value':'Títulos oficiales de los grupos menores SOC 2018, en inglés'}])
# 7. Covariables por país
cv=pd.read_csv('output/covariates_panel.csv').rename(columns={'geo_id':'iso'})
cv['aui']=np.exp(cv.laui); cv['pib_ppa']=np.exp(cv.lgdp); cv['id_rd']=np.exp(cv.lrd); cv['investigadores']=np.exp(cv.linv)
dump('covariables_pais',cv[['iso','aui','cursos','trabajo','academico','pib_ppa','id_rd','investigadores','terciaria','internet','epi']],code('14_covariates.py','25_sitio_datos.py'))
