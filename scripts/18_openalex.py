"""Contraste con la producción científica (OpenAlex, consultado el 2026-11-19).
Artículos (type:article) por país de afiliación de algún autor (conteo completo: un artículo con autores de dos países
cuenta en ambos), 2023 y 2025; subconjunto cuyo título o resumen menciona modelos de lenguaje (large language model(s),
ChatGPT, generative AI, generative artificial intelligence, GPT-4). Indicador: artículos sobre LLM por cada mil artículos.
Se compara con el uso de Claude (índice de uso, peso de cursos, peso académico) y se ajusta por ingreso.
Mide investigación SOBRE modelos de lenguaje, no uso de modelos de lenguaje para investigar."""
import pandas as pd, numpy as np, pycountry
rng=np.random.default_rng(5)
o=pd.read_csv('data/openalex_llm_by_country.csv').pivot_table(index='country_code',columns='series',values='count')
def i3(a):
    try: return pycountry.countries.get(alpha_2=a).alpha_3
    except Exception: return None
o.index=[i3(a) for a in o.index]; o=o[o.index.notna()]
o['llm_x1000_2025']=o.llm_2025/o.total_2025*1000; o['llm_x1000_2023']=o.llm_2023/o.total_2023*1000
o['crec']=np.log(o.llm_x1000_2025/o.llm_x1000_2023)
C=pd.read_csv('output/covariates_panel.csv',index_col=0)
D=C.join(o,how='left'); D=D[D.total_2025>=1000]  # países con al menos 1.000 artículos en 2025
print('países con ≥1.000 artículos y uso de Claude:',len(D),'| mediana LLM por mil (2025): %.2f, RIC %.2f-%.2f'%(D.llm_x1000_2025.median(),D.llm_x1000_2025.quantile(.25),D.llm_x1000_2025.quantile(.75)))
def sp(a,b):
    s=D[[a,b]].dropna(); r=s.corr('spearman').iloc[0,1]; bs=[s.iloc[rng.integers(0,len(s),len(s))].corr('spearman').iloc[0,1] for _ in range(500)]
    return f'{r:+.2f} [{np.percentile(bs,2.5):+.2f},{np.percentile(bs,97.5):+.2f}] n={len(s)}'
for y in ['laui','cursos','academico']:
    print(f'Spearman LLM por mil 2025 vs {y}: {sp("llm_x1000_2025",y)}')
# residuos por ingreso de ambos lados
for v in ['llm_x1000_2025','laui']:
    s=D[[v,'lgdp']].dropna(); b=np.polyfit(s.lgdp,np.log(s[v]) if v!='laui' else s[v],1)
    D[v+'_res']=(np.log(D[v]) if v!='laui' else D[v])-np.polyval(b,D.lgdp)
print('Spearman residuos (ambos sin ingreso):',sp('llm_x1000_2025_res','laui_res'))
LAT=['ARG','BOL','BRA','CHL','COL','CRI','DOM','ECU','GTM','HND','MEX','PAN','PER','PRY','SLV','URY']
rk=D.llm_x1000_2025.rank(ascending=False)
t=D.loc[[c for c in LAT if c in D.index],['total_2025','llm_2025','llm_x1000_2023','llm_x1000_2025','crec']].copy(); t['puesto']=rk.reindex(t.index)
print(t.round(2).sort_values('llm_x1000_2025',ascending=False).to_string()); print('n países ranking:',len(D))
print('referencias LLM por mil 2025:',D.llm_x1000_2025.reindex(['USA','GBR','ESP','IDN','IND','KOR']).round(2).to_dict()); print('USA en datos OpenAlex:', 'USA' in o.index, '| en panel:', 'USA' in C.index)
D.to_csv('output/openalex_vs_usage.csv')
