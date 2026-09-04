// ===== Historico Mensual 2025+2026 -- Equipos E-Catman (mini-app FastAPI + DuckDB) =====
const PALETTE = [
  '#0053e2', '#ea1100', '#2a8703', '#ffc220', '#7a3ffe', '#00a3a1',
  '#ff7a00', '#5b6675', '#c2185b', '#00838f',
];
const MONTH_LABELS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

const state = {
  team: '',
  level: 'categoria',
  view: 'grafica',  // 'grafica' | 'tabla' -- tabla de metricas mensuales (precio/costo/margen/CR/MoM/share)
  selected: new Set(),
  metric: 'pesos',
  canal: 'total',
  catFilter: '',
  subcatFilter: '',
  search: '',
  tiendaItem: null,
  tiendaItemData: null,  // {clubs, series} -- resultado del query en vivo para el item elegido
  tableEntity: null,  // key de la entidad elegida para la tabla de metricas
  chart: null,
  nMonths2026: 0,
};

function fmtMoney(v) {
  return '$' + Math.round(v).toLocaleString('es-MX');
}
function fmtVal(metric, v) {
  return metric === 'pesos' ? fmtMoney(v) : Math.round(v).toLocaleString('es-MX');
}

async function api(path, params) {
  const url = new URL(path, window.location.origin);
  Object.entries(params || {}).forEach(([k, v]) => { if (v !== null && v !== undefined && v !== '') url.searchParams.set(k, v); });
  const res = await fetch(url);
  return res.json();
}

function setActiveLevelBtn() {
  document.querySelectorAll('#levelBtns .btn').forEach(b => b.classList.toggle('active', b.dataset.level === state.level));
}

function setActiveViewBtn() {
  document.querySelectorAll('#viewBtns .btn').forEach(b => b.classList.toggle('active', b.dataset.view === state.view));
}

/** Dispatcher unico -- todo el codigo que antes llamaba renderChart() tras
 * un cambio de seleccion/filtro ahora llama esto, para que la vista Tabla
 * se mantenga sincronizada sin duplicar cada handler (DRY). */
async function renderCurrentView() {
  if (state.view === 'tabla') {
    await renderMetricsTable();
  } else {
    await renderChart();
  }
}

async function populateTeamSelect() {
  const teams = await api('/api/teams', {});
  const sel = document.getElementById('teamSelect');
  sel.innerHTML = teams.map(t => `<option value="${t.key}">${t.label} (${t.owner})</option>`).join('');
  state.team = teams[0].key;
}

async function populateCatFilter() {
  const cats = await api('/api/entities', { team: state.team, level: 'categoria' });
  const sel = document.getElementById('catFilter');
  sel.innerHTML = '<option value="">Todas</option>' + cats.map(c => `<option value="${c.key}">${c.label}</option>`).join('');
}

async function populateSubcatFilter() {
  const sel = document.getElementById('subcatFilter');
  if (!state.catFilter) { sel.innerHTML = '<option value="">Todas</option>'; return; }
  const subs = await api('/api/entities', { team: state.team, level: 'subcategoria', cat_filter: state.catFilter });
  sel.innerHTML = '<option value="">Todas</option>' + subs.map(s => `<option value="${s.key}">${s.label}</option>`).join('');
}

async function loadTiendaItemLive() {
  const hint = document.getElementById('pickerHint');
  const box = document.getElementById('picker');
  hint.textContent = `Consultando BigQuery en vivo para "${state.tiendaItem.label}"... (unos segundos, no es instantaneo)`;
  box.innerHTML = '<p class="text-xs text-gray-400 p-2">Cargando...</p>';
  const data = await api('/api/tienda_item', { item_nbr: state.tiendaItem.key });
  state.tiendaItemData = data;
  const clubs = data.clubs || [];
  hint.textContent = `2. Clubs que vendieron "${state.tiendaItem.label}" (top 5 preseleccionados):`;
  if (state.selected.size === 0) clubs.slice(0, 5).forEach(c => state.selected.add(c.key));
  box.innerHTML = clubs.map(c => `
    <label class="flex items-center gap-2 text-xs py-1 cursor-pointer">
      <input type="checkbox" data-key="${c.key}" ${state.selected.has(c.key) ? 'checked' : ''}>
      <span class="truncate">${c.label}</span>
    </label>`).join('') || '<p class="text-xs text-gray-400 p-2">Este item no vendio en ningun club.</p>';
  wireCheckboxes(box);
  renderCurrentView();
}

async function buildPicker() {
  const box = document.getElementById('picker');
  const hint = document.getElementById('pickerHint');
  const level = state.level;

  document.getElementById('itemPickForClubs').style.display = level === 'tienda_item' ? 'block' : 'none';
  document.getElementById('catFilterWrap').style.display = (level === 'subcategoria' || level === 'item') ? 'block' : 'none';
  document.getElementById('subcatFilterWrap').style.display = level === 'item' ? 'block' : 'none';
  document.getElementById('searchWrap').style.display = level === 'item' ? 'block' : 'none';

  if (level === 'tienda_item') {
    if (!state.tiendaItem) {
      hint.textContent = 'Elige un item arriba primero.';
      box.innerHTML = '';
      return;
    }
    await loadTiendaItemLive();
    return;
  }

  const entities = await api('/api/entities', {
    team: state.team, level, cat_filter: state.catFilter || null, subcat_filter: state.subcatFilter || null, search: state.search || null,
  });
  const hintText = {
    categoria: 'Categorías (todas seleccionadas por default):',
    subcategoria: 'Subcategorías (top 5 por venta seleccionadas):',
    item: `Ítems (${entities.length} encontrados, máx. 200):`,
  };
  hint.textContent = hintText[level];

  if (state.selected.size === 0 && level !== 'item') entities.forEach(e => state.selected.add(e.key));
  if (state.selected.size === 0 && level === 'item') entities.slice(0, 5).forEach(e => state.selected.add(e.key));

  box.innerHTML = entities.map(e => `
    <label class="flex items-center gap-2 text-xs py-1 cursor-pointer">
      <input type="checkbox" data-key="${e.key}" ${state.selected.has(e.key) ? 'checked' : ''}>
      <span class="truncate">${e.label}</span>
    </label>`).join('') || '<p class="text-xs text-gray-400 p-2">Sin coincidencias.</p>';
  wireCheckboxes(box);
}

function wireCheckboxes(box) {
  box.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', () => {
      if (cb.checked) state.selected.add(cb.dataset.key);
      else state.selected.delete(cb.dataset.key);
      renderCurrentView();
    });
  });
}

async function buildTiendaItemSearch() {
  const input = document.getElementById('tiendaItemSearch');
  const list = document.getElementById('tiendaItemList');
  async function refresh() {
    const items = await api('/api/entities', { team: state.team, level: 'item', search: input.value.trim() || null });
    list.innerHTML = items.slice(0, 50).map(it => `
      <div class="text-xs py-1 cursor-pointer hover:bg-gray-100 rounded px-1" data-key="${it.key}" data-label="${it.label.replace(/"/g, '&quot;')}">
        ${it.label}
      </div>`).join('');
    list.querySelectorAll('[data-key]').forEach(el => {
      el.addEventListener('click', () => {
        state.tiendaItem = { key: el.dataset.key, label: el.dataset.label };
        state.tiendaItemData = null;
        state.selected = new Set();
        buildPicker();
      });
    });
  }
  input.addEventListener('input', refresh);
  await refresh();
}

function getSeriesDataForCurrentLevel(keys, callback) {
  if (state.level === 'tienda_item') {
    const skey = `${state.metric}|${state.canal}`;
    const series = (state.tiendaItemData && state.tiendaItemData.series[skey]) || {};
    callback(series);
    return;
  }
  api('/api/series', { team: state.team, level: state.level, keys: keys.join(','), metric: state.metric, canal: state.canal }).then(callback);
}

async function renderChart() {
  const keys = [...state.selected];
  if (!keys.length) { renderChartWithData({}); return; }
  getSeriesDataForCurrentLevel(keys, renderChartWithData);
}

function renderChartWithData(data) {
  const keys = [...state.selected];
  const datasets = [];
  let i = 0;
  for (const key of keys) {
    const d = data[key];
    if (!d) continue;
    const color = PALETTE[i % PALETTE.length];
    datasets.push({ label: `${d.label} (2025)`, data: d.y2025, borderColor: color, backgroundColor: color, borderWidth: 1.5, borderDash: [2, 2], pointRadius: 0, tension: 0.2, yAxisID: 'y' });
    datasets.push({ label: `${d.label} (2026 YTD)`, data: d.y2026, borderColor: color, backgroundColor: color, borderWidth: 3, pointRadius: 2, tension: 0.2, yAxisID: 'y' });
    datasets.push({ label: `${d.label} (% YoY mes)`, data: d.growth, borderColor: color, backgroundColor: color, borderWidth: 1, borderDash: [4, 3], pointRadius: 0, tension: 0.15, yAxisID: 'y1', hidden: true });
    i++;
  }

  if (state.chart) state.chart.destroy();
  const ctx = document.getElementById('chart').getContext('2d');
  state.chart = new Chart(ctx, {
    type: 'line',
    data: { labels: MONTH_LABELS, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: {},
        y: { position: 'left', ticks: { callback: v => fmtVal(state.metric, v) }, title: { display: true, text: state.metric === 'pesos' ? 'Pesos $' : 'Piezas' } },
        y1: { position: 'right', grid: { drawOnChartArea: false }, ticks: { callback: v => v.toFixed(0) + '%' }, title: { display: true, text: '% crec. YoY por mes (click leyenda para ver)' } },
      },
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } },
        tooltip: { callbacks: { label: c => c.dataset.yAxisID === 'y1' ? `${c.dataset.label}: ${c.parsed.y === null ? 's/d' : c.parsed.y.toFixed(1) + '%'}` : `${c.dataset.label}: ${c.parsed.y === null ? 's/d' : fmtVal(state.metric, c.parsed.y)}` } },
      },
    },
  });

  const rows = keys.map(k => data[k]).filter(Boolean).sort((a, b) => b.total_2026 - a.total_2026);
  document.getElementById('summaryBody').innerHTML = rows.map(r => {
    const g = r.growth_pct;
    const gCls = g === null ? '' : (g >= 0 ? 'growth-pos' : 'growth-neg');
    const gTxt = g === null ? 'sin base 2025' : `${g >= 0 ? '+' : ''}${g.toFixed(1)}%`;
    return `<tr>
      <td class="px-3 py-1.5 text-left">${r.label}</td>
      <td class="px-3 py-1.5 text-right font-mono text-gray-500">${fmtVal(state.metric, r.total_2025)}</td>
      <td class="px-3 py-1.5 text-right font-mono">${fmtVal(state.metric, r.total_2026)}</td>
      <td class="px-3 py-1.5 text-right ${gCls}">${gTxt}</td>
    </tr>`;
  }).join('') || '<tr><td class="px-3 py-2 text-gray-400" colspan="4">Selecciona al menos una entidad.</td></tr>';
}

async function onTeamChange(team) {
  state.team = team;
  state.selected = new Set();
  state.catFilter = '';
  state.subcatFilter = '';
  state.search = '';
  state.tiendaItem = null;
  state.tiendaItemData = null;
  document.getElementById('catFilter').value = '';
  document.getElementById('subcatFilter').value = '';
  document.getElementById('search').value = '';
  await populateCatFilter();
  await buildTiendaItemSearch();
  await buildPicker();
  renderCurrentView();
}

async function onLevelChange(level) {
  state.level = level;
  state.selected = new Set();
  state.catFilter = '';
  state.subcatFilter = '';
  state.search = '';
  state.tiendaItem = null;
  state.tiendaItemData = null;
  document.getElementById('catFilter').value = '';
  document.getElementById('subcatFilter').value = '';
  document.getElementById('search').value = '';
  document.getElementById('tiendaItemSearch').value = '';
  setActiveLevelBtn();
  await buildPicker();
  renderCurrentView();
}

function onViewChange(view) {
  state.view = view;
  setActiveViewBtn();
  document.getElementById('chartWrap').style.display = view === 'grafica' ? 'block' : 'none';
  document.getElementById('tableWrap').style.display = view === 'tabla' ? 'block' : 'none';
  renderCurrentView();
}

// ===== Tabla de Datos: precio/costo/margen/CR YoY/MoM/share .com-piso =====
function fmtPct(v) {
  if (v === null || v === undefined) return '<span class="text-gray-300">s/d</span>';
  const cls = v >= 0 ? 'growth-pos' : 'growth-neg';
  return `<span class="${cls}">${v >= 0 ? '+' : ''}${v.toFixed(1)}%</span>`;
}
function fmtMoneyOrDash(v) {
  return (v === null || v === undefined) ? '<span class="text-gray-300">s/d</span>' : fmtMoney(v);
}

function populateTableEntitySelect(entityLabels) {
  const sel = document.getElementById('tableEntitySelect');
  const keys = [...state.selected];
  if (!keys.length) { sel.innerHTML = '<option value="">Selecciona al menos una entidad</option>'; return; }
  if (!state.tableEntity || !keys.includes(state.tableEntity)) state.tableEntity = keys[0];
  sel.innerHTML = keys.map(k => `<option value="${k}" ${k === state.tableEntity ? 'selected' : ''}>${(entityLabels && entityLabels[k]) || k}</option>`).join('');
}

async function renderMetricsTable() {
  const keys = [...state.selected];
  const tbody = document.getElementById('metricsTableBody');
  if (state.level === 'tienda_item') {
    populateTableEntitySelect({});
    tbody.innerHTML = '<tr><td class="px-2 py-2 text-gray-400" colspan="13">La tabla de metricas no aplica a Tienda-Item (no hay costo/precio a ese grano) -- elige otro nivel.</td></tr>';
    return;
  }
  if (!keys.length) {
    populateTableEntitySelect({});
    tbody.innerHTML = '<tr><td class="px-2 py-2 text-gray-400" colspan="13">Selecciona al menos una entidad.</td></tr>';
    return;
  }
  const data = await api('/api/metrics_table', { team: state.team, level: state.level, keys: keys.join(',') });
  const labels = {};
  Object.entries(data).forEach(([k, v]) => { labels[k] = v.label; });
  populateTableEntitySelect(labels);

  const entity = data[state.tableEntity];
  if (!entity) { tbody.innerHTML = '<tr><td class="px-2 py-2 text-gray-400" colspan="13">Sin datos para esta entidad.</td></tr>'; return; }

  tbody.innerHTML = entity.rows.map(r => `
    <tr class="border-t">
      <td class="px-2 py-1 font-medium">${r.mes_label}</td>
      <td class="px-2 py-1 text-right font-mono text-gray-500">${fmtMoney(r.pesos_ly)}</td>
      <td class="px-2 py-1 text-right font-mono">${fmtMoneyOrDash(r.pesos_ty)}</td>
      <td class="px-2 py-1 text-right font-mono text-gray-500">${Math.round(r.pzas_ly).toLocaleString('es-MX')}</td>
      <td class="px-2 py-1 text-right font-mono">${r.pzas_ty === null ? '<span class="text-gray-300">s/d</span>' : Math.round(r.pzas_ty).toLocaleString('es-MX')}</td>
      <td class="px-2 py-1 text-right">${fmtPct(r.cr_yoy)}</td>
      <td class="px-2 py-1 text-right">${fmtPct(r.mom_ty !== null && r.mom_ty !== undefined ? r.mom_ty : r.mom_ly)}</td>
      <td class="px-2 py-1 text-right font-mono">${fmtMoneyOrDash(r.utilidad_ty)}</td>
      <td class="px-2 py-1 text-right font-mono">${fmtMoneyOrDash(r.margen_ty)}</td>
      <td class="px-2 py-1 text-right font-mono text-gray-500">${fmtMoneyOrDash(r.precio_prom_ly)}</td>
      <td class="px-2 py-1 text-right font-mono">${fmtMoneyOrDash(r.precio_prom_ty)}</td>
      <td class="px-2 py-1 text-right font-mono text-gray-400">${fmtMoneyOrDash(r.costo_prom)}</td>
      <td class="px-2 py-1 text-right">${r.share_com_ty === null ? '<span class="text-gray-300">s/d</span>' : r.share_com_ty.toFixed(0) + '%'}</td>
    </tr>`).join('') + `
    <tr class="border-t-2 font-semibold bg-gray-50">
      <td class="px-2 py-1">YTD 2026</td>
      <td class="px-2 py-1 text-right font-mono text-gray-500">${fmtMoney(entity.total_2025.pesos)} (Total LY)</td>
      <td class="px-2 py-1 text-right font-mono">${fmtMoney(entity.ytd_2026.pesos)}</td>
      <td class="px-2 py-1 text-right font-mono text-gray-500">${Math.round(entity.total_2025.pzas).toLocaleString('es-MX')}</td>
      <td class="px-2 py-1 text-right font-mono">${Math.round(entity.ytd_2026.pzas).toLocaleString('es-MX')}</td>
      <td class="px-2 py-1 text-right">${fmtPct(entity.ytd_2026.cr_yoy)}</td>
      <td class="px-2 py-1 text-right">-</td>
      <td class="px-2 py-1 text-right font-mono">${fmtMoneyOrDash(entity.ytd_2026.utilidad)}</td>
      <td class="px-2 py-1 text-right font-mono">${fmtMoneyOrDash(entity.ytd_2026.margen)}</td>
      <td class="px-2 py-1 text-right font-mono text-gray-500">${fmtMoneyOrDash(entity.total_2025.precio_prom)}</td>
      <td class="px-2 py-1 text-right font-mono">${fmtMoneyOrDash(entity.ytd_2026.precio_prom)}</td>
      <td class="px-2 py-1 text-right font-mono text-gray-400">${fmtMoneyOrDash(entity.ytd_2026.costo_prom)}</td>
      <td class="px-2 py-1 text-right">${entity.ytd_2026.share_com === null ? '-' : entity.ytd_2026.share_com.toFixed(0) + '%'}</td>
    </tr>`;
}

document.getElementById('teamSelect').addEventListener('change', e => onTeamChange(e.target.value));
document.querySelectorAll('#levelBtns .btn').forEach(btn => btn.addEventListener('click', () => onLevelChange(btn.dataset.level)));
document.querySelectorAll('#viewBtns .btn').forEach(btn => btn.addEventListener('click', () => onViewChange(btn.dataset.view)));
document.getElementById('tableEntitySelect').addEventListener('change', e => { state.tableEntity = e.target.value; renderMetricsTable(); });
document.getElementById('metric').addEventListener('change', e => { state.metric = e.target.value; renderCurrentView(); });
document.getElementById('canal').addEventListener('change', e => { state.canal = e.target.value; renderCurrentView(); });
document.getElementById('catFilter').addEventListener('change', async e => { state.catFilter = e.target.value; state.subcatFilter = ''; state.selected = new Set(); await populateSubcatFilter(); await buildPicker(); renderCurrentView(); });
document.getElementById('subcatFilter').addEventListener('change', async e => { state.subcatFilter = e.target.value; state.selected = new Set(); await buildPicker(); renderCurrentView(); });
document.getElementById('search').addEventListener('input', async e => { state.search = e.target.value.trim(); await buildPicker(); renderCurrentView(); });

(async function init() {
  document.getElementById('pickerHint').textContent = 'Cargando...';
  const meta = await api('/api/meta', {});
  state.nMonths2026 = meta.n_months_2026;
  await populateTeamSelect();
  await populateCatFilter();
  await buildTiendaItemSearch();
  await buildPicker();
  await renderCurrentView();
})();
