"""Lee las tablas de calendario académico y de población producidas por Gemini (app web) y DeepSeek V4.1 Flash (Abacus),
valida el esquema y compara las dos fuentes. Salidas: data/delegated/calendario_{gemini,deepseek}.csv,
output/calendario_desacuerdos.csv y output/poblacion_comparada.csv."""
import re, glob, csv, io, pandas as pd
COLS=['iso3','pais','uni_V1','uni_V2','uni_V3','uni_V4','uni_V5','col_V1','col_V2','col_V3','col_V4','col_V5','fuente']
OK={'clases','vacaciones','mixto'}
def parse_file(fn):
    txt=open(fn,encoding='utf-8',errors='ignore').read()
    rows={}
    # formato lista python: ["ISO", "pais", ...]
    for m in re.finditer(r'\[\s*"([A-Z]{3})"\s*,(.*?)\]',txt):
        vals=next(csv.reader(io.StringIO(m.group(1)+','+m.group(2)),skipinitialspace=True))
        vals=[v.strip().strip('"') for v in vals]
        if len(vals)>=13: rows[vals[0]]=vals[:12]+[','.join(vals[12:])]
    # formato CSV plano
    for line in txt.splitlines():
        line=line.strip().strip('|')
        if re.match(r'^"?[A-Z]{3}"?\s*,',line):
            vals=next(csv.reader(io.StringIO(line),skipinitialspace=True))
            vals=[v.strip() for v in vals]
            if len(vals)>=13 and all(v.lower() in OK for v in vals[2:12]): rows[vals[0]]=vals[:12]+[','.join(vals[12:])]
    return rows
countries=[l.split(';')[0] for l in open('data/delegated/countries_113.txt',encoding='utf-8').read().splitlines()]
out={}
for model in ['gemini','deepseek']:
    R={}
    for fn in sorted(glob.glob(f'data/delegated/cal_{model}_*.csv')): R.update(parse_file(fn))
    df=pd.DataFrame(list(R.values()),columns=COLS)
    for c in COLS[2:12]: df[c]=df[c].str.lower()
    bad=df[~df[COLS[2:12]].isin(OK).all(axis=1)]
    print(model,'filas',len(df),'faltan',sorted(set(countries)-set(df.iso3)),'valores inválidos',len(bad))
    df.to_csv(f'data/delegated/calendario_{model}.csv',index=False); out[model]=df.set_index('iso3')
if all(len(v) for v in out.values()):
    G,D=out['gemini'],out['deepseek']; common=G.index.intersection(D.index)
    agree=(G.loc[common,COLS[2:12]]==D.loc[common,COLS[2:12]])
    print('países en ambas:',len(common),'| acuerdo por columna:',agree.mean().round(2).to_dict())
    dis=[]
    for iso in common:
        for c in COLS[2:12]:
            if G.loc[iso,c]!=D.loc[iso,c]: dis.append(dict(iso3=iso,pais=G.loc[iso,'pais'],col=c,gemini=G.loc[iso,c],deepseek=D.loc[iso,c]))
    pd.DataFrame(dis).to_csv('output/calendario_desacuerdos.csv',index=False); print('desacuerdos:',len(dis))
