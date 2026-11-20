(function(){
const root=document.querySelector('.cx');const reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
document.querySelectorAll('[data-goto]').forEach(b=>b.addEventListener('click',()=>{const v=b.dataset.goto,t=b.dataset.target;const nb=document.querySelector(".cx-nav button[data-tab='"+v+"']");if(nb)nb.click();
setTimeout(()=>{const el=document.getElementById(t||v)||document.getElementById('navegacion');if(el)el.scrollIntoView({behavior:reduce?'auto':'smooth',block:'start'});},80);}));
if(root&&'IntersectionObserver' in window&&!reduce){root.classList.add('cx-js');
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('cx-in');io.unobserve(e.target);}}),{rootMargin:'0px 0px -12% 0px',threshold:0.12});
document.querySelectorAll('.cx-sec .cx-card, .cx-sec .cx-shead').forEach(el=>{el.classList.add('cx-rv');io.observe(el);});}
})();
