// ===== TAB 5: Histórico Diario 2026 (Categoría / Subcategoría / Ítem) =====
const HIST = DATA5; // { dates: [...], levels: { categoria, subcategoria, item } }

const HIST_PALETTE = [
  '#0053e2', '#ea1100', '#2a8703', '#ffc220', '#7a3ffe', '#00a3a1',
  '#ff7a00', '#5b6675', '#c2185b', '#00838f', '#8d6e63', '#3949ab',
];

const histState = {
  level: 'categoria',
  selected: new Set(),
  metric: 'pesos',
  canal: 'total',
  catFilter: '',
  search: '',
  chart: null,
};

function histDefaultSelection(level) {
  const entities = HIST.levels[level].entities;
  if (level === 'categoria') return new Set(entities.map(e => e.key));
  return new Set(entities.slice(0, 5).map(e => e.key));
}

function histGetSeries(level, key, metric, canal) {
  const s = HIST.levels[level].series[key];
  const fis = s[`${metric}_fisico`];
  const com = s[`${metric}_com`];
  if (canal === 'fisico') return fis;
  if (canal === 'com') return com;
  return fis.map((v, i) => v + com[i]);
}

function histFmtValue(metric, v) {
  return metric === 'pesos' ? fmtPesos(v) : Math.round(v).toLocaleString('es-MX');
}

function histBuildCatFilterOptions() {
  const sel = document.getElementById('histCatFilter');
  const cats = HIST.levels.categoria.entities; // fuente de verdad de nombres de categoria
  sel.innerHTML = '<option value="">Todas</option>' +
    cats.map(c => `<option value="${c.key}">${c.label}</option>`).join('');
  sel.value = histState.catFilter;
}

function histEntitiesForPicker() {
  const level = histState.level;
  let entities = HIST.levels[level].entities;
  if (level !== 'categoria' && histState.catFilter) {
    entities = entities.filter(e => String(e.cat_nbr) === histState.catFilter);
  }
  if (level === 'item' && histState.search) {
    const q = histState.search.toUpperCase();
    entities = entities.filter(e => e.label.toUpperCase().includes(q) || e.key.includes(q));
  }
  return entities;
}

function histBuildPicker() {
  const box = document.getElementById('histPicker');
  const hint = document.getElementById('histPickerHint');
  const entities = histEntitiesForPicker();
  const level = histState.level;

  const hintText = {
    categoria: 'Categorías (todas seleccionadas por default):',
    subcategoria: 'Subcategorías (top 5 por venta seleccionadas):',
    item: `Ítems (${entities.length} coinciden con el filtro/búsqueda):`,
  };
  hint.textContent = hintText[level];

  // Para "item" solo se renderizan las primeras 200 coincidencias --
  // de sobra para cualquier busqueda razonable, evita pintar 1,160
  // checkboxes de un jalon si el usuario limpia el filtro.
  const renderList = level === 'item' ? entities.slice(0, 200) : entities;

  box.innerHTML = renderList.map(e => `
    <label class="flex items-center gap-2 text-xs py-1 cursor-pointer">
      <input type="checkbox" data-key="${e.key}" ${histState.selected.has(e.key) ? 'checked' : ''}>
      <span class="truncate">${e.label}</span>
    </label>`).join('') || '<p class="text-xs text-gray-400 p-2">Sin coincidencias.</p>';

  box.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', () => {
      if (cb.checked) histState.selected.add(cb.dataset.key);
      else histState.selected.delete(cb.dataset.key);
      histRenderChart();
    });
  });
}

function histRenderChart() {
  const level = histState.level;
  const metric = histState.metric;
  const canal = histState.canal;
  const entities = HIST.levels[level].entities;
  const byKey = Object.fromEntries(entities.map(e => [e.key, e]));

  const selectedKeys = [...histState.selected].filter(k => byKey[k]);

  const datasets = selectedKeys.map((key, i) => ({
    label: byKey[key].label,
    data: histGetSeries(level, key, metric, canal),
    borderColor: HIST_PALETTE[i % HIST_PALETTE.length],
    backgroundColor: HIST_PALETTE[i % HIST_PALETTE.length],
    fill: false,
    tension: 0.15,
    pointRadius: 0,
    borderWidth: 2,
  }));

  if (histState.chart) histState.chart.destroy();
  const ctx = document.getElementById('histChart').getContext('2d');
  histState.chart = new Chart(ctx, {
    type: 'line',
    data: { labels: HIST.dates, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: { ticks: { maxTicksLimit: 12, autoSkip: true } },
        y: { ticks: { callback: v => histFmtValue(metric, v) } },
      },
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } },
        tooltip: { callbacks: { label: ctx2 => `${ctx2.dataset.label}: ${histFmtValue(metric, ctx2.parsed.y)}` } },
      },
    },
  });

  // Tabla resumen: total del periodo por entidad seleccionada, orden desc.
  const totals = selectedKeys.map(key => ({
    label: byKey[key].label,
    total: sumOrNull(histGetSeries(level, key, metric, canal)) || 0,
  })).sort((a, b) => b.total - a.total);

  document.getElementById('histSummaryBody').innerHTML = totals.map(t => `
    <tr>
      <td class="px-3 py-1.5 text-left">${t.label}</td>
      <td class="px-3 py-1.5 text-right font-mono">${histFmtValue(metric, t.total)}</td>
    </tr>`).join('') || '<tr><td class="px-3 py-2 text-gray-400" colspan="2">Selecciona al menos una entidad.</td></tr>';
}

function histOnLevelChange(level) {
  histState.level = level;
  histState.selected = histDefaultSelection(level);
  histState.catFilter = '';
  histState.search = '';
  document.getElementById('histCatFilterWrap').style.display = level === 'categoria' ? 'none' : 'block';
  document.getElementById('histSearchWrap').style.display = level === 'item' ? 'block' : 'none';
  document.getElementById('histCatFilter').value = '';
  document.getElementById('histSearch').value = '';
  document.querySelectorAll('#histLevelBtns .tab-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.level === level);
  });
  histBuildPicker();
  histRenderChart();
}

document.querySelectorAll('#histLevelBtns .tab-btn').forEach(btn => {
  btn.addEventListener('click', () => histOnLevelChange(btn.dataset.level));
});
document.getElementById('histMetric').addEventListener('change', e => { histState.metric = e.target.value; histRenderChart(); });
document.getElementById('histCanal').addEventListener('change', e => { histState.canal = e.target.value; histRenderChart(); });
document.getElementById('histCatFilter').addEventListener('change', e => { histState.catFilter = e.target.value; histBuildPicker(); });
document.getElementById('histSearch').addEventListener('input', e => { histState.search = e.target.value.trim(); histBuildPicker(); });

histBuildCatFilterOptions();
histOnLevelChange('categoria');
