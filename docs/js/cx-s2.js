window.CXF=['Lectura','Escritura','Análisis científico','Software','Mentoría y docencia','Ideación','Recolección de datos','Revisión por pares','Administración'];
dash.draw('c_flujos',el=>{if(!CX.ready(el,['ciencia_flujos']))return;const p=CX.prm();const t=CX.t;
const rows=dash.data('ciencia_flujos').data.filter(o=>o.version===p.version).map(o=>({iso:o.iso,band:CX.tr(o.flujo),x:o.peso==null?null:+o.peso,o}));
const mx=d3.max(rows,r=>r.x)||1;
CX.strip(el,rows,{bands:CXF.map(CX.tr),domain:[0,Math.ceil(mx/10)*10],xf:v=>CX.F.f0(v),xlab:t('% del uso científico del país','% of the country\'s scientific usage'),bh:62,aria:t('Puntos por país: peso de cada flujo de trabajo científico en el uso científico de Claude','Dots by country: share of each scientific workflow in scientific Claude usage'),
tip:r=>[CX.tr(r.o.flujo)+': '+CX.fmt(r.o.peso,'f1')+t(' % del uso científico','% of scientific usage')].concat(r.o.publicado?[]:[t('Ninguna categoría del flujo se publica para este país','No category of this workflow is published for this country')])});});

dash.draw('c_sin',el=>{const r=dash.data('ciencia_cobertura');const c=CX.ctx();const p=c.p;const t=CX.t;el.replaceChildren();if(r.status!=='ok'||!c.ok){el.textContent=r.status==='error'?t('No se pudo cargar la cobertura.','Coverage could not be loaded.'):'—';return;}
const miss=r.data.filter(o=>o.version===p.version&&!o.suficiente&&c.hl(o.iso)&&c.vis(o.iso)).sort((a,b)=>b.cobertura-a.cobertura);
if(!miss.length){el.textContent=t('Todos los países resaltados que cumplen los filtros tienen cobertura suficiente.','All highlighted countries that match the filters have sufficient coverage.');return;}
el.appendChild(document.createTextNode(t('Países resaltados sin cobertura suficiente (entre paréntesis, la cobertura): ','Highlighted countries without sufficient coverage (coverage in parentheses): ')));
miss.forEach((o,i)=>{el.appendChild(document.createTextNode((i?', ':'')+c.name(o.iso)+' ('));const b=document.createElement('span');b.textContent=CX.fmt(o.cobertura,'f0');el.appendChild(b);el.appendChild(document.createTextNode(' %)'));});el.appendChild(document.createTextNode('.'));});

dash.draw('c_tareas',box=>{const r=dash.data('ciencia_tareas');const c=CX.ctx();const p=c.p;const t=CX.t;box.replaceChildren();
if(r.status!=='ok'||!c.ok){CX.msg(box,r.status==='error'?t('No se pudo cargar esta tabla.','This table could not be loaded.'):t('Cargando…','Loading…'));return;}
const rows=r.data.filter(o=>o.version===p.version);const tasks=[...d3.rollup(rows,v=>d3.mean(v,o=>o.peso==null?0:+o.peso),o=>o.tarea)].sort((a,b)=>b[1]-a[1]).map(d=>d[0]);
const isos=[...new Set(rows.filter(o=>c.hl(o.iso)&&c.vis(o.iso)).map(o=>o.iso))].sort((a,b)=>c.name(a).localeCompare(c.name(b),CXI.L()));
if(!isos.length){CX.msg(box,t('Ningún país resaltado que cumpla los filtros tiene cobertura suficiente.','No highlighted country that matches the filters has sufficient coverage.'));return;}
const mx=d3.max(rows,o=>+o.peso)||1;const idx=new Map(rows.map(o=>[o.iso+'|'+o.tarea,o]));
const tb0=document.createElement('table');tb0.className='cx-table cx-heat';const th=document.createElement('thead');const hr=document.createElement('tr');
[t('País','Country')].concat(tasks.map(CX.tr)).forEach((x,i)=>{const h=document.createElement('th');h.textContent=x;if(i)h.className='cx-num';hr.appendChild(h);});th.appendChild(hr);tb0.appendChild(th);
const tb=document.createElement('tbody');isos.forEach(i=>{const tr=document.createElement('tr');const td0=document.createElement('td');td0.textContent=c.name(i);tr.appendChild(td0);
tasks.forEach(k=>{const o=idx.get(i+'|'+k);const td=document.createElement('td');td.className='cx-num';if(o&&o.peso!=null){const s=document.createElement('span');s.textContent=CX.fmt(o.peso,'f1');td.appendChild(s);
td.style.background='color-mix(in srgb, '+CX.C[0]+' '+Math.round(Math.min(55,+o.peso/mx*55))+'%, transparent)';}else td.textContent='—';tr.appendChild(td);});tb.appendChild(tr);});
tb0.appendChild(tb);box.appendChild(tb0);});

dash.draw('c_tareas_res',tb=>{const p=CX.prm();const n1=v=>CX.fmt(v,'f1');CX.table(tb,'ciencia_tareas_resumen',[{k:'tarea',f:v=>CX.tr(v)},{k:'flujo',f:v=>CX.tr(v)},{k:'peso_medio',f:n1,num:1},{k:'de',f:n1,num:1},{k:'n_paises',f:v=>CX.fmt(v,'f0'),num:1},{k:'difusion',f:n1,num:1},{k:'dif_inf',f:n1,num:1},{k:'dif_sup',f:n1,num:1}],o=>o.version===p.version,(a,b)=>b.peso_medio-a.peso_medio);});

dash.draw('c_pruebas',tb=>{const p=CX.prm();CX.table(tb,'ciencia_pruebas',[{k:'flujo',f:v=>CX.tr(v)},{k:'publicado_en',f:v=>CX.fmt(v,'f0'),num:1},{k:'p_regiones',f:v=>v==null?CX.t('no se prueba','not tested'):CX.fmt(v,'f3'),num:1}],o=>o.version===p.version,(a,b)=>CXF.indexOf(a.flujo)-CXF.indexOf(b.flujo));});

dash.draw('c_inv',el=>{const r=dash.data('involucramiento');const t=CX.t;if(r.status!=='ok'){CX.msg(el,r.status==='error'?t('No se pudo cargar este gráfico.','This chart could not be loaded.'):t('Cargando…','Loading…'));return;}el.replaceChildren();
const d=r.data.filter(o=>o.inv!=null).sort((a,b)=>b.inv-a.inv);const W=Math.max(280,el.clientWidth),bh=24,gap=14;
const svg=d3.select(el).append('svg').attr('width','100%').attr('role','img').attr('aria-label',t('Barras apiladas: involucramiento del usuario por flujo de trabajo científico, en revisión y verificación, agregado mundial','Stacked bars: user involvement by scientific workflow, split into revision and verification, world aggregate'));
const m={t:6,r:CX.measure(svg,['100,0 %'],'cx-val')+12,b:40,l:CX.measure(svg,d.map(o=>CX.tr(o.flujo)),'cx-ylab')+10};const H=m.t+m.b+d.length*(bh+gap)-gap;svg.attr('viewBox',`0 0 ${W} ${H}`).attr('height',H);
const x=d3.scaleLinear().domain([0,100]).range([m.l,W-m.r]);
[0,25,50,75,100].forEach(v=>{svg.append('line').attr('class','cx-grid').attr('x1',x(v)).attr('x2',x(v)).attr('y1',m.t).attr('y2',H-m.b);svg.append('text').attr('class','cx-tick').attr('x',x(v)).attr('y',H-m.b+16).attr('text-anchor','middle').text(v);});
svg.append('text').attr('class','cx-tick').attr('x',W-m.r).attr('y',H-4).attr('text-anchor','end').text(t('% de las conversaciones','% of conversations'));const T=CX.tip(el);
d.forEach((o,i)=>{const yy=m.t+i*(bh+gap),a=+o.revision,b=+o.verificacion;svg.append('text').attr('class','cx-ylab').attr('x',m.l-8).attr('y',yy+bh/2).attr('dy','0.35em').attr('text-anchor','end').text(CX.tr(o.flujo));
svg.append('rect').attr('x',x(0)).attr('y',yy).attr('width',x(100)-x(0)).attr('height',bh).attr('rx',7).attr('class','cx-track');
svg.append('rect').attr('x',x(0)).attr('y',yy).attr('width',Math.max(0,x(a)-x(0)-2)).attr('height',bh).attr('rx',7).style('fill','url(#cx-grad)').attr('class','cx-grow').style('animation-delay',(i*70)+'ms');
svg.append('rect').attr('x',x(a)+2).attr('y',yy).attr('width',Math.max(0,x(a+b)-x(a)-2)).attr('height',bh).attr('rx',7).style('fill','url(#cx-gradt)').attr('class','cx-grow').style('animation-delay',(380+i*70)+'ms');
let end=a+b;if(o.ic_inf!=null&&o.ic_sup!=null){const cy=yy+bh/2;svg.append('line').attr('x1',x(+o.ic_inf)).attr('x2',x(+o.ic_sup)).attr('y1',cy).attr('y2',cy).style('stroke','#101828').attr('stroke-width',1.5);[+o.ic_inf,+o.ic_sup].forEach(v=>svg.append('line').attr('x1',x(v)).attr('x2',x(v)).attr('y1',cy-5).attr('y2',cy+5).style('stroke','#101828').attr('stroke-width',1.5));end=Math.max(end,+o.ic_sup);}
svg.append('text').attr('class','cx-val cx-strong cx-rise').style('animation-delay',(700+i*70)+'ms').attr('x',x(end)+8).attr('y',yy+bh/2).attr('dy','0.35em').text(CX.fmt(o.inv,'f1')+' %');
svg.append('rect').attr('x',0).attr('y',yy-gap/2).attr('width',W).attr('height',bh+gap).attr('fill','transparent').on('pointermove',ev=>{const e=d3.pointer(ev,el);T.show([CX.tr(o.flujo),t('Involucramiento: ','Involvement: ')+CX.fmt(o.inv,'f1')+' %'+(o.ic_inf!=null?' ('+t('IC ','CI ')+CX.fmt(o.ic_inf,'f1')+t(' a ',' to ')+CX.fmt(o.ic_sup,'f1')+')':''),t('Revisión: ','Revision: ')+CX.fmt(a,'f1')+' %',t('Verificación: ','Verification: ')+CX.fmt(b,'f1')+' %',t('Aprender (aparte): ','Learning (separate): ')+CX.fmt(o.aprender,'f1')+' %',t('Delegación directa: ','Direct delegation: ')+CX.fmt(o.delegacion,'f1')+' %',t('Categorías: ','Categories: ')+o.n_categorias],e[0],e[1]);}).on('pointerleave',()=>T.hide());});});

dash.draw('c_mco',el=>{const r=dash.data('involucramiento_mco');const t=CX.t;if(r.status!=='ok'){CX.msg(el,r.status==='error'?t('No se pudo cargar este gráfico.','This chart could not be loaded.'):t('Cargando…','Loading…'));return;}
const S={'Categorías científicas, ponderadas por uso':['científicas, ponderadas','scientific, weighted'],'Categorías científicas, sin ponderar':['científicas, sin ponderar','scientific, unweighted'],'Todas las categorías':['todas las categorías','all categories']};
CX.forest(el,r.data,{label:o=>CX.tr(o.variable).split(' (')[0]+', '+(S[o.modelo]?t(S[o.modelo][0],S[o.modelo][1]):CX.tr(o.modelo)),v:'coef',lo:'ic_inf',hi:'ic_sup',ref:0,tf:v=>CX.F.f0(v),xlab:t('Puntos de involucramiento por desviación estándar','Involvement points per standard deviation'),aria:t('Coeficientes de pericia y duración sobre el involucramiento, con intervalos al 95 %','Coefficients of expertise and duration on involvement, with 95% intervals'),
tip:o=>[CX.tr(o.variable)+', '+CX.tr(o.modelo).toLowerCase(),t('Coeficiente: ','Coefficient: ')+CX.fmt(o.coef,'f1')+t(' puntos',' points'),t('Intervalo: ','Interval: ')+CX.fmt(o.ic_inf,'f1')+t(' a ',' to ')+CX.fmt(o.ic_sup,'f1'),'p: '+CX.fmt(o.p,'f3'),t('Categorías: ','Categories: ')+o.n]});});

dash.draw('c_cat',sel=>{const r=dash.data('involucramiento_pais');const p=CX.prm();sel.setAttribute('aria-label',CX.t('Categoría de solicitud','Request category'));if(r.status!=='ok'){sel.replaceChildren(new Option('Total','Total'));return;}
const cats=[...new Set(r.data.map(o=>o.categoria))].filter(x=>x!=='Total').sort((a,b)=>CX.tr(a).localeCompare(CX.tr(b),CXI.L()));sel.replaceChildren(new Option('Total','Total'),...cats.map(x=>new Option(CX.tr(x),x)));sel.value=p.categoria;sel.onchange=()=>dash.setParams({categoria:sel.value});});

dash.draw('c_invp',el=>{if(!CX.ready(el,['involucramiento_pais']))return;const c=CX.ctx();const p=c.p;const t=CX.t;const cat=CX.tr(p.categoria);
const rows=dash.data('involucramiento_pais').data.filter(o=>o.categoria===p.categoria).map(o=>({iso:o.iso,band:c.reg(o.iso),x:+o.inv,o}));
CX.strip(el,rows,{bands:CX.REG.map(CX.tr),xf:v=>CX.F.f0(v),xlab:t('% de conversaciones con iteración, retroalimentación o validación','% of conversations with iteration, feedback or validation'),aria:t('Puntos por país, agrupados por región: involucramiento del usuario en ','Dots by country, grouped by region: user involvement in ')+cat,
tip:r=>[cat+': '+CX.fmt(r.o.inv,'f1')+' %',t('Revisión: ','Revision: ')+CX.fmt(r.o.revision,'f1')+' %',t('Verificación: ','Verification: ')+CX.fmt(r.o.verificacion,'f1')+' %',t('Aprender (aparte): ','Learning (separate): ')+CX.fmt(r.o.aprender,'f1')+' %',t('Delegación directa: ','Direct delegation: ')+CX.fmt(r.o.delegacion,'f1')+' %']});});

dash.draw('o_version',sel=>{const p=CX.prm();const t=CX.t;sel.replaceChildren(new Option(t('Todo el uso','All usage'),'todo'),new Option(t('Solo la parte de trabajo','Work share only'),'trabajo'));sel.value=p.version;sel.setAttribute('aria-label',t('Versión del uso','Usage version'));sel.onchange=()=>dash.setParams({version:sel.value});});
