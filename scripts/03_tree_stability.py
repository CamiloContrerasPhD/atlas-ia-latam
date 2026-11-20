"""Estabilidad de la reconstrucción hijo→padre (nivel 1→2): resuelve el mismo problema entero con
la correlación perturbada por ruido aleatorio (5 semillas, 6 padres candidatos por hijo) y cuenta en
cuántas soluciones factibles cada hijo cae bajo el mismo padre."""
import subprocess, pandas as pd, numpy as np, importlib.util, sys, warnings
warnings.filterwarnings('ignore')
src=open('scripts/02_request_tree_milp.py').read().split("lvl=int(sys.argv[1])")[0]
src=src.replace("cobj=-np.array([rho.loc[j,k] for j,k in cand])","cobj=-np.array([rho.loc[j,k] for j,k in cand])+np.random.default_rng(SEED).normal(0,0.15,n)")
src=src.replace("options={'time_limit':140}","options={'time_limit':28}")
sols=[]
for SEED in range(5):
    ns={'SEED':SEED}; exec(src,ns)
    o=ns['solve'](1,6)
    if o is not None: sols.append(o.set_index('child').parent_name.rename(f's{SEED}'))
S=pd.concat(sols,axis=1)
names=pd.read_csv('output/request_tree_level1.csv').set_index('child')
S['modal']=S.mode(axis=1)[0]; S['share']=(S.iloc[:,:len(sols)].eq(S.modal,axis=0)).mean(axis=1)
S['child_name']=names.child_name; S['pct_may']=names['global_pct_2026-05']
S.to_csv('output/request_tree_level1_stability.csv')
print('soluciones factibles:',len(sols))
print('hijos con el mismo padre en todas:',(S.share==1).mean().round(2))
for p in ['Research & Intelligence','Education & Learning']:
    t=S[S.modal==p].sort_values('pct_may',ascending=False)
    print('\n==',p,'| suma estable (share=1): %.2f | suma modal: %.2f'%(t[t.share==1].pct_may.sum(),t.pct_may.sum()))
    print(t[['child_name','pct_may','share']].to_string(index=False))
