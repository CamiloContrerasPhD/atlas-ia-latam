dash.draw('m_scatter',el=>{if(!CX.ready(el,['mundo']))return;const p=CX.prm();const t=CX.t;
const rows=dash.data('mundo').data.filter(o=>o.mes===p.mes).map(o=>({iso:o.iso,x:o.pib_ppa,y:o.aui,fit:o.aui_esperado,o}));
CX.scatter(el,rows,{xlog:true,ylog:true,href:1,xlab:t('PIB per cápita PPA, dólares internacionales (escala log)','GDP per capita PPP, international dollars (log scale)'),ylab:t('Índice de uso (escala log)','Usage index (log scale)'),aria:t('Dispersión por país del PIB per cápita PPA frente al índice de uso de Claude, con la línea que predice el ingreso','Scatter by country of GDP per capita PPP against the Claude usage index, with the line predicted by income'),
tip:r=>[t('Índice de uso: ','Usage index: ')+CX.fmt(r.o.aui,'f2'),t('Esperado por ingreso: ','Expected from income: ')+CX.fmt(r.o.aui_esperado,'f2'),t('Observado / esperado: ','Observed / expected: ')+CX.fmt(r.o.obs_esp,'f2'),t('Percentil del índice: ','Index percentile: ')+CX.fmt(r.o.percentil,'f0'),t('PIB per cápita PPA: $','GDP per capita PPP: $')+CX.fmt(r.o.pib_ppa,'f0')]});});

dash.draw('m_strip',el=>{if(!CX.ready(el,['mundo']))return;const p=CX.prm();const c=CX.ctx();const t=CX.t;
const rows=dash.data('mundo').data.filter(o=>o.mes===p.mes&&o.obs_esp!=null).map(o=>({iso:o.iso,band:c.reg(o.iso),x:o.obs_esp,o}));
CX.strip(el,rows,{bands:CX.REG.map(CX.tr),xlog:true,ref:1,xlab:t('Índice observado / esperado por ingreso (escala log)','Observed / income-expected index (log scale)'),aria:t('Puntos por país, agrupados por región: uso de Claude frente a lo esperado por ingreso','Dots by country, grouped by region: Claude usage against what income predicts'),
tip:r=>[t('Observado / esperado: ','Observed / expected: ')+CX.fmt(r.o.obs_esp,'f2'),t('Índice de uso: ','Usage index: ')+CX.fmt(r.o.aui,'f2'),t('Esperado: ','Expected: ')+CX.fmt(r.o.aui_esperado,'f2')]});});

window.CXL=(function(){const ALL=['Mundo'].concat(CX.REG);
function series(sub){const r=dash.data('lorenz');if(r.status!=='ok')return[];const p=CX.prm();const by=d3.group(r.data,o=>o.serie);
let names=sub?[...by.keys()].filter(k=>/subnacional/.test(k)):ALL.filter(k=>by.has(k));if(!sub&&p.region)names=names.filter(k=>k==='Mundo'||k===p.region);
const all=sub?[...by.keys()].filter(k=>/subnacional/.test(k)):ALL;
return names.map(k=>({name:CX.tr(k),color:CX.C[all.indexOf(k)%CX.C.length],pts:by.get(k).map(o=>({x:+o.x,y:+o.y})).sort((a,b)=>a.x-b.x)}));}
return{series};})();
dash.draw('m_lorenz_ley',el=>{const s=CXL.series(false);el.replaceChildren();s.forEach(x=>{const sp=document.createElement('span');const sw=document.createElement('span');sw.className='cx-sw';sw.style.background=x.color;sp.appendChild(sw);sp.appendChild(document.createTextNode(x.name));el.appendChild(sp);});const r=document.createElement('span');const sw=document.createElement('span');sw.className='cx-swr';r.appendChild(sw);r.appendChild(document.createTextNode(CX.t('Uso proporcional a la población','Usage proportional to population')));el.appendChild(r);});
dash.draw('m_lorenz',el=>{const r=dash.data('lorenz');const t=CX.t;if(r.status!=='ok'){CX.msg(el,r.status==='error'?t('No se pudo cargar este gráfico.','This chart could not be loaded.'):t('Cargando…','Loading…'));return;}
CX.lorenz(el,CXL.series(false),{xlab:t('% acumulado de la población de 15 a 64 años, de mayor a menor uso','Cumulative % of the population aged 15 to 64, from highest to lowest usage'),aria:t('Curvas de Lorenz del uso de Claude entre países, para el mundo y cada región','Lorenz curves of Claude usage across countries, for the world and each region')});});
dash.draw('m_gini',tb=>CX.table(tb,'gini',[{k:'serie',f:v=>CX.tr(v)},{k:'gini',f:v=>CX.fmt(v,'f2'),num:1},{k:'top10',f:v=>CX.fmt(v,'f1'),num:1},{k:'n',f:v=>CX.fmt(v,'f0'),num:1}],o=>!/subnacional/.test(o.serie)));

dash.draw('p_scatter',el=>{if(!CX.ready(el,['mundo']))return;const p=CX.prm();const t=CX.t;
const rows=dash.data('mundo').data.filter(o=>o.mes===p.mes&&o.trabajo!=null&&o.cursos!=null).map(o=>({iso:o.iso,x:o.trabajo,y:o.cursos,o}));
CX.scatter(el,rows,{xlab:t('Trabajo (% de las conversaciones)','Work (% of conversations)'),ylab:t('Cursos (% de las conversaciones)','Coursework (% of conversations)'),xf:v=>CX.F.f0(v),yf:v=>CX.F.f0(v),aria:t('Dispersión por país del peso de trabajo frente al peso de cursos en las conversaciones con Claude','Scatter by country of the work share against the coursework share of Claude conversations'),
tip:r=>[t('Trabajo: ','Work: ')+CX.fmt(r.o.trabajo,'f1')+' %',t('Cursos: ','Coursework: ')+CX.fmt(r.o.cursos,'f1')+' %',t('Personal: ','Personal: ')+CX.fmt(r.o.personal,'f1')+' %',t('Puesto en cursos: ','Coursework rank: ')+CX.fmt(r.o.puesto_cursos,'f0')]});});
dash.draw('p_tabla',tb=>{const c=CX.ctx();const p=c.p;CX.table(tb,'mundo',[{k:'iso',f:v=>c.name(v)},{k:'trabajo',f:v=>CX.fmt(v,'f1'),num:1},{k:'cursos',f:v=>CX.fmt(v,'f1'),num:1},{k:'personal',f:v=>CX.fmt(v,'f1'),num:1},{k:'puesto_cursos',f:v=>CX.fmt(v,'f0'),num:1}],o=>o.mes===p.mes&&c.hl(o.iso)&&c.vis(o.iso),(a,b)=>b.cursos-a.cursos);});

dash.draw('o_mes',sel=>{const p=CX.prm();const t=CX.t;sel.replaceChildren(new Option(t('Mayo de 2026','May 2026'),'2026-05'),new Option(t('Abril de 2026','April 2026'),'2026-04'));sel.value=p.mes;sel.setAttribute('aria-label',t('Mes','Month'));sel.onchange=()=>dash.setParams({mes:sel.value});});
