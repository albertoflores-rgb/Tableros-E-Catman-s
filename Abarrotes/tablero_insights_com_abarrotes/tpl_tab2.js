// ===== TAB 2: Explorador BQ =====
const EXP_LABELS = {
  Item_Nbr: 'Item #', Item_Desc_1: 'Descripción', Cat_Desc: 'Categoría',
  Sub_Cat_Desc: 'Subcategoría', Proveedor: 'Proveedor', Tipo: 'Tipo',
  Status: 'Status', Semaforo_OH: 'Inventario', En_Parrilla: 'En Parrilla',
  Promo_Vigente: 'Promo Vigente', Top_L7D_Cat: 'Top L7D (Cat)',
  Inv_Pzas_Total: 'Inv. Pzas Total', Inv_MXN_Total: 'Inv. Valor $',
  Club_con_Inventario: 'Tiendas con Inv.', Precio_Venta: 'Precio',
  Piso_Pzas_YTD: 'Piso YTD (pzas)', Piso_Pesos_YTD: 'Piso YTD $',
  Com_Pzas_YTD: '.com YTD (pzas)', Com_Pesos_YTD: '.com YTD $',
  Crecimiento_Piso_Pesos_YTD: 'Crec Piso YTD', Crecimiento_Com_Pesos_YTD: 'Crec .com YTD',
  Share_Com_YTD: 'Share .com YTD',
  Piso_Pzas_MTD: 'Piso MTD (pzas)', Piso_Pesos_MTD: 'Piso MTD $',
  Com_Pzas_MTD: '.com MTD (pzas)', Com_Pesos_MTD: '.com MTD $',
  Crecimiento_Piso_Pesos_MTD: 'Crec Piso MTD', Crecimiento_Com_Pesos_MTD: 'Crec .com MTD',
  Share_Com_MTD: 'Share .com MTD',
  Piso_Pzas_L7D: 'Piso L7D (pzas)', Piso_Pesos_L7D: 'Piso L7D $',
  Com_Pzas_L7D: '.com L7D (pzas)', Com_Pesos_L7D: '.com L7D $',
  Crecimiento_Piso_Pesos_L7D: 'Crec Piso L7D', Crecimiento_Com_Pesos_L7D: 'Crec .com L7D',
  Share_Com_L7D: 'Share .com L7D',
};
const EXP_PCT_COLS = new Set([
  'Crecimiento_Piso_Pesos_YTD', 'Crecimiento_Com_Pesos_YTD',
  'Crecimiento_Piso_Pesos_MTD', 'Crecimiento_Com_Pesos_MTD',
  'Crecimiento_Piso_Pesos_L7D', 'Crecimiento_Com_Pesos_L7D',
]);
const EXP_SHARE_COLS = new Set(['Share_Com_YTD', 'Share_Com_MTD', 'Share_Com_L7D']);
const EXP_MONEY_COLS = new Set([
  'Precio_Venta', 'Inv_MXN_Total',
  'Piso_Pesos_YTD', 'Com_Pesos_YTD',
  'Piso_Pesos_MTD', 'Com_Pesos_MTD',
  'Piso_Pesos_L7D', 'Com_Pesos_L7D',
]);
const EXP_BOOL_COLS = new Set(['En_Parrilla', 'Promo_Vigente']);

// Descriptor de como totalizar cada columna en la fila de totales (refleja
// SIEMPRE el conjunto filtrado completo, no solo la pagina visible).
const EXP_TOTALS_TYPE = {
  Inv_Pzas_Total: 'sum_pzas', Inv_MXN_Total: 'sum_money',
  Club_con_Inventario: 'avg_int', Precio_Venta: 'avg_money',
  Piso_Pzas_YTD: 'sum_pzas', Piso_Pesos_YTD: 'sum_money',
  Com_Pzas_YTD: 'sum_pzas', Com_Pesos_YTD: 'sum_money',
  Crecimiento_Piso_Pesos_YTD: 'growth_exact:Piso_Pesos_YTD:Piso_Pesos_YTDLY',
  Crecimiento_Com_Pesos_YTD: 'growth_exact:Com_Pesos_YTD:Com_Pesos_YTDLY',
  Share_Com_YTD: 'share:Com_Pesos_YTD:Piso_Pesos_YTD',
  Piso_Pzas_MTD: 'sum_pzas', Piso_Pesos_MTD: 'sum_money',
  Com_Pzas_MTD: 'sum_pzas', Com_Pesos_MTD: 'sum_money',
  Crecimiento_Piso_Pesos_MTD: 'growth_exact:Piso_Pesos_MTD:Piso_Pesos_MTDLY',
  Crecimiento_Com_Pesos_MTD: 'growth_exact:Com_Pesos_MTD:Com_Pesos_MTDLY',
  Share_Com_MTD: 'share:Com_Pesos_MTD:Piso_Pesos_MTD',
  Piso_Pzas_L7D: 'sum_pzas', Piso_Pesos_L7D: 'sum_money',
  Com_Pzas_L7D: 'sum_pzas', Com_Pesos_L7D: 'sum_money',
  Crecimiento_Piso_Pesos_L7D: 'growth_exact:Piso_Pesos_L7D:Piso_Pesos_L7DLY',
  Crecimiento_Com_Pesos_L7D: 'growth_exact:Com_Pesos_L7D:Com_Pesos_L7DLY',
  Share_Com_L7D: 'share:Com_Pesos_L7D:Piso_Pesos_L7D',
  En_Parrilla: 'count_bool', Promo_Vigente: 'count_bool',
};

function expBuildTotals(rows) {
  const idx = expColIdx;
  const col = c => rows.map(r => r[idx[c]]);
  const html = visibleCols.map((c, i) => {
    if (i === 0) return `<td class="px-3 py-1.5 text-left">TOTAL (${rows.length.toLocaleString('es-MX')} items)</td>`;
    const type = EXP_TOTALS_TYPE[c];
    if (!type) return '<td class="px-3 py-1.5">-</td>';
    if (type === 'sum_pzas') {
      const v = sumOrNull(col(c));
      return `<td class="px-3 py-1.5 text-right">${v == null ? '-' : Math.round(v).toLocaleString('es-MX')}</td>`;
    }
    if (type === 'sum_money') {
      return `<td class="px-3 py-1.5 text-right">${fmtPesos(sumOrNull(col(c)))}</td>`;
    }
    if (type === 'avg_money') {
      return `<td class="px-3 py-1.5 text-right">${fmtPesos(avgOrNull(col(c)))} <span class="font-normal text-xs">(prom)</span></td>`;
    }
    if (type === 'avg_int') {
      const v = avgOrNull(col(c));
      return `<td class="px-3 py-1.5 text-right">${v == null ? '-' : v.toFixed(1)} <span class="font-normal text-xs">(prom)</span></td>`;
    }
    if (type === 'count_bool') {
      const vals = col(c);
      const n = vals.filter(v => v === true).length;
      return `<td class="px-3 py-1.5 text-right">${n}/${vals.length}</td>`;
    }
    if (type.startsWith('growth_exact:')) {
      const [, tyCol, lyCol] = type.split(':');
      const g = exactGrowth(col(tyCol), col(lyCol));
      return `<td class="px-3 py-1.5 text-right">${badge(g)}</td>`;
    }
    if (type.startsWith('share:')) {
      const [, comCol, pisoCol] = type.split(':');
      const sumCom = sumOrNull(col(comCol)) || 0;
      const sumPiso = sumOrNull(col(pisoCol)) || 0;
      const share = (sumCom + sumPiso) > 0 ? sumCom / (sumCom + sumPiso) : null;
      return `<td class="px-3 py-1.5 text-right"><span class="badge-flat">${fmtPct(share).replace('+','')}</span></td>`;
    }
    return '<td class="px-3 py-1.5">-</td>';
  }).join('');
  document.getElementById('explorerFoot').innerHTML = `<tr class="totals-row">${html}</tr>`;
}

const expCols = DATA2.columns;
const expColIdx = Object.fromEntries(expCols.map((c, i) => [c, i]));
const HIDDEN_FIELDS = new Set(DATA2.hidden_fields || []);
const visibleCols = expCols.filter(c => !HIDDEN_FIELDS.has(c));

const expState = {
  filters: {},
  search: '',
  sortCol: 'Com_Pesos_MTD',
  sortDir: 'desc',
  page: 1,
  pageSize: 50,
};

function expFormatCell(col, val) {
  if (val == null) return '<span class="text-gray-300">-</span>';
  if (EXP_BOOL_COLS.has(col)) return val ? '<span class="chip chip-green">Sí</span>' : '<span class="chip chip-gray">No</span>';
  if (EXP_PCT_COLS.has(col)) return badge(val);
  if (EXP_SHARE_COLS.has(col)) return `<span class="badge-flat">${fmtPct(val).replace('+','')}</span>`;
  if (EXP_MONEY_COLS.has(col)) return fmtPesos(val);
  if (col === 'Semaforo_OH') return `<span class="chip ${semColor(val)}">${val}</span>`;
  if (typeof val === 'number') return val.toLocaleString('es-MX');
  return val;
}

function expBuildFilters() {
  const box = document.getElementById('explorerFilters');
  let html = '';
  DATA2.filter_fields.forEach(f => {
    const opts = DATA2.filter_options[f] || [];
    html += `<div><label class="text-xs text-gray-500 block mb-0.5">${EXP_LABELS[f] || f}</label>
      <select class="filter-select" data-field="${f}" onchange="expOnFilterChange(this)">
        <option value="">Todos</option>
        ${opts.map(o => `<option value="${o}">${o}</option>`).join('')}
      </select></div>`;
  });
  html += `<div><label class="text-xs text-gray-500 block mb-0.5">Buscar (descripción / item#)</label>
    <input type="text" class="pill-input" id="explorerSearch" placeholder="ej. NESCAFE, 214464..." oninput="expOnSearch(this)"></div>`;
  box.innerHTML = html;
}

function expOnFilterChange(sel) {
  const field = sel.dataset.field;
  if (sel.value === '') delete expState.filters[field];
  else expState.filters[field] = sel.value;
  expState.page = 1;
  expRender();
}

function expOnSearch(input) {
  expState.search = input.value.trim().toUpperCase();
  expState.page = 1;
  expRender();
}

function expBuildHead() {
  const head = document.getElementById('explorerHead');
  head.innerHTML = '<tr>' + visibleCols.map(c => {
    const isNumeric = DATA2.numeric_fields.includes(c);
    const arrow = expState.sortCol === c ? (expState.sortDir === 'asc' ? ' \u25b2' : ' \u25bc') : '';
    const cls = isNumeric ? 'sortable text-right' : 'sortable text-left';
    return `<th class="px-3 py-2 ${cls}" onclick="expOnSort('${c}')">${EXP_LABELS[c] || c}${arrow}</th>`;
  }).join('') + '</tr>';
}

function expOnSort(col) {
  if (expState.sortCol === col) {
    expState.sortDir = expState.sortDir === 'desc' ? 'asc' : 'desc';
  } else {
    expState.sortCol = col;
    expState.sortDir = DATA2.numeric_fields.includes(col) ? 'desc' : 'asc';
  }
  expRender();
}

function expFilteredRows() {
  const idx = expColIdx;
  let rows = DATA2.rows;
  for (const [field, val] of Object.entries(expState.filters)) {
    const i = idx[field];
    rows = rows.filter(r => String(r[i]) === val);
  }
  if (expState.search) {
    const di = idx['Item_Desc_1'], ni = idx['Item_Nbr'];
    rows = rows.filter(r => String(r[di]).toUpperCase().includes(expState.search) || String(r[ni]).includes(expState.search));
  }
  return rows;
}

function expSortRows(rows) {
  const i = expColIdx[expState.sortCol];
  const dir = expState.sortDir === 'asc' ? 1 : -1;
  return [...rows].sort((a, b) => {
    let av = a[i], bv = b[i];
    if (av == null) av = -Infinity;
    if (bv == null) bv = -Infinity;
    if (typeof av === 'string') return av.localeCompare(bv) * dir;
    return (av - bv) * dir;
  });
}

function expRender() {
  expBuildHead();
  let rows = expFilteredRows();
  document.getElementById('explorerCount').textContent = `${rows.length.toLocaleString('es-MX')} items encontrados (de ${DATA2.rows.length.toLocaleString('es-MX')} totales)`;
  rows = expSortRows(rows);

  const totalPages = Math.max(1, Math.ceil(rows.length / expState.pageSize));
  if (expState.page > totalPages) expState.page = totalPages;
  const startIdx = (expState.page - 1) * expState.pageSize;
  const pageRows = rows.slice(startIdx, startIdx + expState.pageSize);

  document.getElementById('explorerBody').innerHTML = pageRows.map(r => '<tr>' +
    visibleCols.map((c, i) => {
      const isNumeric = DATA2.numeric_fields.includes(c);
      return `<td class="px-3 py-1.5 ${isNumeric ? 'text-right font-mono' : 'text-left'}">${expFormatCell(c, r[expColIdx[c]])}</td>`;
    }).join('') + '</tr>').join('');

  expBuildTotals(rows);

  document.getElementById('explorerPageInfo').textContent = `Página ${expState.page} de ${totalPages}`;
  document.getElementById('explorerPrev').disabled = expState.page <= 1;
  document.getElementById('explorerNext').disabled = expState.page >= totalPages;
}

document.getElementById('explorerPageSize').addEventListener('change', e => {
  expState.pageSize = parseInt(e.target.value, 10);
  expState.page = 1;
  expRender();
});
document.getElementById('explorerPrev').addEventListener('click', () => { expState.page--; expRender(); });
document.getElementById('explorerNext').addEventListener('click', () => { expState.page++; expRender(); });
document.getElementById('explorerReset').addEventListener('click', () => {
  expState.filters = {};
  expState.search = '';
  expState.page = 1;
  expBuildFilters();
  document.getElementById('explorerSearch').value = '';
  expRender();
});

expBuildFilters();
expRender();
