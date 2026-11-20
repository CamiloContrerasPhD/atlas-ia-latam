window.CX=(function(){
const C=['#4F46E5','#14B8A6','#8B5CF6','#3B82F6','#2DD4BF','#F59E0B','#EC4899','#64748B'];
const LOC={es:d3.formatLocale({decimal:',',thousands:'.',grouping:[3],currency:['$','']}),en:d3.formatLocale({decimal:'.',thousands:',',grouping:[3],currency:['$','']})};
const FS={};Object.keys(LOC).forEach(k=>{FS[k]={f0:LOC[k].format(',.0f'),f1:LOC[k].format(',.1f'),f2:LOC[k].format(',.2f'),f3:LOC[k].format(',.3f')};});
const F={f0:v=>FS[CXI.L()].f0(v),f1:v=>FS[CXI.L()].f1(v),f2:v=>FS[CXI.L()].f2(v),f3:v=>FS[CXI.L()].f3(v)};
const t=CXI.t,tr=CXI.tr;
const fmt=(v,f)=>v==null||v===''||isNaN(+v)?'—':F[f||'f1'](+v);
const LAT=['ARG','BOL','BRA','CHL','COL','CRI','DOM','ECU','GTM','HND','MEX','PAN','PER','PRY','SLV','URY'];
const REG=['América Latina y el Caribe','Norteamérica','Europa y Asia Central','Asia Oriental y el Pacífico','Asia Meridional','Oriente Medio y Norte de África','África Subsahariana'];
const ING=['Ingreso alto','Ingreso mediano alto','Ingreso mediano bajo','Ingreso bajo'];
const CANDS=[[10,4,'start'],[-10,4,'end'],[0,-11,'middle'],[0,20,'middle'],[10,-9,'start'],[-10,-9,'end'],[10,17,'start'],[-10,17,'end'],[14,-16,'start'],[-14,-16,'end'],[14,24,'start'],[-14,24,'end']];
function prm(){const p=dash.params()||{};return{resaltar:Array.isArray(p.resaltar)?p.resaltar:LAT,region:p.region||'',ingreso:p.ingreso||'',mes:p.mes||'2026-05',version:p.version||'todo',categoria:p.categoria||'Total',cx:p.cx||'pib_ppa',cy:p.cy||'aui',rca_pais:p.rca_pais||'COL'};}
function ctx(){const r=dash.data('paises');const P=r.status==='ok'?new Map(r.data.map(o=>[o.iso,o])):new Map();const p=prm();const H=new Set(p.resaltar);
return{P,p,H,ok:r.status==='ok',vis:iso=>{const o=P.get(iso);if(!o)return false;return(!p.region||o.region===p.region)&&(!p.ingreso||o.ingreso===p.ingreso);},hl:iso=>H.has(iso),
name:iso=>{const o=P.get(iso);if(CXI.L()==='en'&&CXI.EN[iso])return CXI.EN[iso];return o?o.pais:iso;},reg:iso=>{const o=P.get(iso);return o?tr(o.region):'';},
col:iso=>{const o=P.get(iso);return o&&o.latam?CX.C[0]:CX.C[1];}};}
function msg(el,s){const m=document.createElement('div');m.className='cx-msg';m.textContent=s;el.replaceChildren(m);}
function ready(el,ids){for(const id of ['paises'].concat(ids)){const r=dash.data(id);if(r.status==='ok')continue;msg(el,r.status==='error'?t('No se pudo cargar este gráfico.','This chart could not be loaded.'):(r.status==='loading'?t('Cargando…','Loading…'):'—'));return false;}return true;}
function tip(el){const tp=document.createElement('div');tp.className='cx-tip';tp.hidden=true;el.appendChild(tp);
return{el,show(lines,x,y){tp.replaceChildren(...lines.map(l=>{const d=document.createElement('div');d.textContent=l;return d;}));tp.hidden=false;const w=el.clientWidth,tw=tp.offsetWidth,th=tp.offsetHeight;let L=x+16;if(L+tw>w)L=x-16-tw;if(L<0)L=0;let T=y-th-12;if(T<0)T=y+18;tp.style.left=L+'px';tp.style.top=T+'px';},hide(){tp.hidden=true;}};}
function measure(svg,texts,cls){const tx=svg.append('text').attr('class',cls);let w=0;texts.forEach(s=>{tx.text(s);w=Math.max(w,tx.node().getComputedTextLength());});tx.remove();return w;}
function place(svg,items,W){const pad=3;const boxes=svg.selectAll('text').nodes().map(n=>n.getBBox());svg.selectAll('circle.cx-doth').nodes().forEach(n=>{const b=n.getBBox();boxes.push({x:b.x-1,y:b.y-1,width:b.width+2,height:b.height+2});});const g=svg.append('g').attr('class','cx-labs');
items.forEach(it=>{const tx=g.append('text').attr('class','cx-lab').text(it.label);let ok=false;
for(const c of CANDS){tx.attr('x',it.x+c[0]).attr('y',it.y+c[1]).attr('text-anchor',c[2]);const b=tx.node().getBBox();if(b.x<0||b.x+b.width>W)continue;
if(!boxes.some(q=>q.x<b.x+b.width+pad&&b.x<q.x+q.width+pad&&q.y<b.y+b.height+pad&&b.y<q.y+q.height+pad)){boxes.push(b);ok=true;break;}}
if(!ok)tx.remove();});}
function trunc(tx,maxw){const s=tx.text();if(tx.node().getComputedTextLength()<=maxw)return;let n=s.length;while(n>4){n--;tx.text(s.slice(0,n)+'…');if(tx.node().getComputedTextLength()<=maxw)break;}}
function logTicks(d){let out=[];for(let e=Math.floor(Math.log10(d[0]));e<=Math.ceil(Math.log10(d[1]));e++)[1,2,5].forEach(k=>{const v=k*Math.pow(10,e);if(v>=d[0]&&v<=d[1])out.push(v);});if(out.length>8)out=out.filter(v=>Math.abs(Math.log10(v)-Math.round(Math.log10(v)))<1e-9);return out;}
function scale(log,ext,r){if(log){return d3.scaleLog().domain([ext[0]/1.12,ext[1]*1.12]).range(r);}const p=(ext[1]-ext[0])*0.05||1;return d3.scaleLinear().domain([ext[0]-p,ext[1]+p]).range(r).nice();}
function ticks(s,log,n){return log?logTicks(s.domain()):s.ticks(n);}
const numf=v=>Math.abs(v)>=1000?F.f0(v/1000)+t(' mil','k'):(Math.abs(v)<1&&v!==0?String(+v.toPrecision(2)).replace('.',t(',','.')):F.f0(v));
function svgOf(el,W,H,aria){return d3.select(el).append('svg').attr('width','100%').attr('height',H).attr('viewBox',`0 0 ${W} ${H}`).attr('role','img').attr('aria-label',aria);}
function vw(svg){const v=(svg.attr('viewBox')||'').split(' ');return +v[2]||600;}
function gridl(svg,x1,x2,y1,y2,i){return svg.append('line').attr('class','cx-grid').attr('x1',x1).attr('x2',x2).attr('y1',y1).attr('y2',y2).style('animation-delay',((i||0)*40)+'ms');}
function dots(svg,pts,c,X,Y,r){const W=vw(svg);const dim=pts.filter(p=>!c.hl(p.iso)),hi=pts.filter(p=>c.hl(p.iso));const R=r||4;
svg.append('g').selectAll('circle').data(dim).join('circle').attr('cx',p=>X(p)).attr('cy',p=>Y(p)).attr('r',R).attr('class','cx-dot cx-dotm').style('animation-delay',p=>Math.round(Math.max(0,X(p))/W*900)+'ms');
svg.append('g').selectAll('circle').data(hi).join('circle').attr('cx',p=>X(p)).attr('cy',p=>Y(p)).attr('r',R+2).style('fill',p=>c.col(p.iso)).attr('class','cx-dot cx-doth').style('animation-delay',p=>(700+Math.round(Math.max(0,X(p))/W*700))+'ms');}
function ring(svg){return svg.append('circle').attr('r',11).attr('class','cx-ring').style('display','none');}
function hover(svg,el,T,xy,data,f,maxd){const del=d3.Delaunay.from(xy);const rg=ring(svg);
svg.on('pointermove',ev=>{const p=d3.pointer(ev);const i=del.find(p[0],p[1]);const q=xy[i];if(!q||Math.hypot(q[0]-p[0],q[1]-p[1])>(maxd||26)){T.hide();rg.style('display','none');return;}rg.attr('cx',q[0]).attr('cy',q[1]).style('display',null);const e=d3.pointer(ev,el);T.show(f(data[i]),e[0],e[1]);}).on('pointerleave',()=>{T.hide();rg.style('display','none');});}
function scatter(el,rows,o){const c=ctx();el.replaceChildren();const T=tip(el);
const pts=rows.filter(r=>c.vis(r.iso)&&r.x!=null&&r.y!=null&&!isNaN(r.x)&&!isNaN(r.y)&&(!o.xlog||r.x>0)&&(!o.ylog||r.y>0));
if(!pts.length){msg(el,t('Ningún país con datos cumple los filtros.','No country with data matches the filters.'));return;}
const W=Math.max(280,el.clientWidth),H=o.H||Math.round(Math.max(300,Math.min(460,W*0.56))),m={t:26,r:16,b:46,l:54};
const svg=svgOf(el,W,H,o.aria);
const X=scale(o.xlog,d3.extent(pts,p=>p.x),[m.l,W-m.r]),Y=scale(o.ylog,d3.extent(pts,p=>p.y),[H-m.b,m.t]);
ticks(X,o.xlog,Math.max(3,Math.floor((W-m.l)/90))).forEach(v=>svg.append('text').attr('class','cx-tick').attr('x',X(v)).attr('y',H-m.b+20).attr('text-anchor','middle').text((o.xf||numf)(v)));
ticks(Y,o.ylog,6).forEach((v,i)=>{gridl(svg,m.l,W-m.r,Y(v),Y(v),i);svg.append('text').attr('class','cx-tick').attr('x',m.l-10).attr('y',Y(v)).attr('dy','0.35em').attr('text-anchor','end').text((o.yf||numf)(v));});
svg.append('line').attr('class','cx-base').attr('x1',m.l).attr('x2',W-m.r).attr('y1',H-m.b).attr('y2',H-m.b);
svg.append('text').attr('class','cx-tick').attr('x',W-m.r).attr('y',H-6).attr('text-anchor','end').text(o.xlab);
svg.append('text').attr('class','cx-tick').attr('x',m.l).attr('y',12).text(o.ylab);
if(o.href!=null){const d=Y.domain();if(o.href>=Math.min(...d)&&o.href<=Math.max(...d))svg.append('line').attr('class','cx-ref').attr('x1',m.l).attr('x2',W-m.r).attr('y1',Y(o.href)).attr('y2',Y(o.href));}
if(o.vref!=null){const d=X.domain();if(o.vref>=Math.min(...d)&&o.vref<=Math.max(...d))svg.append('line').attr('class','cx-ref').attr('x1',X(o.vref)).attr('x2',X(o.vref)).attr('y1',m.t).attr('y2',H-m.b);}
const fp=pts.filter(p=>p.fit!=null&&(!o.ylog||p.fit>0)).sort((a,b)=>a.x-b.x);if(fp.length>1)svg.append('path').attr('class','cx-fit cx-draw').attr('pathLength',1).attr('d',d3.line().x(p=>X(p.x)).y(p=>Y(p.fit))(fp));
const fx=p=>X(p.x),fy=p=>Y(p.y);dots(svg,pts,c,fx,fy);
place(svg,pts.filter(p=>c.hl(p.iso)).map(p=>({label:c.name(p.iso),x:fx(p),y:fy(p)})),W);
hover(svg,el,T,pts.map(p=>[fx(p),fy(p)]),pts,p=>[c.name(p.iso)+' · '+c.reg(p.iso)].concat(o.tip(p)));}
function strip(el,rows,o){const c=ctx();el.replaceChildren();const T=tip(el);
const pts=rows.filter(r=>c.vis(r.iso)&&r.x!=null&&!isNaN(r.x)&&(!o.xlog||r.x>0));
if(!pts.length){msg(el,t('Ningún país con datos cumple los filtros.','No country with data matches the filters.'));return;}
const bands=o.bands.filter(b=>pts.some(r=>r.band===b));const W=Math.max(280,el.clientWidth),rr=4,bh=o.bh||72;
const svg=d3.select(el).append('svg').attr('width','100%').attr('role','img').attr('aria-label',o.aria);
const lw=Math.min(W*0.36,measure(svg,bands,'cx-ylab'));const m={t:8,r:18,b:46,l:lw+18};const H=m.t+m.b+bands.length*bh;svg.attr('viewBox',`0 0 ${W} ${H}`).attr('height',H);
const X=o.domain?(o.xlog?d3.scaleLog():d3.scaleLinear()).domain(o.domain).range([m.l,W-m.r]):scale(o.xlog,d3.extent(pts,p=>p.x),[m.l,W-m.r]);
bands.forEach((b,i)=>{if(i%2===0)svg.append('rect').attr('class','cx-band').attr('x',4).attr('y',m.t+i*bh+2).attr('width',W-8).attr('height',bh-4).attr('rx',12);});
ticks(X,o.xlog,Math.max(3,Math.floor((W-m.l)/80))).forEach((v,i)=>{gridl(svg,X(v),X(v),m.t,H-m.b,i);svg.append('text').attr('class','cx-tick').attr('x',X(v)).attr('y',H-m.b+20).attr('text-anchor','middle').text((o.xf||numf)(v));});
svg.append('text').attr('class','cx-tick').attr('x',W-m.r).attr('y',H-6).attr('text-anchor','end').text(o.xlab);
if(o.ref!=null){const d=X.domain();if(o.ref>=d[0]&&o.ref<=d[1])svg.append('line').attr('class','cx-ref').attr('x1',X(o.ref)).attr('x2',X(o.ref)).attr('y1',m.t).attr('y2',H-m.b);}
const pos=[];
bands.forEach((b,i)=>{const y0=m.t+i*bh,cy=y0+bh/2;
const tx=svg.append('text').attr('class','cx-ylab').attr('x',m.l-14).attr('y',cy).attr('dy','0.35em').attr('text-anchor','end').text(b);trunc(tx,lw);
const ps=pts.filter(r=>r.band===b).map(r=>({r,x:X(r.x),y:null})).sort((a,q)=>a.x-q.x);
if(ps.length>=3){const v=ps.map(p=>p.r.x).sort(d3.ascending);const q1=d3.quantile(v,.25),q2=d3.quantile(v,.5),q3=d3.quantile(v,.75);const ih=Math.round(bh*0.6);
svg.append('rect').attr('x',X(q1)).attr('y',cy-ih/2).attr('width',Math.max(ih,X(q3)-X(q1))).attr('height',ih).attr('rx',ih/2).attr('class','cx-iqr cx-growc').style('animation-delay',(i*90)+'ms');
svg.append('rect').attr('x',X(q2)-2.5).attr('y',cy-ih/2-4).attr('width',5).attr('height',ih+8).attr('rx',2.5).attr('class','cx-med cx-rise').style('animation-delay',(450+i*90)+'ms');}
const placed=[];ps.forEach(p=>{for(let k=0;k<80;k++){const off=(k%2?1:-1)*Math.ceil(k/2)*(rr+1);if(Math.abs(off)>bh/2-rr-2)continue;const yy=cy+off;if(placed.every(q=>Math.hypot(q.x-p.x,q.y-yy)>=2*rr+1)){p.y=yy;break;}}if(p.y==null)p.y=cy;placed.push(p);pos.push(p);});});
dots(svg,pos.map(p=>Object.assign({iso:p.r.iso},{_x:p.x,_y:p.y})),c,p=>p._x,p=>p._y,rr);
place(svg,pos.filter(p=>c.hl(p.r.iso)).map(p=>({label:c.name(p.r.iso),x:p.x,y:p.y})),W);
hover(svg,el,T,pos.map(p=>[p.x,p.y]),pos.map(p=>p.r),r=>[c.name(r.iso)+' · '+c.reg(r.iso)].concat(o.tip(r)),20);}
function forest(el,rows,o){el.replaceChildren();const W=Math.max(260,el.clientWidth);
const svg=d3.select(el).append('svg').attr('width','100%').attr('role','img').attr('aria-label',o.aria);
const maxw=Math.min(W*0.42,260);const lw=Math.min(maxw,measure(svg,rows.map(o.label),'cx-ylab'));const vf=o.vf||o.tf;const vwid=measure(svg,rows.map(r=>vf(+r[o.v])),'cx-val');
const bh=40,m={t:8,r:vwid+26,b:42,l:lw+18},H=m.t+m.b+rows.length*bh;svg.attr('viewBox',`0 0 ${W} ${H}`).attr('height',H);
const lo=d3.min(rows,r=>+r[o.lo]),hi=d3.max(rows,r=>+r[o.hi]);
const x=d3.scaleLinear().domain(o.domain||[Math.min(o.ref,lo),Math.max(o.ref,hi)]).range([m.l,W-m.r]).nice();
x.ticks(Math.max(3,Math.floor((W-m.l)/80))).forEach((v,i)=>{gridl(svg,x(v),x(v),m.t,H-m.b,i);svg.append('text').attr('class','cx-tick').attr('x',x(v)).attr('y',H-m.b+20).attr('text-anchor','middle').text(o.tf(v));});
svg.append('text').attr('class','cx-tick').attr('x',W-m.r).attr('y',H-4).attr('text-anchor','end').text(o.xlab);
const T=tip(el);const rows_g=svg.append('g');
svg.append('line').attr('class','cx-ref').attr('x1',x(o.ref)).attr('x2',x(o.ref)).attr('y1',m.t).attr('y2',H-m.b);
rows.forEach((r,i)=>{const cy=m.t+i*bh+bh/2;const bg=rows_g.append('rect').attr('x',2).attr('y',cy-bh/2+3).attr('width',W-4).attr('height',bh-6).attr('rx',10).attr('class','cx-rowbg');
const tx=svg.append('text').attr('class','cx-ylab').attr('x',m.l-14).attr('y',cy).attr('dy','0.35em').attr('text-anchor','end').text(o.label(r));trunc(tx,lw);
svg.append('rect').attr('x',m.l).attr('y',cy-5).attr('width',Math.max(0,W-m.r-m.l)).attr('height',10).attr('rx',5).attr('class','cx-track');
svg.append('rect').attr('x',x(+r[o.lo])).attr('y',cy-5).attr('width',Math.max(10,x(+r[o.hi])-x(+r[o.lo]))).attr('height',10).attr('rx',5).style('fill','url(#cx-grad)').attr('class','cx-grow').style('animation-delay',(i*80)+'ms');
svg.append('circle').attr('cx',x(+r[o.v])).attr('cy',cy).attr('r',6.5).attr('class','cx-dot cx-est').style('animation-delay',(450+i*80)+'ms');
svg.append('text').attr('class','cx-val cx-strong cx-rise').attr('x',W-m.r+12).attr('y',cy).attr('dy','0.35em').style('animation-delay',(600+i*80)+'ms').text(vf(+r[o.v]));
svg.append('rect').attr('x',0).attr('y',cy-bh/2).attr('width',W).attr('height',bh).attr('fill','transparent').on('pointerenter',()=>bg.classed('cx-on',true)).on('pointermove',ev=>{const p=d3.pointer(ev,el);T.show(o.tip(r),p[0],p[1]);}).on('pointerleave',()=>{bg.classed('cx-on',false);T.hide();});});}
function table(tb,ds,cols,filter,sort){const r=dash.data(ds);tb.replaceChildren();
if(r.status==='error'){const tr0=document.createElement('tr');const td=document.createElement('td');td.colSpan=cols.length;td.textContent=t('No se pudo cargar esta tabla.','This table could not be loaded.');tr0.appendChild(td);tb.appendChild(tr0);return;}
if(r.status!=='ok'||!Array.isArray(r.data))return;let rows=filter?r.data.filter(filter):r.data;if(sort)rows=[...rows].sort(sort);
if(!rows.length){const tr0=document.createElement('tr');const td=document.createElement('td');td.colSpan=cols.length;td.className='cx-cap';td.textContent=t('Ninguna fila cumple los filtros.','No row matches the filters.');tr0.appendChild(td);tb.appendChild(tr0);return;}
rows.forEach((o,i)=>{const tr0=document.createElement('tr');tr0.style.animationDelay=Math.min(i*35,600)+'ms';if(o.id!=null)tr0.dataset.key=o.id;cols.forEach(cl=>{const td=document.createElement('td');td.textContent=cl.f?cl.f(o[cl.k],o):o[cl.k];if(cl.num)td.className='cx-num';tr0.appendChild(td);});tb.appendChild(tr0);});}
function lorenz(el,series,o){el.replaceChildren();const T=tip(el);if(!series.length){msg(el,'—');return;}
const W=Math.max(280,el.clientWidth),H=Math.round(Math.max(280,Math.min(420,W*0.56))),m={t:26,r:16,b:46,l:44};
const svg=svgOf(el,W,H,o.aria);const x=d3.scaleLinear().domain([0,100]).range([m.l,W-m.r]),y=d3.scaleLinear().domain([0,100]).range([H-m.b,m.t]);
const gid=(el.id||'cx-lz')+'-area';const lg=svg.append('defs').append('linearGradient').attr('id',gid).attr('x1',0).attr('x2',0).attr('y1',0).attr('y2',1);lg.append('stop').attr('offset',0).attr('stop-color',series[0].color).attr('stop-opacity',0.24);lg.append('stop').attr('offset',1).attr('stop-color',series[0].color).attr('stop-opacity',0);
[0,25,50,75,100].forEach((v,i)=>{svg.append('text').attr('class','cx-tick').attr('x',x(v)).attr('y',H-m.b+20).attr('text-anchor',v===0?'start':(v===100?'end':'middle')).text(v);gridl(svg,m.l,W-m.r,y(v),y(v),i);svg.append('text').attr('class','cx-tick').attr('x',m.l-10).attr('y',y(v)).attr('dy','0.35em').attr('text-anchor','end').text(v);});
svg.append('path').attr('class','cx-area').attr('fill',`url(#${gid})`).attr('d',d3.area().curve(d3.curveMonotoneX).x(p=>x(p.x)).y0(y(0)).y1(p=>y(p.y))(series[0].pts));
svg.append('line').attr('class','cx-ref').attr('x1',x(0)).attr('y1',y(0)).attr('x2',x(100)).attr('y2',y(100));
svg.append('text').attr('class','cx-tick').attr('x',m.l).attr('y',12).text(t('% acumulado del uso','Cumulative % of usage'));
svg.append('text').attr('class','cx-tick').attr('x',W-m.r).attr('y',H-6).attr('text-anchor','end').text(o.xlab);
series.forEach((s,si)=>svg.append('path').attr('fill','none').attr('stroke-width',si===0?3:2.25).attr('stroke-linecap','round').attr('stroke-linejoin','round').attr('pathLength',1).attr('class','cx-draw').style('animation-delay',(si*140)+'ms').style('stroke',s.color).attr('d',d3.line().curve(d3.curveMonotoneX).x(p=>x(p.x)).y(p=>y(p.y))(s.pts)));
const at=(pts,xv)=>{const i=d3.bisector(p=>p.x).left(pts,xv);if(i<=0)return pts[0].y;if(i>=pts.length)return pts[pts.length-1].y;const a=pts[i-1],b=pts[i];const k=(b.x-a.x)?(xv-a.x)/(b.x-a.x):0;return a.y+k*(b.y-a.y);};
const cross=svg.append('line').attr('class','cx-cross').attr('y1',m.t).attr('y2',H-m.b).style('display','none');const mk=svg.append('g').style('display','none');const mks=series.map(s=>mk.append('circle').attr('r',5).attr('class','cx-mk').style('fill',s.color));
svg.append('rect').attr('x',m.l).attr('y',m.t).attr('width',Math.max(0,W-m.l-m.r)).attr('height',Math.max(0,H-m.t-m.b)).attr('fill','transparent').on('pointermove',ev=>{const p=d3.pointer(ev);const xv=Math.max(0,Math.min(100,x.invert(p[0])));cross.attr('x1',x(xv)).attr('x2',x(xv)).style('display',null);mk.style('display',null);series.forEach((s,i)=>mks[i].attr('cx',x(xv)).attr('cy',y(at(s.pts,xv))));const e=d3.pointer(ev,el);T.show([F.f0(xv)+t(' % de la población que más usa','% of the population that uses most')].concat(series.map(s=>s.name+': '+F.f1(at(s.pts,xv))+t(' % del uso','% of usage'))),e[0],e[1]);}).on('pointerleave',()=>{T.hide();cross.style('display','none');mk.style('display','none');});}
function legend(host,items){host.replaceChildren();items.forEach(it=>{const s=document.createElement('span');const sw=document.createElement('span');sw.className='cx-sw';sw.style.background=it.color;s.appendChild(sw);s.appendChild(document.createTextNode(it.name));host.appendChild(s);});}
return{t,tr,C,F,fmt,LAT,REG,ING,prm,ctx,msg,ready,tip,measure,place,trunc,scatter,strip,forest,table,lorenz,legend,numf,svgOf,gridl,ring,vw};})();
