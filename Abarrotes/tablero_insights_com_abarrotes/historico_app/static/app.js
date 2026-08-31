// ===== Historico Diario 2026 vs 2025 -- Mini-app FastAPI + DuckDB =====
const PALETTE = [
  '#0053e2', '#ea1100', '#2a8703', '#ffc220', '#7a3ffe', '#00a3a1',
  '#ff7a00', '#5b6675', '#c2185b', '#00838f',
];
const TY_START = new Date('2026-01-01T00:00:00');

const state = {
  level: 'categoria',
  selected: new Set(),
  metric: 'pesos',
  canal: 'total',
  catFilter: '',
  subcatFilter: '',
  search: '',
  tiendaItem: null,   // {key, label} del item elegido para el nivel Tienda-Item
  chart: null,
  nDays: 0,
};

function dayLabel(i) {
  const d = new Date(TY_START);
  d.setDate(d.getDate() + i);
  return d.toLocaleDateString('es-MX', { day: '2-digit', month: 'short' });
}

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

async function populateCatFilter() {
  const cats = await api('/api/entities', { level: 'categoria' });
  const sel = document.getElementById('catFilter');
  sel.innerHTML = '<option value="">Todas</option>' + cats.map(c => `<option value="${c.key}">${c.label}</option>`).join('');
}

async function populateSubcatFilter() {
  const sel = document.getElementById('subcatFilter');
  if (!state.catFilter) { sel.innerHTML = '<option value="">Todas</option>'; return; }
  const subs = await api('/api/entities', { level: 'subcategoria', cat_filter: state.catFilter });
  sel.innerHTML = '<option value="">Todas</option>' + subs.map(s => `<option value="${s.key}">${s.label}</option>`).join('');
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
      hint.textContent = 'Elige un ítem arriba primero.';
      box.innerHTML = '';
      return;
    }
    hint.textContent = `2. Clubs que vendieron "${state.tiendaItem.label}" (top 5 preseleccionados):`;
    const clubs = await api('/api/entities', { level: 'tienda_item', item_filter: state.tiendaItem.key });
    if (state.selected.size === 0) clubs.slice(0, 5).forEach(c => state.selected.add(`${state.tiendaItem.key}|${c.key}`));
    box.innerHTML = clubs.map(c => {
      const k = `${state.tiendaItem.key}|${c.key}`;
      return `<label class="flex items-center gap-2 text-xs py-1 cursor-pointer">
        <input type="checkbox" data-key="${k}" ${state.selected.has(k) ? 'checked' : ''}>
        <span class="truncate">${c.label}</span></label>`;
    }).join('') || '<p class="text-xs text-gray-400 p-2">Este ítem no vendió en ningún club en 2026.</p>';
    wireCheckboxes(box);
    return;
  }

  const entities = await api('/api/entities', {
    level, cat_filter: state.catFilter || null, subcat_filter: state.subcatFilter || null, search: state.search || null,
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
      renderChart();
    });
  });
}

async function buildTiendaItemSearch() {
  const input = document.getElementById('tiendaItemSearch');
  const list = document.getElementById('tiendaItemList');
  async function refresh() {
    const items = await api('/api/entities', { level: 'item', search: input.value.trim() || null });
    list.innerHTML = items.slice(0, 50).map(it => `
      <div class="text-xs py-1 cursor-pointer hover:bg-gray-100 rounded px-1" data-key="${it.key}" data-label="${it.label.replace(/"/g, '&quot;')}">
        ${it.label}
      </div>`).join('');
    list.querySelectorAll('[data-key]').forEach(el => {
      el.addEventListener('click', () => {
        state.tiendaItem = { key: el.dataset.key, label: el.dataset.label };
        state.selected = new Set();
        buildPicker().then(renderChart);
      });
    });
  }
  input.addEventListener('input', refresh);
  await refresh();
}

async function renderChart() {
  const level = state.level;
  const keys = [...state.selected];
  const data = keys.length ? await api('/api/series', { level, keys: keys.join(','), metric: state.metric, canal: state.canal }) : {};

  const labels = Array.from({ length: state.nDays }, (_, i) => dayLabel(i));
  const datasets = [];
  let i = 0;
  for (const key of keys) {
    const d = data[key];
    if (!d) continue;
    const color = PALETTE[i % PALETTE.length];
    datasets.push({ label: `${d.label} (venta)`, data: d.ty, borderColor: color, backgroundColor: color, borderWidth: 2, pointRadius: 0, tension: 0.15, yAxisID: 'y' });
    datasets.push({ label: `${d.label} (crec. % acum.)`, data: d.growth, borderColor: color, backgroundColor: color, borderWidth: 1.5, borderDash: [4, 3], pointRadius: 0, tension: 0.15, yAxisID: 'y1' });
    i++;
  }

  if (state.chart) state.chart.destroy();
  const ctx = document.getElementById('chart').getContext('2d');
  state.chart = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: { ticks: { maxTicksLimit: 12, autoSkip: true } },
        y: { position: 'left', ticks: { callback: v => fmtVal(state.metric, v) }, title: { display: true, text: state.metric === 'pesos' ? 'Pesos $' : 'Piezas' } },
        y1: { position: 'right', grid: { drawOnChartArea: false }, ticks: { callback: v => v.toFixed(0) + '%' }, title: { display: true, text: '% crec. acum. vs 2025' } },
      },
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } },
        tooltip: { callbacks: { label: c => c.dataset.yAxisID === 'y1' ? `${c.dataset.label}: ${c.parsed.y === null ? 's/d' : c.parsed.y.toFixed(1) + '%'}` : `${c.dataset.label}: ${fmtVal(state.metric, c.parsed.y)}` } },
      },
    },
  });

  const rows = keys.map(k => data[k]).filter(Boolean).sort((a, b) => b.total_ty - a.total_ty);
  document.getElementById('summaryBody').innerHTML = rows.map(r => {
    const g = r.growth_pct;
    const gCls = g === null ? '' : (g >= 0 ? 'growth-pos' : 'growth-neg');
    const gTxt = g === null ? 'sin base LY' : `${g >= 0 ? '+' : ''}${g.toFixed(1)}%`;
    return `<tr>
      <td class="px-3 py-1.5 text-left">${r.label}</td>
      <td class="px-3 py-1.5 text-right font-mono">${fmtVal(state.metric, r.total_ty)}</td>
      <td class="px-3 py-1.5 text-right ${gCls}">${gTxt}</td>
    </tr>`;
  }).join('') || '<tr><td class="px-3 py-2 text-gray-400" colspan="3">Selecciona al menos una entidad.</td></tr>';
}

async function onLevelChange(level) {
  state.level = level;
  state.selected = new Set();
  state.catFilter = '';
  state.subcatFilter = '';
  state.search = '';
  state.tiendaItem = null;
  document.getElementById('catFilter').value = '';
  document.getElementById('subcatFilter').value = '';
  document.getElementById('search').value = '';
  document.getElementById('tiendaItemSearch').value = '';
  setActiveLevelBtn();
  await buildPicker();
  renderChart();
}

document.querySelectorAll('#levelBtns .btn').forEach(btn => btn.addEventListener('click', () => onLevelChange(btn.dataset.level)));
document.getElementById('metric').addEventListener('change', e => { state.metric = e.target.value; renderChart(); });
document.getElementById('canal').addEventListener('change', e => { state.canal = e.target.value; renderChart(); });
document.getElementById('catFilter').addEventListener('change', async e => { state.catFilter = e.target.value; state.subcatFilter = ''; state.selected = new Set(); await populateSubcatFilter(); await buildPicker(); renderChart(); });
document.getElementById('subcatFilter').addEventListener('change', async e => { state.subcatFilter = e.target.value; state.selected = new Set(); await buildPicker(); renderChart(); });
document.getElementById('search').addEventListener('input', async e => { state.search = e.target.value.trim(); await buildPicker(); renderChart(); });

(async function init() {
  document.getElementById('pickerHint').textContent = 'Cargando...';
  const meta = await api('/api/meta', {});
  state.nDays = meta.n_days;
  await populateCatFilter();
  await buildTiendaItemSearch();
  await buildPicker();
  await renderChart();
})();
