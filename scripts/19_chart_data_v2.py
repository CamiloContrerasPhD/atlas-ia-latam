"""Datos de los gráficos de la segunda ronda para el artefacto "Uso de Claude en América Latina" (output/charts/*.json, {rows, meta}).
Lee las salidas de los scripts 12 a 18; los intervalos de las correlaciones y de los AUC se recalculan aquí por bootstrap."""
import pandas as pd, numpy as np, json, gettext, pycountry, warnings
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
warnings.filterwarnings('ignore'); rng=np.random.default_rng(11)
es=gettext.translation('iso3166-1',pycountry.LOCALES_DIR,languages=['es'])
CORTO={'USA':'Estados Unidos','BOL':'Bolivia','GBR':'Reino Unido','KOR':'Corea del Sur','RUS':'Rusia','TZA':'Tanzania','VNM':'Vietnam','MDA':'Moldavia','TWN':'Taiwán','CZE':'Chequia','IRN':'Irán','VEN':'Venezuela'}
def nom(i):
    c=pycountry.countries.get(alpha_3=i); return CORTO.get(i, es.gettext(c.name) if c else i)
LAT=['ARG','BOL','BRA','CHL','COL','CRI','DOM','ECU','GTM','HND','MEX','PAN','PER','PRY','SLV','URY']
CODE=open('scripts/19_chart_data_v2.py').read()
def save(name,rows,inputs,extra=None):
    meta=[{'label':'19_chart_data_v2.py','value':CODE,'type':'code','lang':'python'},{'label':'Entrada','value':', '.join(inputs)}]+(extra or [])
    json.dump({'rows':rows,'meta':meta},open(f'output/charts/{name}.json','w'),ensure_ascii=False,allow_nan=False)
r2=lambda x: None if pd.isna(x) else round(float(x),4)  # 4 decimales: evita redondear dos veces al mostrar con 2 o 3
# 1. experimento del calendario
E=pd.read_csv('output/calendar_experiment.csv')
rows=[dict(id=f'{a}|{b}',nivel=a,codificacion=b,efecto=r2(c),bajo=r2(d),alto=r2(e),interaccion=r2(f),int_bajo=r2(g),int_alto=r2(h),p_int=r2(p),n_paises=int(n)) for a,b,c,d,e,f,g,h,p,n in E[['nivel','codificacion','efecto_pct','ic95_bajo','ic95_alto','interaccion_pp_por_DE_cursos','int_ic_bajo','int_ic_alto','p_int','n_paises']].itertuples(index=False)]
save('vacaciones',rows,['calendar_experiment.csv (script 12)'],[{'label':'Modelo','value':'log(AUI) = efecto fijo país + efecto fijo periodo + b·vacaciones; errores agrupados por país; efecto = 100·(exp(b)−1)'}])
# 2. subnacional
S=pd.read_csv('output/subnational_may2026.csv').dropna(subset=['intensidad'])
P={'CO':'Colombia','BR':'Brasil','MX':'México'}
rows=[dict(geo=g,pais=P[p],nombre=n,intensidad=r2(i),cursos=r2(c),uso_pct=r2(u)) for g,p,n,i,c,u in S[['geo_id','pais','nombre_g','intensidad','use_case_coursework_pct','usage_pct']].itertuples(index=False)]
save('subnacional',rows,['aei_claude_ai_2026-06-26.csv','pop_gemini.csv','pop_deepseek.csv'])
# 3. especialización: AUC con IC
V=pd.read_csv('output/rca_validation.csv'); V['grp']=V.iloc[:,1]; y=V.y.values
def boot(sc):
    a=roc_auc_score(y,sc); b=[]
    for _ in range(300):
        i=rng.integers(0,len(y),len(y)); b.append(roc_auc_score(y[i],sc[i]))
    return a,np.percentile(b,2.5),np.percentile(b,97.5)
pb=np.zeros(len(V)); pf=np.zeros(len(V))
for tr,te in GroupKFold(5).split(V,groups=V.geo):
    for c,o in [(['lr0'],pb),(['lr0','dens'],pf)]: o[te]=LogisticRegression().fit(V.iloc[tr][c],y[tr]).predict_proba(V.iloc[te][c])[:,1]
W=[];N=[]
for g,s in V.groupby('grp'):
    if s.y.nunique()==2 and len(s)>=10: W.append(roc_auc_score(s.y,s.dens)); N.append(len(s))
rows=[]
for k,(lab,sc) in enumerate([('Cercanía (densidad) en t0',V.dens.values),('Especialización previa en t0',V.lr0.values),('Modelo con ambas, países no vistos',pf),('Modelo solo con especialización previa, países no vistos',pb)]):
    a,l,h=boot(sc); rows.append(dict(orden=k,modelo=lab,auc=r2(a),bajo=r2(l),alto=r2(h)))
rows.append(dict(orden=4,modelo='Cercanía, dentro de cada grupo ocupacional',auc=r2(np.average(W,weights=N)),bajo=r2(np.percentile(W,25)),alto=r2(np.percentile(W,75))))
save('especializacion_auc',rows,['rca_validation.csv (script 15)'],[{'label':'Nota','value':'Intervalos al 95 % por bootstrap; para el AUC dentro de grupo, el intervalo es el rango intercuartílico entre grupos. Casos: '+str(len(V))+' pares país-grupo sin especialización en t0; '+str(int(y.sum()))+' nuevas especializaciones en t1.'}])
ES={'Legal Support Workers':'Apoyo legal','Lawyers, Judges, and Related Workers':'Abogados y jueces','Supervisors of Personal Care and Service Workers':'Supervisión de cuidado personal y servicios','Top Executives':'Alta dirección','Other Healthcare Support Occupations':'Otro apoyo en salud','Sales Representatives, Services':'Ventas de servicios','Art and Design Workers':'Arte y diseño','Advertising, Marketing, Promotions, Public Relations, and Sales Managers':'Dirección de publicidad, mercadeo y ventas','Other Healthcare Practitioners and Technical Occupations':'Otros profesionales técnicos de salud','Electrical and Electronic Equipment Mechanics, Installers, and Repairers':'Mecánica de equipos eléctricos','Entertainers and Performers, Sports and Related Workers':'Artistas, deportistas y afines','Business Operations Specialists':'Operaciones de negocio','Financial Specialists':'Especialistas financieros','Social Scientists and Related Workers':'Ciencias sociales','Other Personal Care and Service Workers':'Otros servicios de cuidado personal','Preschool, Elementary, Middle, Secondary, and Special Education Teachers':'Docencia escolar','Physical Scientists':'Ciencias físicas','Other Educational Instruction and Library Occupations':'Otra docencia y bibliotecas','Postsecondary Teachers':'Docencia universitaria'}
R=pd.read_csv('output/rca_latam.csv'); st=R[(R.rca_t0>=1.5)&(R.rca_t1>=1.5)].sort_values(['pais','rca_t1'],ascending=[True,False])
rows=[dict(id=f'{a}|{b}',iso=a,pais=nom(a),grupo=ES.get(c,c),rca_t0=r2(d),rca_t1=r2(e)) for a,b,c,d,e in st[['pais','grupo','nombre','rca_t0','rca_t1']].itertuples(index=False)]
save('especializacion_estable',rows,['rca_latam.csv (script 15)'],[{'label':'Criterio','value':'Especialización relativa ≥ 1,5 en t0 (ago y nov 2025) y en t1 (abr y may 2026)'}])
# 4. arquetipos
A=pd.read_csv('output/archetypes_ca.csv',index_col=0)
sd=A.d1_resid.std(); b=np.polyfit(A.lgdp,A.d1,1); edu=A.groupby('arquetipo').d1.mean().idxmin()  # arquetipo educativo = el de menor posición media en el eje 1
rows=[dict(iso=i,pais=nom(i),latam=bool(i in LAT),eje1=r2(d),pib_ppa=round(float(np.exp(g))),eje1_esperado=r2(np.polyval(b,g)),desvio_de=r2(res/sd),arquetipo='Educativo' if k==edu else 'Trabajo y ocio') for i,d,g,res,k in A[['d1','lgdp','d1_resid','arquetipo']].itertuples()]
save('arquetipos',rows,['aei_claude_ai_2026-06-26.csv','worldbank_gdp_pc_ppp_2022_2024.csv','archetypes_ca.csv (script 17)'],[{'label':'Eje 1','value':'Primera dimensión del análisis de correspondencias sobre 11 categorías mayores de solicitud; negativo = educación y documentos, positivo = trabajo, ocio y consultas prácticas.'}])
# 5. covariables: Spearman con IC
D=pd.read_csv('output/covariates_panel.csv',index_col=0)
XL={'lgdp':'PIB per cápita (PPA)','linv':'Investigadores por millón','terciaria':'Matrícula terciaria','internet':'Uso de internet','lrd':'Gasto en I+D','epi':'Dominio del inglés'}
YL={'laui':'Intensidad de uso','cursos':'Peso de cursos','academico':'Peso académico'}
rows=[]
for yv,yl in YL.items():
    for xv,xl in XL.items():
        s=D[[yv,xv]].dropna(); r=s.corr('spearman').iloc[0,1]
        bs=[s.iloc[rng.integers(0,len(s),len(s))].corr('spearman').iloc[0,1] for _ in range(500)]
        rows.append(dict(id=f'{yv}|{xv}',resultado=yl,variable=xl,rho=r2(r),bajo=r2(np.percentile(bs,2.5)),alto=r2(np.percentile(bs,97.5)),n=len(s)))
save('covariables',rows,['covariates_panel.csv (script 14)'],[{'label':'Nota','value':'Correlación de Spearman con intervalo al 95 % por bootstrap (500 remuestreos).'}])
# 6. OpenAlex
O=pd.read_csv('output/openalex_vs_usage.csv',index_col=0).dropna(subset=['llm_x1000_2025','laui'])
rows=[dict(iso=i,pais=nom(i),latam=bool(i in LAT),llm_por_mil=r2(l),aui=r2(np.exp(a)),articulos=int(t)) for i,l,a,t in O[['llm_x1000_2025','laui','total_2025']].itertuples()]
save('openalex',rows,['openalex_llm_by_country.csv','aei_claude_ai_2026-06-26.csv'],[{'label':'Búsqueda','value':'title_and_abstract.search: "large language model" OR "large language models" OR ChatGPT OR "generative AI" OR "generative artificial intelligence" OR GPT-4; type:article; conteo completo por país de afiliación'}])
import os; print({f:os.path.getsize('output/charts/'+f) for f in sorted(os.listdir('output/charts'))})
print(json.load(open('output/charts/especializacion_auc.json'))['rows'])
