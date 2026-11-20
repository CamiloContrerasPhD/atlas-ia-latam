"""Concentración del uso (análogo de la Fig. 1A del paper de OpenAI).
Unidad: país (y departamento/estado en CO, BR, MX). Intensidad = uso por persona en edad de trabajar (AUI).
Curva de Lorenz invertida ponderada por población: se ordenan las unidades de mayor a menor AUI y se acumula
x = participación en la población en edad de trabajar, y = participación en el uso.
Población de cada país: pob_i ∝ usage_pct_i / AUI_i (definición del AUI).
Gini = 1 - 2·∫L(p)dp con la curva ascendente."""
import pandas as pd, numpy as np, json
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv',usecols=['date_start','geo_id','geo_level','category_name','metric_id','value'])
o=d[(d.category_name=='overall')&d.metric_id.isin(['usage_pct','usage_per_capita_index'])&(d.geo_level=='country')]
import sys; sys.path.insert(0,'scripts'); from regiones import LAT
def lorenz(u,pop):
    df=pd.DataFrame({'u':u,'p':pop}); df['r']=df.u/df.p; df=df.sort_values('r',ascending=False)
    x=np.r_[0,(df.p.cumsum()/df.p.sum()).values]; y=np.r_[0,(df.u.cumsum()/df.u.sum()).values]
    xa=1-x[::-1]; ya=1-y[::-1]; gini=1-2*np.trapezoid(ya,xa)
    dec={f'{k*10}%':float(np.interp(k/10,x,y)) for k in range(1,11)}
    return x,y,gini,dec
out={}
for ds,g in o.groupby('date_start'):
    p=g.pivot_table(index='geo_id',columns='metric_id',values='value').dropna()
    p['pop']=p.usage_pct/p.usage_per_capita_index
    x,y,gi,dec=lorenz(p.usage_pct,p['pop'])
    lat=p.loc[p.index.isin(LAT)]
    xl,yl,gl,decl=lorenz(lat.usage_pct,lat['pop'])
    out[ds[:7]]=dict(n=len(p),gini=gi,deciles=dec,n_lat=len(lat),gini_lat=gl,deciles_lat=decl,
        curva=[[float(a),float(b)] for a,b in zip(x,y)],curva_lat=[[float(a),float(b)] for a,b in zip(xl,yl)])
    print(ds[:7],'países',len(p),'Gini',round(gi,3),'| 10% pob. top ->',round(dec['10%']*100,1),'% uso; 50% ->',round(dec['50%']*100,1))
    print('   AL',len(lat),'Gini',round(gl,3),'| 10% ->',round(decl['10%']*100,1),'50% ->',round(decl['50%']*100,1))
s=pd.read_csv('output/subnational_may2026.csv')
sub={}
for c,g in s.dropna(subset=['pob','usage_pct']).groupby('pais'):
    x,y,gi,dec=lorenz(g.usage_pct,g.pob)
    sub[c]=dict(n=len(g),gini=gi,deciles=dec,curva=[[float(a),float(b)] for a,b in zip(x,y)])
    print('subnacional',c,len(g),'Gini',round(gi,3),'10% ->',round(dec['10%']*100,1))
out['subnacional_2026-05']=sub
json.dump(out,open('output/concentracion.json','w'))
