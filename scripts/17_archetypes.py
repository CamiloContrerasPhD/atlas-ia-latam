"""Arquetipos de uso por país (mayo 2026): tabla país × 20 categorías mayores de solicitud (todas publicadas por país).
Solo categorías publicadas en ≥ 95 % de los países y países sin celdas suprimidas (una celda suprimida no es cero).
(1) Análisis de correspondencias (CA) por descomposición en valores singulares, filas con igual masa (cada país pesa lo
mismo); (2) transformación logarítmica centrada (CLR) y k-medias con k elegido por silueta (k=2..8, 50 inicios);
(3) perfil de cada arquetipo como especialización relativa media por categoría. Se ubica a América Latina."""
import pandas as pd, numpy as np, warnings
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
warnings.filterwarnings('ignore')
d=pd.read_csv('data/aei_claude_ai_2026-06-26.csv',dtype={'node_external_id':str})
q=d[(d.geo_level=='country')&(d.category_name=='request')&(d.metric_id=='pct')&(d.hierarchy_level==2)&(d.date_start=='2026-05-01')]
N=q.pivot_table(index='geo_id',columns='node_name',values='value')
print('países',len(N),'categorías',N.shape[1],'faltantes',int(N.isna().sum().sum()))
miss=N.isna().mean().sort_values(ascending=False); print('faltantes por categoría:',miss[miss>0].round(2).to_dict())
N=N.loc[:,miss[miss<=0.05].index]; N=N.dropna()  # sin ceros artificiales: categorías publicadas en ≥95 % de países y países completos
print('tras filtrar: países',len(N),'categorías',N.shape[1]); P=N.div(N.sum(axis=1),axis=0)
# CA con masa de fila igual
r=np.full(len(P),1/len(P)); c=(P.mul(r,axis=0)).sum(axis=0).values
S=(P.mul(r,axis=0).values-np.outer(r,c))/np.sqrt(np.outer(r,c))
U,sv,Vt=np.linalg.svd(S,full_matrices=False); inert=sv**2/np.sum(sv**2)
F=(U*sv)/np.sqrt(r)[:,None]; G=(Vt.T*sv)/np.sqrt(c)[:,None]
print('inercia explicada dim1-3:',np.round(inert[:3],3))
cats=pd.DataFrame(G[:,:2],index=P.columns,columns=['d1','d2'])
print('categorías en dim1 (extremos):',cats.d1.sort_values().round(2).iloc[[0,1,2,-3,-2,-1]].to_dict())
print('categorías en dim2 (extremos):',cats.d2.sort_values().round(2).iloc[[0,1,2,-3,-2,-1]].to_dict())
rows=pd.DataFrame(F[:,:2],index=P.index,columns=['d1','d2'])
# CLR + k-medias
L=np.log(P+1e-4); CLR=L.sub(L.mean(axis=1),axis=0)
best=None
for k in range(2,9):
    km=KMeans(k,n_init=50,random_state=0).fit(CLR); s=silhouette_score(CLR,km.labels_)
    print(f'k={k} silueta {s:.3f}'); best=(s,k,km) if best is None or s>best[0] else best
s,k,km=best; lab=pd.Series(km.labels_,index=P.index)
# estabilidad: misma partición con otras semillas y con 90 % de los países
from sklearn.metrics import adjusted_rand_score
ari=[]
rng=np.random.default_rng(0)
for b in range(30):
    i=rng.choice(len(CLR),int(0.9*len(CLR)),replace=False); kb=KMeans(k,n_init=20,random_state=b).fit(CLR.iloc[i])
    ari.append(adjusted_rand_score(lab.iloc[i],kb.labels_))
print(f'elegido k={k} (silueta {s:.3f}); estabilidad ARI submuestras 90 %%: mediana {np.median(ari):.2f}, RIC {np.percentile(ari,25):.2f}-{np.percentile(ari,75):.2f}')
RCA=P.div(P.mean(axis=0),axis=1)
LAT=['ARG','BOL','BRA','CHL','COL','CRI','DOM','ECU','GTM','HND','MEX','PAN','PER','PRY','SLV','URY']
gdp=pd.read_csv('data/worldbank_gdp_pc_ppp_2022_2024.csv').sort_values('year').groupby('iso3').last().gdp_pc_ppp_current_intl
for g in range(k):
    m=lab[lab==g].index; prof=RCA.loc[m].mean().sort_values(ascending=False)
    print(f'\nArquetipo {g}: {len(m)} países | PIB PPA mediano {gdp.reindex(m).median():,.0f} | más usa: '+', '.join(f'{c} {v:.2f}' for c,v in prof.head(4).items())+' | menos usa: '+', '.join(f'{c} {v:.2f}' for c,v in prof.tail(3).items()))
    print('   América Latina:',[c for c in m if c in LAT],'| ejemplos:',[c for c in m if c not in LAT][:12])
out=rows.assign(arquetipo=lab,latam=lambda x: x.index.isin(LAT)); out.to_csv('output/archetypes_ca.csv'); cats.to_csv('output/archetypes_ca_categories.csv')
# posición en el eje 1 (educación ↔ trabajo/ocio) frente a lo esperado por ingreso
Rw=out.join(np.log(gdp).rename('lgdp')).dropna(); b=np.polyfit(Rw.lgdp,Rw.d1,1); Rw['d1_resid']=Rw.d1-np.polyval(b,Rw.lgdp)
sd=Rw.d1_resid.std(); pr=Rw.d1.rank(pct=True)*100
print('\nEje 1 (negativo = educativo): correlación con log PIB %.2f; DE del residuo %.2f'%(Rw.d1.corr(Rw.lgdp),sd))
print({c:(round(Rw.loc[c,'d1'],2),int(pr[c]),round(Rw.loc[c,'d1_resid']/sd,2)) for c in LAT if c in Rw.index})
Rw.to_csv('output/archetypes_ca.csv')
