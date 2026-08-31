// ===== TAB 1: Resumen y Accionables =====

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
document.getElementById('kpiAccionables').textContent = `${k1.n_accionables} accionables (parrilla+promo) · ${k1.n_impulsar} urgentes · ${k1.n_replicar} éxito`;

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

// ---- Category cards (clickeables) ----
document.getElementById('catCards').innerHTML = DATA1.categorias.map(c => `
  <div class="card cat-card p-4" onclick="toggleCatExpand('${c.cat_desc.replace(/'/g, "\\'")}')">
    <p class="font-bold text-blue-800 mb-1">${c.cat_desc}</p>
    <p class="text-xs text-gray-400 mb-2">${c.n_items.toLocaleString('es-MX')} items · ${c.n_accionables} en parrilla+promo vigente · click para ver detalle</p>
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
    <div class="flex justify-between items-center mb-2 opacity-70">
      <span class="text-xs text-gray-400">Piso MTD (ref.)</span>
      <span class="text-xs text-gray-500">${fmtM(c.piso_mtd)} · ${fmtPct(c.crec_piso_mtd)}</span>
    </div>
    <div class="flex gap-1 flex-wrap mt-2">
      ${c.n_impulsar > 0 ? `<span class="chip chip-red">${c.n_impulsar} impulsar</span>` : ''}
      ${c.n_riesgo > 0 ? `<span class="chip chip-red">${c.n_riesgo} riesgo</span>` : ''}
      ${c.n_replicar > 0 ? `<span class="chip chip-green">${c.n_replicar} éxito</span>` : ''}
    </div>
  </div>`).join('');

function itemMiniRow(r, showPromo) {
  return `<tr>
    <td class="px-3 py-1.5"><span class="font-medium">${r.item_desc}</span><br><span class="text-xs text-gray-400">#${r.item_nbr}</span></td>
    ${showPromo ? `<td class="px-3 py-1.5 text-xs">${r.promo || '—'}</td>` : ''}
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
    <p class="section-title mb-3">${catDesc} — detalle completo de accionables</p>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <p class="font-bold text-red-700 mb-2">Impulsar .com (${items.impulsar.length})</p>
        ${items.impulsar.length === 0 ? '<p class="text-xs text-gray-400">Sin items urgentes en esta categoría.</p>' : `
        <table class="text-sm w-full border-collapse">
          <thead><tr class="text-xs"><th class="px-2 py-1 text-left">Item</th><th class="px-2 py-1 text-left">Promo</th><th class="px-2 py-1 text-right">.com MTD</th><th class="px-2 py-1 text-right">Crec MTD</th><th class="px-2 py-1 text-right">Crec L7D</th><th class="px-2 py-1 text-center">Top L7D</th></tr></thead>
          <tbody>${items.impulsar.map(r => itemMiniRow(r, true)).join('')}</tbody>
        </table>`}
      </div>
      <div>
        <p class="font-bold text-green-700 mb-2">Replicar éxito (${items.replicar.length})</p>
        ${items.replicar.length === 0 ? '<p class="text-xs text-gray-400">Sin casos de éxito en parrilla+promo en esta categoría.</p>' : `
        <table class="text-sm w-full border-collapse">
          <thead><tr class="text-xs"><th class="px-2 py-1 text-left">Item</th><th class="px-2 py-1 text-left">Promo</th><th class="px-2 py-1 text-right">.com MTD</th><th class="px-2 py-1 text-right">Crec MTD</th><th class="px-2 py-1 text-right">Crec L7D</th><th class="px-2 py-1 text-center">Top L7D</th></tr></thead>
          <tbody>${items.replicar.map(r => itemMiniRow(r, true)).join('')}</tbody>
        </table>`}
      </div>
    </div>`;
  box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ---- Tabla Impulsar (global) ----
document.getElementById('tblImpulsar').innerHTML = DATA1.accionables.impulsar.map(r => `
  <tr class="tbl-row-neg">
    <td class="px-3 py-1.5"><span class="font-medium">${r.item_desc}</span><br><span class="text-xs text-gray-400">#${r.item_nbr}</span></td>
    <td class="px-3 py-1.5 text-xs">${r.cat_desc}</td>
    <td class="px-3 py-1.5 text-xs">${r.promo || '—'}</td>
    <td class="px-3 py-1.5 text-xs">${r.promo_fin || '—'}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(r.piso_mtd)}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(r.com_mtd)}</td>
    <td class="px-3 py-1.5 text-right">${badge(r.crec_com_mtd)}</td>
    <td class="px-3 py-1.5 text-right">${badge(r.crec_com_l7d)}</td>
    <td class="px-3 py-1.5 text-center text-xs">#${r.top_l7d_cat ?? '-'}</td>
    <td class="px-3 py-1.5 text-center"><span class="chip ${semColor(r.semaforo)}">${r.semaforo}</span></td>
  </tr>`).join('');

// ---- Tabla Riesgo ----
if (DATA1.accionables.riesgo.length > 0) {
  document.getElementById('riesgoSection').style.display = 'block';
  document.getElementById('tblRiesgo').innerHTML = DATA1.accionables.riesgo.map(r => `
    <tr class="tbl-row-neg">
      <td class="px-3 py-1.5"><span class="font-medium">${r.item_desc}</span><br><span class="text-xs text-gray-400">#${r.item_nbr}</span></td>
      <td class="px-3 py-1.5 text-xs">${r.cat_desc}</td>
      <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(r.com_mtd)}</td>
      <td class="px-3 py-1.5 text-right">${badge(r.crec_com_mtd)}</td>
      <td class="px-3 py-1.5 text-center"><span class="chip ${semColor(r.semaforo)}">${r.semaforo}</span></td>
    </tr>`).join('');
}

// ---- Tabla Replicar (global) ----
document.getElementById('tblReplicar').innerHTML = DATA1.accionables.replicar.map(r => `
  <tr class="tbl-row-pos">
    <td class="px-3 py-1.5"><span class="font-medium">${r.item_desc}</span><br><span class="text-xs text-gray-400">#${r.item_nbr}</span></td>
    <td class="px-3 py-1.5 text-xs">${r.cat_desc}</td>
    <td class="px-3 py-1.5 text-xs">${r.promo || '—'}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(r.com_mtd)}</td>
    <td class="px-3 py-1.5 text-right">${badge(r.crec_com_mtd)}</td>
    <td class="px-3 py-1.5 text-right">${badge(r.crec_com_l7d)}</td>
    <td class="px-3 py-1.5 text-center text-xs">#${r.top_l7d_cat ?? '-'}</td>
  </tr>`).join('');

// ---- Recomendaciones finales ----
const cats1 = DATA1.categorias;
const best1 = [...cats1].sort((a,b) => b.crec_com_mtd - a.crec_com_mtd)[0];
const worstTrend1 = [...cats1].sort((a,b) => a.crec_com_l7d - b.crec_com_l7d)[0];
document.getElementById('recoCapitalizar').innerHTML = `
  <li>• ${best1.cat_desc}: .com +${(best1.crec_com_mtd*100).toFixed(1)}% MTD — el mejor motor de crecimiento del mes.</li>
  <li>• ${DATA1.accionables.replicar.length} items con promo vigente ya muestran tracción fuerte en .com — replicar su exhibición/keywords en items similares.</li>
  <li>• Mix .com sigue en ${(k1.share_com_mtd*100).toFixed(1)}% del total — margen amplio para ganar participación sin canibalizar Piso.</li>
`;
document.getElementById('recoAccionar').innerHTML = `
  <li>• ${k1.n_impulsar} items con promo vigente y parrilla activa cayendo en .com — dar boost de banner/búsqueda esta semana.</li>
  <li>• ${worstTrend1.cat_desc}: tendencia L7D (${fmtPct(worstTrend1.crec_com_l7d)}) muy por debajo del MTD (${fmtPct(worstTrend1.crec_com_mtd)}) — investigar causa (quiebre, precio, visibilidad).</li>
  <li>• Ver pestaña 3 para saber cuáles promos vigentes NO están apareciendo en los carruseles del sitio.</li>
`;
document.getElementById('recoMonitorear').innerHTML = `
  <li>• Tendencia general .com: MTD +${(k1.com_mtd_growth*100).toFixed(1)}% vs L7D +${(k1.com_l7d_growth*100).toFixed(1)}% — vigilar si la desaceleración se sostiene la próxima semana.</li>
  <li>• ${k1.n_monitorear} items adicionales en parrilla+promo sin señal clara (crecimiento entre -10% y +20%) — sin acción inmediata, solo seguimiento.</li>
  <li>• Piso crece +${(k1.piso_mtd_growth*100).toFixed(1)}% MTD — más lento que .com, consistente con la migración del canal.</li>
`;
