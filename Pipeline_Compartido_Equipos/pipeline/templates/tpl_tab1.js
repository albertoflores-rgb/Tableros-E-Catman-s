// ===== TAB 1: Resumen (generico, parametrizado) =====

// ---- Insights ----
document.getElementById('insightsTop').innerHTML = DATA1.insights_top.map(t =>
  `<div class="flex gap-2 items-start"><p>${t}</p></div>`).join('');

// ---- KPIs ----
const k1 = DATA1.kpis;
document.getElementById('kpiComMtd').textContent = fmtM(k1.com_mtd);
document.getElementById('kpiComMtdGrowth').innerHTML = badge(k1.com_mtd_growth) + ' vs LY';
const l7dEl = document.getElementById('kpiComL7d');
l7dEl.textContent = fmtPct(k1.com_l7d_growth);
l7dEl.className = 'text-2xl font-bold ' + (k1.com_l7d_growth >= 0.02 ? 'kpi-up' : (k1.com_l7d_growth <= -0.02 ? 'kpi-dn' : 'kpi-neutral'));
document.getElementById('kpiPisoMtd').textContent = fmtM(k1.piso_mtd);
document.getElementById('kpiPisoMtdGrowth').textContent = fmtPct(k1.piso_mtd_growth) + ' vs LY';
document.getElementById('kpiShareCom').textContent = fmtPct(k1.share_com_mtd).replace('+','');
document.getElementById('kpiMovers').textContent = `${k1.n_riesgo} riesgo · ${k1.n_impulsar} impulsar · ${k1.n_replicar} éxito (top 20 c/u)`;
document.getElementById('kpiSociosMtd').textContent = (k1.com_socios_mtd ?? 0).toLocaleString('es-MX');
document.getElementById('kpiSociosMtdGrowth').innerHTML = (k1.com_socios_mtd_growth == null) ? '<span class="text-gray-400">sin LY</span>' : badge(k1.com_socios_mtd_growth) + ' vs LY';

// ---- Chart: .com por categoria ----
new Chart(document.getElementById('comCatChart'), {
  type: 'bar',
  data: {
    labels: DATA1.categorias.map(c => c.cat_desc),
    datasets: [
      { label: '.com TY ($M)', data: DATA1.categorias.map(c => c.com_mtd/1e6), backgroundColor: '#0053e2', borderRadius: 6 },
      { label: '.com LY ($M)', data: DATA1.categorias.map(c => c.com_mtdly/1e6), backgroundColor: '#a8c0f5', borderRadius: 6 }
    ]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: 'top' } },
    scales: { y: { ticks: { callback: v => `$${v}M` } } }
  }
});

// ---- Chart: MTD vs L7D growth ----
new Chart(document.getElementById('trendChart'), {
  type: 'bar',
  data: {
    labels: DATA1.categorias.map(c => c.cat_desc),
    datasets: [
      { label: 'Crecimiento MTD', data: DATA1.categorias.map(c => c.crec_com_mtd*100), backgroundColor: '#0053e2', borderRadius: 6 },
      { label: 'Crecimiento Últimos 7D', data: DATA1.categorias.map(c => c.crec_com_l7d*100), backgroundColor: '#ffc220', borderRadius: 6 }
    ]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: 'top' }, tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}%` } } },
    scales: { y: { ticks: { callback: v => `${v}%` } } }
  }
});

// ---- Chart: Piso referencia ----
new Chart(document.getElementById('pisoCatChart'), {
  type: 'bar',
  data: {
    labels: DATA1.categorias.map(c => c.cat_desc),
    datasets: [
      { label: 'Piso TY ($M)', data: DATA1.categorias.map(c => c.piso_mtd/1e6), backgroundColor: '#c7cfdb', borderRadius: 6 },
      { label: 'Piso LY ($M)', data: DATA1.categorias.map(c => c.piso_mtdly/1e6), backgroundColor: '#e6e9ef', borderRadius: 6 }
    ]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: 'top' } },
    scales: { y: { ticks: { callback: v => `$${v}M` } } }
  }
});

// ---- Category cards (clickeables -- ver toggleCatExpand, misma
// funcionalidad que el tablero de Abarrotes: click en la tarjeta
// expande el detalle de movers de esa categoria) ----
document.getElementById('catCards').innerHTML = DATA1.categorias.map(c => `
  <div class="card cat-card p-4" onclick="toggleCatExpand('${c.cat_desc.replace(/'/g, "\\'")}')">
    <p class="font-bold text-blue-800 mb-1">${c.cat_desc}</p>
    <p class="text-xs text-gray-400 mb-2">${c.n_items.toLocaleString('es-MX')} items · click para ver detalle</p>
    <div class="flex justify-between items-center mb-1">
      <span class="text-xs text-gray-500">.com MTD</span>
      <span class="font-mono font-bold">${fmtM(c.com_mtd)}</span>
    </div>
    <div class="flex justify-between items-center mb-2">
      <span class="text-xs text-gray-500">vs LY</span>
      ${badge(c.crec_com_mtd)}
    </div>
    <div class="flex justify-between items-center mb-1">
      <span class="text-xs text-gray-500">Tendencia .com L7D</span>
      ${badge(c.crec_com_l7d)}
    </div>
    <div class="flex justify-between items-center opacity-70">
      <span class="text-xs text-gray-400">Piso MTD (ref.)</span>
      <span class="text-xs text-gray-500">${fmtM(c.piso_mtd)} · ${fmtPct(c.crec_piso_mtd)}</span>
    </div>
    <div class="flex gap-1 flex-wrap mt-2">
      ${c.n_impulsar > 0 ? `<span class="chip chip-red">${c.n_impulsar} impulsar</span>` : ''}
      ${c.n_riesgo > 0 ? `<span class="chip chip-red">${c.n_riesgo} riesgo</span>` : ''}
      ${c.n_replicar > 0 ? `<span class="chip chip-green">${c.n_replicar} éxito</span>` : ''}
    </div>
  </div>`).join('');

function itemMiniRow(r) {
  return `<tr>
    <td class="px-3 py-1.5"><span class="font-medium">${r.item_desc}</span><br><span class="text-xs text-gray-400">#${r.item_nbr}</span></td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(r.com_mtd)}</td>
    <td class="px-3 py-1.5 text-right">${badge(r.crec_com_mtd)}</td>
    <td class="px-3 py-1.5 text-right">${badge(r.crec_com_l7d)}</td>
    <td class="px-3 py-1.5 text-center text-xs">#${r.top_l7d_cat ?? '-'}</td>
  </tr>`;
}

let expandedCat = null;
function toggleCatExpand(catDesc) {
  const box = document.getElementById('catExpand');
  if (expandedCat === catDesc) {
    box.style.display = 'none';
    expandedCat = null;
    return;
  }
  expandedCat = catDesc;
  const items = DATA1.categoria_items[catDesc] || { impulsar: [], replicar: [], riesgo: [] };
  box.style.display = 'block';
  box.innerHTML = `
    <p class="section-title mb-1">${catDesc} — detalle de movers (top 15 por volumen c/u)</p>
    <p class="text-xs text-gray-400 mb-3">Sin gate de parrilla/promo todavía para este equipo -- son movers puros por volumen, no accionables curados como en Abarrotes.</p>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <p class="font-bold text-red-700 mb-2">Necesitan impulso .com (${items.impulsar.length})</p>
        ${items.impulsar.length === 0 ? '<p class="text-xs text-gray-400">Sin movers de este tipo en esta categoría.</p>' : `
        <table class="text-sm w-full border-collapse">
          <thead><tr class="text-xs"><th class="px-2 py-1 text-left">Item</th><th class="px-2 py-1 text-right">.com MTD</th><th class="px-2 py-1 text-right">Crec MTD</th><th class="px-2 py-1 text-right">Crec L7D</th><th class="px-2 py-1 text-center">Top L7D</th></tr></thead>
          <tbody>${items.impulsar.map(itemMiniRow).join('')}</tbody>
        </table>`}
      </div>
      <div>
        <p class="font-bold text-green-700 mb-2">Replicar éxito (${items.replicar.length})</p>
        ${items.replicar.length === 0 ? '<p class="text-xs text-gray-400">Sin movers de este tipo en esta categoría.</p>' : `
        <table class="text-sm w-full border-collapse">
          <thead><tr class="text-xs"><th class="px-2 py-1 text-left">Item</th><th class="px-2 py-1 text-right">.com MTD</th><th class="px-2 py-1 text-right">Crec MTD</th><th class="px-2 py-1 text-right">Crec L7D</th><th class="px-2 py-1 text-center">Top L7D</th></tr></thead>
          <tbody>${items.replicar.map(itemMiniRow).join('')}</tbody>
        </table>`}
      </div>
    </div>
    ${items.riesgo.length > 0 ? `
    <div class="mt-4">
      <p class="font-bold text-yellow-700 mb-2">Riesgo de quiebre (${items.riesgo.length})</p>
      <table class="text-sm w-full border-collapse">
        <thead><tr class="text-xs"><th class="px-2 py-1 text-left">Item</th><th class="px-2 py-1 text-right">.com MTD</th><th class="px-2 py-1 text-right">Crec MTD</th><th class="px-2 py-1 text-right">Crec L7D</th><th class="px-2 py-1 text-center">Top L7D</th></tr></thead>
        <tbody>${items.riesgo.map(itemMiniRow).join('')}</tbody>
      </table>
    </div>` : ''}`;
  box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ---- Tablas de movers (globales, top 20) ----
function moverRow(r, extra) {
  return `<tr class="${r.crec_com_mtd < 0 ? 'tbl-row-neg' : 'tbl-row-pos'}">
    <td class="px-3 py-1.5"><span class="font-medium">${r.item_desc}</span><br><span class="text-xs text-gray-400">#${r.item_nbr}</span></td>
    <td class="px-3 py-1.5 text-xs">${r.cat_desc}</td>
    ${extra}
  </tr>`;
}

document.getElementById('tblImpulsar').innerHTML = DATA1.movers.impulsar.map(r => moverRow(r, `
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(r.piso_mtd)}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(r.com_mtd)}</td>
    <td class="px-3 py-1.5 text-right">${badge(r.crec_com_mtd)}</td>
    <td class="px-3 py-1.5 text-right">${badge(r.crec_com_l7d)}</td>
    <td class="px-3 py-1.5 text-center text-xs">#${r.top_l7d_cat ?? '-'}</td>
    <td class="px-3 py-1.5 text-center"><span class="chip ${semColor(r.semaforo)}">${r.semaforo}</span></td>`)).join('');

if (DATA1.movers.riesgo.length > 0) {
  document.getElementById('riesgoSection').style.display = 'block';
  document.getElementById('tblRiesgo').innerHTML = DATA1.movers.riesgo.map(r => moverRow(r, `
      <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(r.com_mtd)}</td>
      <td class="px-3 py-1.5 text-right">${badge(r.crec_com_mtd)}</td>
      <td class="px-3 py-1.5 text-center"><span class="chip ${semColor(r.semaforo)}">${r.semaforo}</span></td>`)).join('');
}

document.getElementById('tblReplicar').innerHTML = DATA1.movers.replicar.map(r => moverRow(r, `
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(r.com_mtd)}</td>
    <td class="px-3 py-1.5 text-right">${badge(r.crec_com_mtd)}</td>
    <td class="px-3 py-1.5 text-right">${badge(r.crec_com_l7d)}</td>
    <td class="px-3 py-1.5 text-center text-xs">#${r.top_l7d_cat ?? '-'}</td>`)).join('');
