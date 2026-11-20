/* Capa mínima que reemplaza el entorno de tableros de Claude para publicar el sitio como página estática.
   Ofrece la misma interfaz que usan los scripts del sitio: dash.draw, dash.data, dash.calc, dash.params,
   dash.setParams, dash.onData, dash.setLink. Los datos se leen de docs/data/<id>.json ({rows, meta}). */
window.dash = (function () {
  const DATASETS = ['arquetipos', 'ciencia_cobertura', 'ciencia_flujos', 'ciencia_pruebas', 'ciencia_tareas', 'ciencia_tareas_resumen',
    'covariables', 'covariables_pais', 'especializacion_auc', 'ext_cor', 'ext_costo', 'ext_dev', 'ext_empleo_grupos', 'ext_empleo_mayor',
    'ext_empleo_pais', 'ext_ia', 'febrero', 'gini', 'involucramiento', 'involucramiento_mco', 'involucramiento_pais', 'lorenz', 'mundo',
    'openalex', 'paises', 'rca', 'subnacional', 'trayectoria', 'vacaciones'];
  const DEFAULTS = { categoria: 'Total', cx: 'pib_ppa', cy: 'aui', ingreso: '', mes: '2026-05', rca_pais: 'COL', region: '',
    resaltar: ['ARG', 'BOL', 'BRA', 'CHL', 'COL', 'CRI', 'DOM', 'ECU', 'GTM', 'HND', 'MEX', 'PAN', 'PER', 'PRY', 'SLV', 'URY'], version: 'todo' };
  const store = {};            // id -> {status, data, message}
  const calcs = {};            // id -> {inputs, fn}
  const draws = {};            // name -> fn
  const listeners = [];        // onData callbacks
  let params = Object.assign({}, DEFAULTS);
  const q = new URLSearchParams(location.search);
  if (q.get('lang') === 'en') params.lang = 'en';
  let started = false, pending = false;

  DATASETS.forEach(id => { store[id] = { status: 'loading', data: [] }; });
  function load(id) {
    return fetch('data/' + id + '.json').then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(j => { store[id] = { status: 'ok', data: Array.isArray(j) ? j : (j.rows || j.data || []), meta: j.meta || null }; })
      .catch(e => { store[id] = { status: 'error', data: [], message: String(e) }; })
      .then(schedule);
  }

  function data(id) {
    if (calcs[id]) {
      const c = calcs[id]; const ins = c.inputs.map(i => data(i));
      const bad = ins.find(r => r.status !== 'ok');
      if (bad) return { status: bad.status, data: null };
      try { return { status: 'ok', data: c.fn.apply(null, ins.map(r => r.data)) }; }
      catch (e) { return { status: 'error', data: null, message: String(e) }; }
    }
    return store[id] || { status: 'missing', data: [] };
  }

  function run(name, el) {
    try { draws[name](el); } catch (e) { console.error('[atlas] dibujo ' + name, e); }
  }
  function drawAll() {
    pending = false;
    listeners.forEach(fn => { try { fn(); } catch (e) { console.error('[atlas] onData', e); } });
    Object.keys(draws).forEach(name => document.querySelectorAll('[data-draw="' + name + '"]').forEach(el => run(name, el)));
  }
  function schedule() { if (!started || pending) return; pending = true; requestAnimationFrame(drawAll); }

  // Redibuja un gráfico cuando cambia su ancho (al mostrarse una vista oculta o al cambiar el tamaño de la ventana)
  const widths = new WeakMap();
  const ro = 'ResizeObserver' in window ? new ResizeObserver(entries => entries.forEach(e => {
    const el = e.target; const w = Math.round(e.contentRect.width); if (!w || widths.get(el) === w) return; widths.set(el, w);
    const name = el.getAttribute('data-draw'); if (draws[name]) run(name, el);
  })) : null;

  function start() {
    started = true;
    if (ro) document.querySelectorAll('.cx-chart[data-draw], .cx-tablewrap[data-draw]').forEach(el => ro.observe(el));
    drawAll();
    DATASETS.forEach(load);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => setTimeout(start, 0));
  else setTimeout(start, 0);

  return {
    draw(name, fn) { if (typeof fn === 'function') draws[name] = fn; else if (fn === undefined && draws[name]) document.querySelectorAll('[data-draw="' + name + '"]').forEach(el => run(name, el)); },
    data,
    calc(id, spec) { calcs[id] = spec; },
    params() { return params; },
    setParams(p) {
      params = Object.assign({}, params, p);
      Object.keys(p).forEach(k => { if (p[k] === null || p[k] === undefined) delete params[k]; });
      const u = new URL(location.href);
      if (params.lang === 'en') u.searchParams.set('lang', 'en'); else u.searchParams.delete('lang');
      history.replaceState(null, '', u);
      schedule();
    },
    resetParams() { params = Object.assign({}, DEFAULTS); schedule(); },
    onData(fn) { listeners.push(fn); if (started) { try { fn(); } catch (e) { console.error(e); } } },
    setLink(name) { history.replaceState(null, '', '#' + name); },
    refresh() {},
    get colors() { return window.CX ? CX.C : []; }
  };
})();
