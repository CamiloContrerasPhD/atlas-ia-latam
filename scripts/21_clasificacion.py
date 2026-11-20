"""Une las clasificaciones de DeepSeek V4.1 Flash (Abacus) y Gemini 4 Neon, pensamiento alto (app web) de las 1.008
categorías detalladas de solicitud del AEI en las 40 tareas del paper de OpenAI (Tabla A2).
Regla: se acepta la tarea si coinciden; si ambos la dan por científica pero difieren en la tarea dentro del mismo flujo,
se acepta el flujo (tarea = 'mixta'); cualquier otro desacuerdo queda como 'ambigua' y sale del análisis principal."""
import pandas as pd, re, glob
F={'R':'Lectura y adquisición de conocimiento','I':'Ideación e hipótesis','A':'Administración','D':'Recolección de datos',
   'S':'Software y código de investigación','N':'Análisis científico','W':'Escritura y comunicación','P':'Revisión por pares y servicio',
   'E':'Investigación autónoma de punta a punta','M':'Mentoría y docencia','O':'Otro trabajo científico'}
T={'R1':'Explicar conceptos científicos','R2':'Recuperar información académica','R3':'Revisar y sintetizar literatura',
 'I1':'Formular problemas, modelos o enfoques','I2':'Generar direcciones de investigación','I3':'Generar hipótesis','I4':'Identificar vacíos en la literatura','I5':'Formular preguntas a partir de observaciones',
 'A1':'Gestionar presupuesto y personal','A2':'Coordinar logística de investigación','A3':'Mantener infraestructura de investigación','A4':'Obtener aprobaciones éticas',
 'D1':'Curar bases de datos','D2':'Acceder y adquirir datos','D3':'Diseñar la recolección de datos',
 'S1':'Implementar software de investigación','S2':'Mantener entornos y pipelines','S3':'Revisar y verificar código','S4':'Depurar código de investigación','S5':'Refactorizar u optimizar software',
 'N1':'Desarrollar o probar demostraciones','N2':'Derivar resultados formales','N3':'Analizar propiedades de modelos formales','N4':'Correr análisis estadísticos','N5':'Visualizar datos y resultados','N6':'Desarrollar modelos empíricos','N7':'Establecer cotas y complejidad','N8':'Limpiar y preprocesar datos',
 'W1':'Redactar manuscritos','W2':'Redactar propuestas de financiación','W3':'Crear visuales de investigación','W4':'Responder a evaluadores','W5':'Presentar resultados',
 'P1':'Evaluar manuscritos','P2':'Participar en paneles de evaluación','E1':'Pedir investigación de punta a punta',
 'M1':'Apoyar docencia y mentoría','M2':'Desarrollar currículos','M3':'Revisar investigación de estudiantes','M4':'Supervisar investigadores','OTHER_SCIENTIFIC':'Otro trabajo científico'}
def parse(files):
    out={}
    for f in files:
        for line in open(f,encoding='utf-8',errors='ignore'):
            m=re.search(r'(?:^|[^\d])(\d+)\s*;\s*([A-Z][A-Z0-9_]*)\s*$',line.strip().strip('`'))
            if m: out[int(m.group(1))]=m.group(2)
    return out
cat=pd.read_csv('data/delegated/flujos/categorias_nivel0.csv')
ds=parse(sorted(glob.glob('data/delegated/flujos/deepseek_*.txt'))); gm=parse(sorted(glob.glob('data/delegated/flujos/gemini_salida_*.txt')))
cat['deepseek']=cat.id.map(ds); cat['gemini']=cat.id.map(gm)
wf=lambda c: None if pd.isna(c) or c=='NONE' else ('O' if c=='OTHER_SCIENTIFIC' else c[0])
cat['wf_ds']=cat.deepseek.map(wf); cat['wf_gm']=cat.gemini.map(wf)
def decide(r):
    if pd.isna(r.deepseek) or pd.isna(r.gemini): return pd.Series(dict(estado='sin_respuesta',flujo=None,tarea=None))
    if r.deepseek=='NONE' and r.gemini=='NONE': return pd.Series(dict(estado='no_cientifica',flujo=None,tarea=None))
    if r.deepseek==r.gemini: return pd.Series(dict(estado='acuerdo_tarea',flujo=F[r.wf_ds],tarea=T[r.deepseek]))
    if r.wf_ds and r.wf_ds==r.wf_gm: return pd.Series(dict(estado='acuerdo_flujo',flujo=F[r.wf_ds],tarea='mixta'))
    return pd.Series(dict(estado='ambigua',flujo=None,tarea=None))
cat=pd.concat([cat,cat.apply(decide,axis=1)],axis=1)
for k,col in [('ds','deepseek'),('gm','gemini')]:
    cat['flujo_'+k]=cat['wf_'+k].map(lambda w: F.get(w) if isinstance(w,str) else None)
    cat['tarea_'+k]=cat[col].map(lambda c: T.get(c) if isinstance(c,str) and c!='NONE' else None)
cat.to_csv('output/clasificacion_flujos.csv',index=False)
print(cat.estado.value_counts().to_string())
print(cat[cat.flujo.notna()].groupby('flujo').size().to_string())
# acuerdo científico/no científico (kappa de Cohen)
from sklearn.metrics import cohen_kappa_score
v=cat.dropna(subset=['deepseek','gemini'])
print('kappa científica sí/no', round(cohen_kappa_score(v.deepseek!='NONE', v.gemini!='NONE'),3),
      '| kappa flujo', round(cohen_kappa_score(v.wf_ds.fillna('-'), v.wf_gm.fillna('-')),3),
      '| kappa tarea', round(cohen_kappa_score(v.deepseek, v.gemini),3))
