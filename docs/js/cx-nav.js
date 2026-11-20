(function(){
const V={adopcion:['mundo','ext-ia','subnacional','tiempo'],condiciones:['ext-costo','ext-edu','estructura-b'],usos:['proposito','estructura','ext-empleo','ext-dev'],ciencia:['ciencia','openalex'],metodo:['metodo']};
const TABS=Object.keys(V);
function open(id){if(!TABS.includes(id)){const el=document.getElementById(id);const sec=el&&(el.classList.contains('cx-sec')?el:el.closest('.cx-sec'));id=(sec&&TABS.find(k=>V[k].includes(sec.id)))||'adopcion';}const on=new Set(V[id]);let k=0;document.querySelectorAll('.cx-sec').forEach(s=>{s.hidden=!on.has(s.id);if(!s.hidden)s.style.animationDelay=(k++*90)+'ms';});document.querySelectorAll('.cx-nav button[data-tab]').forEach(b=>b.setAttribute('aria-selected',b.dataset.tab===id?'true':'false'));}
document.querySelectorAll('.cx-nav button[data-tab]').forEach(b=>b.addEventListener('click',()=>{open(b.dataset.tab);dash.setLink(b.dataset.tab);}));
const h=(location.hash||'').replace('#','');if(h){const sec=TABS.includes(h)?h:(document.getElementById(h)&&document.getElementById(h).closest('.cx-sec')?document.getElementById(h).closest('.cx-sec').id:'');open(sec||'adopcion');}else open('adopcion');
let before=null;window.addEventListener('beforeprint',()=>{if(before)return;before=[...document.querySelectorAll('.cx-sec')].map(s=>s.hidden);document.querySelectorAll('.cx-sec').forEach(s=>{s.hidden=false;});});
window.addEventListener('afterprint',()=>{if(!before)return;const b=before;before=null;document.querySelectorAll('.cx-sec').forEach((s,i)=>{s.hidden=b[i];});});
document.querySelectorAll('.cx [data-sw]').forEach(s=>{const v=s.dataset.sw;s.style.background=v==='m'?'#C9CEDA':CX.C[+v];});
document.querySelectorAll('#btn-latam').forEach(b=>b.addEventListener('click',()=>dash.setParams({resaltar:CX.LAT})));
document.querySelectorAll('#btn-limpiar').forEach(b=>b.addEventListener('click',()=>dash.setParams({resaltar:[]})));
document.querySelectorAll('.cx-lang button[data-lang]').forEach(b=>b.addEventListener('click',()=>dash.setParams({lang:b.dataset.lang==='en'?'en':null})));
const sync=()=>{const en=CXI.L()==='en';document.documentElement.lang=en?'en':'es';document.querySelectorAll('.cx').forEach(r=>r.classList.toggle('cx-en',en));document.querySelectorAll('.cx-lang button[data-lang]').forEach(b=>b.setAttribute('aria-pressed',(b.dataset.lang==='en')===en?'true':'false'));};
sync();dash.onData(sync);
})();
dash.draw('f_region',sel=>{const p=CX.prm();sel.setAttribute('aria-label',CX.t('Región','Region'));sel.replaceChildren(new Option(CX.t('Todas','All'),''),...CX.REG.map(r=>new Option(CX.tr(r),r)));sel.value=p.region;sel.onchange=()=>dash.setParams({region:sel.value});});
dash.draw('f_ingreso',sel=>{const p=CX.prm();sel.setAttribute('aria-label',CX.t('Nivel de ingreso','Income level'));sel.replaceChildren(new Option(CX.t('Todos','All'),''),...CX.ING.map(r=>new Option(CX.tr(r),r)));sel.value=p.ingreso;sel.onchange=()=>dash.setParams({ingreso:sel.value});});
dash.draw('f_pais',sel=>{const c=CX.ctx();sel.setAttribute('aria-label',CX.t('Añadir un país resaltado','Add a highlighted country'));const opts=[...c.P.values()].filter(o=>!c.hl(o.iso)).sort((a,b)=>c.name(a.iso).localeCompare(c.name(b.iso),CXI.L()));
sel.replaceChildren(new Option(CX.t('Añadir…','Add…'),''),...opts.map(o=>new Option(c.name(o.iso),o.iso)));sel.value='';
sel.onchange=()=>{if(!sel.value)return;const p=CX.prm();dash.setParams({resaltar:p.resaltar.concat([sel.value])});};});
dash.draw('f_chips',box=>{const c=CX.ctx();box.replaceChildren();if(!c.ok)return;const list=[...c.H].filter(i=>c.P.has(i)).sort((a,b)=>c.name(a).localeCompare(c.name(b),CXI.L()));
if(!list.length){const s=document.createElement('span');s.className='cx-cap';s.textContent=CX.t('Ningún país resaltado.','No highlighted country.');box.appendChild(s);return;}
list.forEach(i=>{const b=document.createElement('button');b.type='button';b.className='cx-chip';const sw=document.createElement('span');sw.className='cx-sw';sw.style.background=c.col(i);sw.style.marginRight='0';b.appendChild(sw);b.appendChild(document.createTextNode(c.name(i)+' ×'));b.setAttribute('aria-label',CX.t('Quitar ','Remove ')+c.name(i));
b.onclick=()=>{const p=CX.prm();dash.setParams({resaltar:p.resaltar.filter(x=>x!==i)});};box.appendChild(b);});});
dash.draw('f_nres',el=>{const c=CX.ctx();const t=CX.t;if(!c.ok){el.textContent=t('Países resaltados','Highlighted countries');return;}const n=[...c.H].filter(i=>c.P.has(i)).length;el.textContent=n===0?t('Ningún país resaltado','No highlighted country'):(n===1?t('1 país resaltado','1 highlighted country'):n+t(' países resaltados',' highlighted countries'));});
