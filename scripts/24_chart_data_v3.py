"""Datos de las secciones nuevas del artefacto (técnicas del paper de OpenAI aplicadas al AEI).
Lee las salidas de 20_concentracion.py, 22_flujos.py y 23_involucramiento.py y escribe output/charts/*.json con {rows, meta};
meta incluye el código del script de análisis y de este script."""
import pandas as pd, numpy as np, json, os, sys
from scipy import stats
sys.path.insert(0,'scripts'); from regiones import LAT
os.makedirs('output/charts',exist_ok=True)
def code(*fs): return [{'label':f,'value':open('scripts/'+f).read(),'type':'code','lang':'python'} for f in fs]
def dump(name,rows,meta):
    rows=json.loads(pd.DataFrame(rows).replace({np.nan:None}).to_json(orient='records',double_precision=4))
    json.dump({'rows':rows,'meta':meta},open(f'output/charts/{name}.json','w'),ensure_ascii=False)
    print(name,len(rows))
SRC={'label':'Datos','value':'Anthropic Economic Index, entrega 2026-06-26 (aei_claude_ai_2026-06-26.csv), mayo de 2026'}
ORD=['Lectura y adquisición de conocimiento','Ideación e hipótesis','Administración','Recolección de datos','Software y código de investigación','Análisis científico','Escritura y comunicación','Revisión por pares y servicio','Mentoría y docencia']
CORTO={'Lectura y adquisición de conocimiento':'Lectura','Ideación e hipótesis':'Ideación','Administración':'Administración','Recolección de datos':'Recolección de datos','Software y código de investigación':'Software','Análisis científico':'Análisis científico','Escritura y comunicación':'Escritura','Revisión por pares y servicio':'Revisión por pares','Mentoría y docencia':'Mentoría y docencia'}
# 1. concentración
C=json.load(open('output/concentracion.json')); m=C['2026-05']; sub=C['subnacional_2026-05']
rows=[];g=[]
for name,cur,gi,dec,n in [('Mundo (121 países)',m['curva'],m['gini'],m['deciles'],m['n']),('América Latina (16 países)',m['curva_lat'],m['gini_lat'],m['deciles_lat'],m['n_lat'])]+[(k2,sub[k]['curva'],sub[k]['gini'],sub[k]['deciles'],sub[k]['n']) for k,k2 in [('BR','Brasil (estados)'),('CO','Colombia (departamentos)'),('MX','México (estados)')]]:
    rows+= [dict(serie=name,x=a*100,y=b*100) for a,b in cur]
    g.append(dict(serie=name,gini=gi,top10=dec['10%']*100,top50=dec['50%']*100,n=n))
dump('concentracion',rows,code('20_concentracion.py','24_chart_data_v3.py')+[SRC])
dump('concentracion_gini',g,code('20_concentracion.py','24_chart_data_v3.py')+[SRC])
# 2. flujos por grupo con IC t
rows=[];tests=[]
for spec,lab in [('todo','Todo el uso'),('trabajo','Solo la parte de trabajo')]:
    P=pd.read_csv(f'output/flujos_por_pais_2026-05_c70_acuerdo_{spec}.csv',index_col=0)
    R=pd.read_csv(f'output/flujos_pesos_2026-05_c70_acuerdo_{spec}.csv').set_index('flujo')
    for f in ORD:
        if f not in P.columns: continue
        for grp,mask in [('Todos los países',P.index==P.index),('América Latina',P.index.isin(LAT)),('Resto',~P.index.isin(LAT))]:
            x=P.loc[mask,f].dropna(); n=len(x); mu=x.mean(); sd=x.std(ddof=1); h=stats.t.ppf(.975,n-1)*sd/np.sqrt(n)
            rows.append(dict(spec=lab,flujo=CORTO[f],grupo=grp,media=mu,de=sd,ic_inf=max(0,mu-h),ic_sup=mu+h,n=n,orden=ORD.index(f)))
        r=R.loc[f]
        tests.append(dict(id=f'{spec}|{CORTO[f]}',spec=lab,flujo=CORTO[f],orden=ORD.index(f),publicado_en=r.publicado_en*100,media_AL=r.media_AL,de_AL=r.de_AL,media_resto=r.media_resto,de_resto=r.de_resto,
                          p_AL_resto=r.p_AL_resto_holm if r.publicado_en>=0.9 else None,p_regiones=r.welch_p_holm if r.publicado_en>=0.9 else None,n_AL=int(r.n_AL),n_resto=int(r.n_resto)))
dump('flujos',rows,code('21_clasificacion.py','22_flujos.py','24_chart_data_v3.py')+[SRC,{'label':'Cobertura mínima','value':'0,7'}])
dump('flujos_pruebas',tests,code('22_flujos.py','24_chart_data_v3.py')+[SRC])
# robustez: dirección y p de AL frente al resto en cada especificación
rob=[]
for f in sorted(os.listdir('output')):
    if f.startswith('flujos_pesos_') and f[:-4].count('_')==5:
        _,_,mes,c,fu,pe=f[:-4].split('_')
        R=pd.read_csv('output/'+f)
        for _,r in R[R.publicado_en>=0.9].iterrows():
            rob.append(dict(id=f'{mes}|{c}|{fu}|{pe}|{CORTO[r.flujo]}',mes=mes,cobertura=int(c[1:])/100,clasificacion={'acuerdo':'Acuerdo de ambos','ds':'Solo DeepSeek','gm':'Solo Gemini'}[fu],peso={'todo':'Todo el uso','trabajo':'Solo trabajo'}[pe],
                            flujo=CORTO[r.flujo],dif=r.media_AL-r.media_resto,p=r.p_AL_resto_holm,n_AL=int(r.n_AL)))
dump('flujos_robustez',rob,code('22_flujos.py','24_chart_data_v3.py')+[SRC])
# 3. tareas
T=pd.read_csv('output/tareas_peso_difusion_2026-05_c70_acuerdo_todo.csv').head(10)
T['flujo']=T.flujo.map(lambda f: CORTO.get(f,f)); T['id']=T.tarea
dump('tareas',T[['id','tarea','flujo','peso','de','difusion','dif_inf','dif_sup','peso_AL','peso_resto','categorias']],code('22_flujos.py','24_chart_data_v3.py')+[SRC])
# 4. involucramiento
F9=pd.read_csv('output/involucramiento_flujos.csv').dropna(subset=['inv']); F9['flujo']=F9.flujo.map(CORTO)
dump('involucramiento',F9,code('23_involucramiento.py','24_chart_data_v3.py')+[SRC])
M=json.load(open('output/involucramiento_mco.json')); rows=[]
for k,lab in [('ponderado','Categorías científicas, ponderadas por uso'),('sin_ponderar','Categorías científicas, sin ponderar'),('todas','Todas las categorías')]:
    for v,vl in [('pericia','Pericia (+1 DE)'),('duracion','Duración (+1 DE de log horas)')]:
        c=M[k]['coef_'+v]; e=M[k]['ee_'+v]; rows.append(dict(id=f'{k}|{v}',modelo=lab,variable=vl,coef=c,ic_inf=c-1.96*e,ic_sup=c+1.96*e,p=M[k]['p_'+v],n=M[k]['n']))
dump('involucramiento_mco',rows,code('23_involucramiento.py','24_chart_data_v3.py')+[SRC])
F11=pd.read_csv('output/involucramiento_paises.csv')
TR={'Total':'Total','Software Development':'Desarrollo de software','Content Creation & Copywriting':'Creación de contenido y redacción','Hobbies & Lifestyle':'Pasatiempos y estilo de vida','Education & Learning':'Educación y aprendizaje','Business Process & Operations':'Procesos y operaciones de negocio','Document Processing & Extraction':'Procesamiento de documentos','DevOps & Infrastructure Operations':'DevOps e infraestructura','Data Analysis & Business Intelligence':'Análisis de datos e inteligencia de negocio','Other / Unclear':'Otro o poco claro','Research & Intelligence':'Investigación e inteligencia','Knowledge Retrieval & Enterprise Search':'Búsqueda de conocimiento','Existential, Relational, and Emotional Support':'Apoyo emocional y relacional','Sales & Revenue Operations':'Ventas','Conversation & Meeting Intelligence':'Conversaciones y reuniones','Cybersecurity & Threat Detection':'Ciberseguridad','Companionship & General Conversation':'Compañía y conversación general','Personal AI Assistant':'Asistente personal','Customer Support & Service Operations':'Atención al cliente','Compliance & Regulatory':'Cumplimiento y regulación','Trust & Safety / Platform Integrity':'Confianza y seguridad'}
F11['id']=F11.categoria; F11['nombre']=F11.categoria.map(TR); F11['dif']=F11.media_AL-F11.media_resto
F11=F11[F11.n_AL>=5].sort_values('dif',ascending=False)
dump('involucramiento_paises',F11[['id','nombre','n','n_AL','media','de','media_AL','de_AL','media_resto','de_resto','dif','p_holm','p_AL_resto_holm']],code('23_involucramiento.py','24_chart_data_v3.py')+[SRC])
