"""Análisis subnacional (Colombia, Brasil, México), mayo 2026.
Población: tablas de Gemini y DeepSeek; se usa el promedio cuando difieren menos de 5 %; México usa el Censo 2020 de INEGI para todos los estados.
Intensidad relativa = participación del departamento/estado en el uso del país / participación en la población del país
(1 = proporcional). Se reporta junto con el peso de cursos y los años de educación requeridos de las tareas."""
import pandas as pd, numpy as np, re, io
def load(fn):
    txt=open(fn,encoding='utf-8',errors='ignore').read()
    rows={}
    for line in txt.splitlines():
        m=re.match(r'^\s*\|?\s*((?:CO|BR|MX)-[A-Z]{2,3})\s*[,|]\s*([^,|]+?)\s*[,|]\s*"?([\d.,\s]+)"?\s*[,|]\s*(\d{4})',line)
        if m: rows[m.group(1)]=dict(nombre=m.group(2).strip(),pob=float(re.sub(r'[^\d]','',m.group(3))),anio=int(m.group(4)))
    return pd.DataFrame.from_dict(rows,orient='index')
g=load('data/delegated/pop_gemini.csv'); k=load('data/delegated/pop_deepseek.csv')
P=g.join(k,lsuffix='_g',rsuffix='_d',how='outer'); P['dif']=(P.pob_g/P.pob_d-1).abs()
P['pob']=np.where(P.dif<0.05,(P.pob_g+P.pob_d)/2,np.nan); P['pais']=P.index.str[:2]
# México: un solo año y fuente para todos los estados (Censo 2020 de INEGI, tabla de Gemini), porque mezclar el censo con proyecciones a 2025 sesga las participaciones
P.loc[P.pais=='MX','pob']=P.loc[P.pais=='MX','pob_g']
print('subregiones con población:',P.pais.value_counts().to_dict(),'| difieren >5 %:',P[P.dif>=0.05].index.tolist())
print('totales Gemini:',(P.groupby('pais').pob_g.sum()/1e6).round(1).to_dict(),'DeepSeek:',(P.groupby('pais').pob_d.sum()/1e6).round(1).to_dict())
print('años:',P.groupby('pais')[['anio_g','anio_d']].agg(lambda s: sorted(set(s.dropna().astype(int)))).to_dict())
P.to_csv('output/poblacion_comparada.csv')
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv',dtype={'node_external_id':str})
s=d[(d.geo_level=='subregion')&(d.category_name=='overall')&(d.date_start=='2026-05-01')&(d.geo_id.str[:2].isin(['CO','BR','MX']))]
S=s.pivot_table(index='geo_id',columns='metric_id',values='value')[['usage_pct','use_case_coursework_pct','use_case_work_pct','human_education_years_mean','collaboration_bucket_automation_pct']]
S=S.join(P[['nombre_g','pob','dif']]); S['pais']=S.index.str[:2]
out=[]
for p,gp in S.groupby('pais'):
    tot=P[P.pais==p].pob.sum()  # población nacional (todas las subregiones con dato)
    gp=gp.assign(pob_share=gp.pob/tot*100); gp['intensidad']=gp.usage_pct/gp.pob_share
    gp['cobertura_uso']=gp.usage_pct.sum()
    out.append(gp)
S=pd.concat(out); S.to_csv('output/subnational_may2026.csv')
for p in ['CO','BR','MX']:
    t=S[S.pais==p].sort_values('intensidad',ascending=False)
    print(f'\n== {p}: subregiones publicadas {len(t)}, cubren {t.usage_pct.sum():.1f} % del uso y {t.pob_share.sum():.1f} % de la población')
    print(t[['nombre_g','usage_pct','pob_share','intensidad','use_case_coursework_pct','human_education_years_mean']].round(2).to_string())
    r=t[['intensidad','use_case_coursework_pct']].corr(method='spearman').iloc[0,1]; print('Spearman intensidad vs cursos: %.2f'%r)
