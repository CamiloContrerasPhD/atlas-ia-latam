"""Análisis con fuentes externas (mayo de 2026 en el índice; última medición disponible en cada fuente).
Escribe output/sitio/ext_*.json y vuelve a escribir output/sitio/covariables_pais.json con las variables nuevas.
Ejecutar después de 25_sitio_datos.py. Fuentes (carpeta data/nuevas, descargadas el 2026-11-20):
  - Microsoft AI Economy Institute, AI user share por país (vía Our World in Data, estimated-share-people-generative-ai.csv):
    % de la población de 15 a 64 años que usó un producto de IA generativa en el periodo; se usa marzo de 2026.
    Our World in Data advierte que a los países sin datos suficientes Microsoft les asigna el promedio de su región;
    se excluyen los valores que comparten al menos tres países de la misma región en la misma fecha.
  - UIT, ICT Price Baskets 2008-2025 (ITU_ICTPriceBaskets_2008-2025.xlsx): banda ancha móvil solo datos 5 GB
    (i271mb_5GB_GNI) y banda ancha fija 5 GB (i154_FBB5_GNI), en % del ingreso nacional bruto (INB) mensual per cápita, 2025.
  - Banco Mundial, INB per cápita, método Atlas, USD corrientes (NY.GNP.PCAP.CD), último dato 2020-2025.
    Costo de Claude Pro = 20 USD (precio de lista mensual) / (INB per cápita / 12) × 100.
  - UNESCO (UIS, vía la API del Banco Mundial, fuente 12): % de graduados terciarios en programas de ciencia, tecnología,
    ingeniería y matemáticas (UIS.FOSGP.5T8.F500600700) y en tecnologías de la información y la comunicación
    (UIS.FOSGP.5T8.F600); último dato 2015-2025.
  - GitHub Innovation Graph (developers.csv): cuentas de desarrolladores por economía, primer trimestre de 2026.
    Índice de desarrolladores = participación del país en las cuentas / participación en la población de 15 a 64 años,
    con la población de cada país tomada del propio índice de Anthropic (uso / índice de uso).
  - ILOSTAT (EMP_TEMP_SEX_OC2_NB_A): empleo por subgrupo principal de la CIUO-08 (dos dígitos), ambos sexos, último año
    desde 2018. Tablas de correspondencia: BLS SOC 2010 -> SOC 2018 (soc_2010_to_2018_crosswalk.xlsx) y BLS ISCO-08 <-> SOC
    2010 (isco08_soc10, paquete iscoCrosswalks de CRAN). Cuando un código corresponde a varios, su peso se reparte por igual.
Correlaciones: Spearman con intervalo al 95 % por bootstrap (1.000 remuestreos de países); la versión parcial descuenta
el PIB per cápita PPA (correlación de los residuos de los rangos)."""
import pandas as pd, numpy as np, json, os, sys, warnings, pycountry, pyreadr
from scipy import stats
sys.path.insert(0, 'scripts'); from regiones import LAT
warnings.filterwarnings('ignore'); rng = np.random.default_rng(26)
N = 'data/nuevas/'
CODE = open('scripts/26_fuentes_externas.py').read()
def dump(name, rows, extra=()):
    df = pd.DataFrame(rows).replace({np.nan: None})
    meta = [{'label': '26_fuentes_externas.py', 'value': CODE, 'type': 'code', 'lang': 'python'}] + list(extra)
    json.dump({'rows': json.loads(df.to_json(orient='records', double_precision=4)), 'meta': meta},
              open(f'output/sitio/{name}.json', 'w'), ensure_ascii=False)
    print(f'-> {name}: {len(df)} filas')
def iso3(a):
    try: return pycountry.countries.get(alpha_2=a).alpha_3
    except Exception: return None

d = pd.read_pickle('/tmp/aei26.pkl') if os.path.exists('/tmp/aei26.pkl') else pd.read_csv('data/aei_claude_ai_2026-06-26.csv', dtype={'node_external_id': str}, low_memory=False)
may = d[(d.date_start == '2026-05-01') & (d.geo_level == 'country')]
ov = may[may.category_name == 'overall'].pivot_table(index='geo_id', columns='metric_id', values='value')
aui = ov.usage_per_capita_index[ov.usage_per_capita_index > 0]
pop = (ov.usage_pct / ov.usage_per_capita_index)[aui.index]          # proporcional a la población de 15 a 64 años
gdp = pd.read_csv('data/worldbank_gdp_pc_ppp_2022_2024.csv').sort_values('year').groupby('iso3').last().gdp_pc_ppp_current_intl
cursos = ov.use_case_coursework_pct
s1 = may[(may.category_name == 'soc_occupation') & (may.hierarchy_level == 1) & (may.metric_id == 'pct')]
L1 = s1.pivot_table(index='geo_id', columns='node_external_id', values='value')
software = L1['15'] / L1.sum(axis=1) * 100                          # % del uso en tareas de ocupaciones de computación y matemáticas

def sp(x, y, B=1000):
    s = pd.concat([x, y], axis=1).dropna()
    r = stats.spearmanr(s.iloc[:, 0], s.iloc[:, 1])[0]
    bs = [stats.spearmanr(*s.iloc[rng.integers(0, len(s), len(s))].T.values)[0] for _ in range(B)]
    return r, np.nanpercentile(bs, 2.5), np.nanpercentile(bs, 97.5), len(s)
def parcial(x, y, z=np.log(gdp), B=1000):
    s = pd.concat([x, y, z], axis=1).dropna()
    def f(t):
        R = t.rank().values
        e = [R[:, k] - np.polyval(np.polyfit(R[:, 2], R[:, k], 1), R[:, 2]) for k in (0, 1)]
        return np.corrcoef(e[0], e[1])[0, 1]
    bs = [f(s.iloc[rng.integers(0, len(s), len(s))]) for _ in range(B)]
    return f(s), np.nanpercentile(bs, 2.5), np.nanpercentile(bs, 97.5), len(s)
COR = []
def cor(sec, orden, var, med, x, y):
    for aj, fn in [('Sin ajuste', sp), ('Descontando el ingreso', parcial)]:
        r, lo, hi, n = fn(x, y)
        COR.append(dict(id=f'{sec}|{var}|{med}|{aj}', seccion=sec, orden=orden, variable=var, medida=med, ajuste=aj, rho=r, bajo=lo, alto=hi, n=n))
        print(f'  {sec:9s} {var:32s} vs {med:28s} {aj:23s} rho={r:+.2f} [{lo:+.2f},{hi:+.2f}] n={n}')

# 1. Claude frente al uso de IA en general (Microsoft)
m = pd.read_csv(N + 'estimated-share-people-generative-ai.csv'); m.columns = ['ent', 'iso', 'dia', 'ia', 'pib_owid', 'reg']
m = m[m.iso.astype(str).str.len() == 3]
m['imputado'] = m.groupby(['dia', 'reg', 'ia']).iso.transform('size') >= 3
q = m[m.dia == '2026-03-31'].set_index('iso')
print('Microsoft, marzo 2026: economías', len(q), '| excluidas por valor regional repetido', int(q.imputado.sum()), sorted(q.index[q.imputado]))
A = q.ia[~q.imputado]
ok = aui.index.intersection(A.index)
b1, b0 = np.polyfit(np.log(A[ok]), np.log(aui[ok]), 1)
r2 = np.corrcoef(np.log(A[ok]), np.log(aui[ok]))[0, 1] ** 2
print(f'ln(índice) = {b0:.3f} + {b1:.3f}·ln(% que usa IA), R² = {r2:.2f}, n = {len(ok)}')
fit = np.exp(b0 + b1 * np.log(A[ok]))
dump('ext_ia', [dict(iso=c, ia=A[c], aui=aui[c], fit=fit[c], oe=aui[c] / fit[c]) for c in ok],
     [{'label': 'Ajuste', 'value': f'ln(índice de uso) = {b0:.3f} + {b1:.3f}·ln(% de 15 a 64 años que usa IA generativa); R² = {r2:.2f}; n = {len(ok)}'},
      {'label': 'Fuente', 'value': 'Microsoft AI Economy Institute, AI Diffusion Report (marzo de 2026), vía Our World in Data; índice de uso de Anthropic, mayo de 2026'}])
cor('ia', 0, '% que usa IA generativa (Microsoft)', 'Índice de uso de Claude', A, aui)

# 2. Costo frente al ingreso
g = pd.read_csv(N + 'wb_gni/API_NY.GNP.PCAP.CD_DS2_en_csv_v2_87042.csv', skiprows=4).set_index('Country Code')
gni = g[[str(y) for y in range(2020, 2026) if str(y) in g.columns]].ffill(axis=1).iloc[:, -1]
claude = 20 / (gni / 12) * 100
e = pd.read_excel(N + 'ITU_ICTPriceBaskets_2008-2025.xlsx', 'economies_2008-2025')
yc = [c for c in e.columns if str(c).startswith('2025')][0]
bam = e[e.Code == 'i271mb_5GB_GNI'].set_index('IsoCode')[yc].astype(float)
baf = e[e.Code == 'i154_FBB5_GNI'].set_index('IsoCode')[yc].astype(float)
C = aui.index
dump('ext_costo', [dict(iso=c, claude=claude.get(c), bam=bam.get(c), baf=baf.get(c), aui=aui[c], pib_ppa=gdp.get(c)) for c in C],
     [{'label': 'Fuente', 'value': 'UIT, ICT Price Baskets 2025 (banda ancha móvil 5 GB y fija 5 GB, % del INB mensual per cápita); Banco Mundial, INB per cápita Atlas; precio de lista de Claude Pro, 20 USD al mes'}])
cor('costo', 0, 'Claude Pro (% del ingreso mensual)', 'Índice de uso de Claude', claude, aui)
cor('costo', 1, 'Banda ancha móvil (% del ingreso)', 'Índice de uso de Claude', bam, aui)
cor('costo', 2, 'Banda ancha fija (% del ingreso)', 'Índice de uso de Claude', baf, aui)

# 3. Graduados por área (UNESCO)
u = pd.read_csv(N + 'uis_graduados_stem_tic.csv')
u = u[u.year >= 2015].sort_values('year').groupby(['indicator', 'iso3']).last()
stem = u.loc['UIS.FOSGP.5T8.F500600700'].value; tic = u.loc['UIS.FOSGP.5T8.F600'].value
ystem = u.loc['UIS.FOSGP.5T8.F500600700'].year
print('UNESCO: países con dato STEM', stem.index.isin(C).sum(), '| año mediano', ystem[ystem.index.isin(C)].median())
for k, (var, x) in enumerate([('Graduados en STEM (%)', stem), ('Graduados en TIC (%)', tic)]):
    cor('educacion', k, var, 'Índice de uso de Claude', x, aui)
    cor('educacion', k, var, 'Cursos (% de conversaciones)', x, cursos)
    cor('educacion', k, var, 'Computación (% del uso)', x, software)

# 4. Programación: desarrolladores (GitHub) y uso en tareas de computación
gh = pd.read_csv(N + 'github_developers.csv'); gh = gh[(gh.year == 2026) & (gh.quarter == 1)].copy()
gh['iso'] = gh.iso2_code.map(iso3); dev = gh.dropna(subset=['iso']).groupby('iso').developers.sum()
both = C.intersection(dev.index)
devidx = (dev[both] / dev[both].sum()) / (pop[both] / pop[both].sum())
print('GitHub: países en ambos', len(both))
dump('ext_dev', [dict(iso=c, devidx=devidx[c], software=software.get(c), aui=aui[c], cuentas=int(dev[c])) for c in both],
     [{'label': 'Fuente', 'value': 'GitHub Innovation Graph, developers.csv, primer trimestre de 2026 (cuentas, incluye inactivas); índice de Anthropic, mayo de 2026'}])
cor('dev', 0, 'Índice de desarrolladores (GitHub)', 'Computación (% del uso)', devidx, software)
cor('dev', 1, 'Índice de desarrolladores (GitHub)', 'Índice de uso de Claude', devidx, aui)

# 5. Uso frente a la estructura del empleo (ILOSTAT)
s0 = may[(may.category_name == 'soc_occupation') & (may.hierarchy_level == 0) & (may.metric_id == 'pct')].copy()
s0['soc18'] = s0.node_external_id.str[:7]
cob = s0.groupby('geo_id').value.sum()
x = pd.read_excel(N + 'soc_2010_to_2018_crosswalk.xlsx', header=8).iloc[:, :4]; x.columns = ['s10', 't10', 's18', 't18']
x = x.dropna(subset=['s10', 's18']); x['w'] = 1 / x.groupby('s18').s10.transform('size')
r = pyreadr.read_r(N + 'isco08_soc10.rda')['isco08_soc10'].copy()
r['s10'] = r.soc10.str[:2] + '-' + r.soc10.str[2:]; r['i2'] = r.isco08.str[:2]; r['w'] = 1 / r.groupby('s10').i2.transform('size')
w = x[['s18', 's10', 'w']].merge(r[['s10', 'i2', 'w']], on='s10', suffixes=('a', 'b')); w['w'] = w.wa * w.wb
w = w.groupby(['s18', 'i2']).w.sum().reset_index()
print('SOC 2018 detalladas del índice con correspondencia:', s0.soc18.isin(w.s18).mean().round(3))
U = s0.merge(w, left_on='soc18', right_on='s18'); U['v'] = U.value * U.w
U = U.groupby(['geo_id', 'i2']).v.sum().unstack(fill_value=0); U = U.div(U.sum(axis=1), axis=0)
il = pd.read_csv(N + 'ilostat_empleo_isco2.csv')
il = il[il.classif1.str.match(r'OC2_ISCO08_\d\d$')].copy(); il['i2'] = il.classif1.str[-2:]
il = il[il.time >= 2018]
last = il.groupby('ref_area').time.max(); il = il[il.time == il.ref_area.map(last)]
src = il.groupby('ref_area').source.first(); il = il[il.source == il.ref_area.map(src)]
E = il.pivot_table(index='ref_area', columns='i2', values='obs_value', aggfunc='sum').fillna(0)
E = E.drop(columns=[c for c in E.columns if c.startswith('0')]); U = U.drop(columns=[c for c in U.columns if c.startswith('0')], errors='ignore')
E = E.div(E.sum(axis=1), axis=0)
keep = [c for c in U.index if c in E.index and cob.get(c, 0) >= 70]
cols = sorted(set(U.columns) | set(E.columns))
U, E = U.reindex(index=keep, columns=cols, fill_value=0), E.reindex(index=keep, columns=cols, fill_value=0)
print('Empleo: países con ILOSTAT ≥2018 y cobertura ≥70 %:', len(keep), '| subgrupos', len(cols))
MAY = {'1': 'Directores y gerentes', '2': 'Profesionales científicos e intelectuales', '3': 'Técnicos y profesionales de nivel medio', '4': 'Personal de apoyo administrativo',
       '5': 'Trabajadores de los servicios y vendedores', '6': 'Agricultores y trabajadores agropecuarios calificados', '7': 'Oficiales, operarios y artesanos',
       '8': 'Operadores de instalaciones y máquinas', '9': 'Ocupaciones elementales'}
Um = U.T.groupby(U.columns.str[0]).sum().T; Em = E.T.groupby(E.columns.str[0]).sum().T
rowsP, rowsG = [], []
for c in keep:
    D = 50 * (U.loc[c] - E.loc[c]).abs().sum()
    rho = stats.spearmanr(U.loc[c], E.loc[c])[0]
    rowsP.append(dict(iso=c, disimilitud=D, rho=rho, anio=int(last[c]), cobertura=cob[c]))
    for k, nm in MAY.items(): rowsG.append(dict(id=f'{c}|{k}', iso=c, orden=int(k), grupo=nm, uso=Um.loc[c, k] * 100, empleo=Em.loc[c, k] * 100))
dump('ext_empleo_pais', rowsP, [{'label': 'Fuente', 'value': 'ILOSTAT EMP_TEMP_SEX_OC2_NB_A (último año desde 2018); índice de Anthropic, ocupaciones SOC detalladas, mayo de 2026; correspondencias del BLS'}])
dump('ext_empleo_grupos', rowsG)
R = (Um[list(MAY)] / Em[list(MAY)]).replace([np.inf], np.nan)
dump('ext_empleo_mayor', [dict(id=k, orden=int(k), grupo=nm, mediana=R[k].median(), p25=R[k].quantile(.25), p75=R[k].quantile(.75), n=int(R[k].notna().sum())) for k, nm in MAY.items()])
DP = pd.DataFrame(rowsP).set_index('iso')
print('Disimilitud: mediana %.1f, RIC %.1f-%.1f' % (DP.disimilitud.median(), DP.disimilitud.quantile(.25), DP.disimilitud.quantile(.75)))
print(DP[DP.index.isin(LAT)].round(2).to_string())
cor('empleo', 0, 'Disimilitud uso-empleo', 'Índice de uso de Claude', DP.disimilitud, aui)
dump('ext_cor', COR)

# 6. Variables nuevas en el explorador de variables por país
cv = pd.DataFrame(json.load(open('output/sitio/covariables_pais.json'))['rows']).set_index('iso')
cv = cv.drop(columns=[c for c in ['ia', 'costo_claude', 'bam', 'stem', 'tic', 'devidx', 'software'] if c in cv.columns])
for k, s in [('ia', A), ('costo_claude', claude), ('bam', bam), ('stem', stem), ('tic', tic), ('devidx', devidx), ('software', software)]:
    cv[k] = s.reindex(cv.index)
meta = json.load(open('output/sitio/covariables_pais.json'))['meta']
json.dump({'rows': json.loads(cv.reset_index().replace({np.nan: None}).to_json(orient='records', double_precision=4)),
           'meta': meta + [{'label': '26_fuentes_externas.py', 'value': CODE, 'type': 'code', 'lang': 'python'}]},
          open('output/sitio/covariables_pais.json', 'w'), ensure_ascii=False)
print('-> covariables_pais actualizado', cv.shape)
L = pd.DataFrame({'ia': A, 'claude_pct': claude, 'bam': bam, 'stem': stem, 'devidx': devidx, 'software': software, 'aui': aui}).reindex(LAT).round(2)
print(L.to_string())
