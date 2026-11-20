"""Exporta los datos de los gráficos del artefacto "Uso de Claude en América Latina" a output/charts/*.json
({rows, meta}). Todo deriva de los archivos del Anthropic Economic Index en data/ y de los mapas en scripts/.
Ejecutar desde la carpeta raíz del proyecto: python3 scripts/10_chart_data.py"""
import pandas as pd, numpy as np, json, runpy, io, contextlib, gettext, pycountry
es=gettext.translation('iso3166-1',pycountry.LOCALES_DIR,languages=['es'])
def nombre(iso):
    c=pycountry.countries.get(alpha_3=iso)
    return es.gettext(c.name) if c else iso
CORTO={'USA':'Estados Unidos','BOL':'Bolivia','VEN':'Venezuela','GBR':'Reino Unido','KOR':'Corea del Sur','RUS':'Rusia','IRN':'Irán','TZA':'Tanzania','VNM':'Vietnam','MDA':'Moldavia','SYR':'Siria','LAO':'Laos','PSE':'Palestina','TWN':'Taiwán','CZE':'Chequia'}
def nom(iso): return CORTO.get(iso, nombre(iso))
CODE=open('scripts/10_chart_data.py').read()
def save(name,rows,inputs,extra=None):
    meta=[{'label':'10_chart_data.py','value':CODE,'type':'code','lang':'python'},{'label':'Entrada','value':', '.join(inputs)}]+(extra or [])
    json.dump({'rows':rows,'meta':meta},open(f'output/charts/{name}.json','w'),ensure_ascii=False,allow_nan=False)
LAT=['URY','CHL','CRI','ARG','COL','PER','BRA','PAN','MEX','ECU','DOM','BOL','SLV','PRY','GTM','HND']
SIX=['PER','COL','CHL','MEX','ARG','BRA']
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv',dtype={'node_external_id':str})
may=d[d.date_start=='2026-05-01']
ov=may[(may.geo_level.isin(['country','global']))&(may.category_name=='overall')].pivot_table(index='geo_id',columns='metric_id',values='value')
# 1. ingreso vs uso (mayo 2026, PIB per cápita PPA Banco Mundial)
wb=pd.read_csv('data/worldbank_gdp_pc_ppp_2022_2024.csv').sort_values('year').groupby('iso3').last().gdp_pc_ppp_current_intl
aui=ov.usage_per_capita_index.drop('GLOBAL').dropna(); aui=aui[(aui>0)&aui.index.isin(wb.index)]
x=np.log(wb[aui.index]); y=np.log(aui); b,a=np.polyfit(x,y,1); fit=np.exp(a+b*x)
rows=[dict(iso=k,pais=nom(k),region='América Latina' if k in LAT else 'Resto del mundo',pib_ppa=round(float(wb[k])),aui=float(aui[k]),aui_esperado=round(float(fit[k]),3),obs_esp=round(float(aui[k]/fit[k]),2)) for k in aui.index]
save('ingreso_uso',rows,['aei_claude_ai_2026-06-26.csv','worldbank_gdp_pc_ppp_2022_2024.csv'],[{'label':'Ajuste','value':f'log(AUI) = {a:.3f} + {b:.3f}·log(PIB PPA); n={len(aui)}'}])
# 2. propósito
U=ov[['use_case_work_pct','use_case_coursework_pct','use_case_personal_pct']].rename(columns={'use_case_work_pct':'trabajo','use_case_coursework_pct':'cursos','use_case_personal_pct':'personal'})
W=U.drop('GLOBAL').dropna(); rk=W.cursos.rank(ascending=False).astype(int)
rows=[dict(geo=k,pais=nom(k),trabajo=float(U.loc[k,'trabajo']),cursos=float(U.loc[k,'cursos']),personal=float(U.loc[k,'personal']),puesto_cursos=int(rk[k]),n=len(W)) for k in SIX+['USA']]
rows.append(dict(geo='MUNDO',pais='Mediana mundial',trabajo=round(W.trabajo.median(),1),cursos=round(W.cursos.median(),1),personal=round(W.personal.median(),1),cursos_p25=round(W.cursos.quantile(.25),1),cursos_p75=round(W.cursos.quantile(.75),1),n=len(W)))
save('proposito',rows,['aei_claude_ai_2026-06-26.csv'])
# 3. uso académico: categorías detalladas publicadas para los seis grandes, EE. UU. y el agregado global en abril y mayo
mp=pd.read_csv('scripts/scholarly_request_map.csv'); mp=mp[mp.workflow_openai!='Conceptos disciplinarios']
q=d[(d.category_name=='request')&(d.metric_id=='pct')&(d.hierarchy_level==0)&(d.geo_level.isin(['global','country']))&(d.node_name.isin(mp.node_name))]
REF=SIX+['USA','GLOBAL']
Wm={m:g.pivot_table(index='geo_id',columns='node_name',values='value') for m,g in q.groupby('date_start')}
common=[n for n in mp.node_name if all(n in Wm[m].columns and Wm[m].loc[REF,n].notna().all() for m in Wm)]
X=Wm['2026-05-01'][common].dropna(); tot=X.sum(axis=1); C=X.drop('GLOBAL'); T=tot.drop('GLOBAL'); rkT=T.rank(ascending=False).astype(int)
def comp(r): s=r.sum(); return dict(escritura=round(r['Thesis writing']/s*100,1),lectura=round(r['Literature review']/s*100,1),metodologia=round(r['Research methodology']/s*100,1))
rows=[dict(geo=k,pais=nom(k),academico=round(float(tot[k]),2),tesis=float(X.loc[k,'Thesis writing']),puesto=int(rkT[k]),n=len(T),**comp(X.loc[k])) for k in SIX+['USA']]
cm=pd.DataFrame([comp(C.loc[k]) for k in C.index]).median()
rows.append(dict(geo='MUNDO',pais='Mediana mundial',academico=round(T.median(),2),academico_p25=round(T.quantile(.25),2),academico_p75=round(T.quantile(.75),2),tesis=round(C['Thesis writing'].median(),2),n=len(T),escritura=round(cm.escritura,1),lectura=round(cm.lectura,1),metodologia=round(cm.metodologia,1)))
save('academico',rows,['aei_claude_ai_2026-06-26.csv','scholarly_request_map.csv'],[{'label':'Categorías','value':', '.join(common)}])
# 4. trayectoria (percentil del AUI en el conjunto fijo de países presentes en las cinco mediciones)
with contextlib.redirect_stdout(io.StringIO()):
    ns=runpy.run_path('scripts/07_trend.py')
A=ns['A']; gdp=ns['gdp']; F=A.dropna(); F=F[F.index.isin(gdp.dropna().index)]
pct=F.rank(pct=True)*100
rows=[dict(iso=k,pais=nom(k),periodo=p,percentil=round(float(pct.loc[k,p]),1),aui=round(float(F.loc[k,p]),2),n=len(F)) for k in LAT if k in F.index for p in F.columns]
med=pct.loc[[k for k in LAT if k in F.index]].median()
rows+=[dict(iso='LAT',pais='Mediana de América Latina',periodo=p,percentil=round(float(med[p]),1),n=len(F)) for p in F.columns]
save('tendencia',rows,['aei_enriched_claude_ai_2025-08-04_to_2025-08-11.csv','aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv','aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv','aei_claude_ai_2026-06-26.csv'])
# 5. febrero: cambio nov-2025 → feb-2026 del AUI, relativo al país mediano
south=['AUS','NZL','ZAF','ARG','CHL','URY','BRA','PER','PRY','BOL']
lc=np.log(F['2026-02']/F['2025-11']); lc=lc-lc.median()
rows=[dict(iso=k,pais=nom(k),cambio=round(float(np.exp(v)),3),hemisferio='Hemisferio sur' if k in south else 'Resto',latam=k in LAT) for k,v in lc.items()]
save('febrero',rows,['aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv','aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv','aei_enriched_claude_ai_2025-08-04_to_2025-08-11.csv'],[{'label':'Hemisferio sur','value':', '.join(south)}])
import os
for f in sorted(os.listdir('output/charts')): print(f, os.path.getsize('output/charts/'+f))
print([r['pais'] for r in json.load(open('output/charts/tendencia.json'))['rows'][::5]])
