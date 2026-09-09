// ===== TAB 4: Septiembre - FCST y Riesgo (Abarrotes) =====
// renderTab4(d) se llama con DATA4_ALL.todos o .sin_baja segun el
// toggle 'excluir bajas' del header. sept_kw_context vive en
// DATA4_ALL (no dentro de todos/sin_baja) porque no depende del
// universo de items -- se pinta una sola vez, fuera de renderTab4.

function renderTab4(DATA4) {

document.getElementById('sept-insights').innerHTML = DATA4.insights_top.map(t =>
  `<div class="flex gap-2 items-start"><p>${t}</p></div>`).join('');

const k4 = DATA4.kpis;
document.getElementById('sept-kpi-fcst').textContent = fmtM(k4.fcst_total);
document.getElementById('sept-kpi-ly').textContent = fmtM(k4.ly_total);
document.getElementById('sept-kpi-needed').textContent = fmtPct(k4.growth_needed_total);
document.getElementById('sept-kpi-actual-trend').textContent = `MTD real: ${fmtPct(k4.crec_mtd_actual_total)} · YTD real: ${fmtPct(k4.crec_ytd_actual_total)} · L7D real: ${fmtPct(k4.crec_l7d_actual_total)}`;

const trendEl = document.getElementById('sept-kpi-trend');
trendEl.textContent = fmtM(k4.trend_total);
trendEl.className = 'text-2xl font-bold ' + (k4.gap_total >= 0 ? 'kpi-up' : 'kpi-dn');

const gapEl = document.getElementById('sept-kpi-gap');
const gapSign = k4.gap_total >= 0 ? '+' : '';
gapEl.textContent = `${gapSign}${fmtM(k4.gap_total)} (${fmtPct(k4.gap_pct_total)})`;
gapEl.className = 'text-2xl font-bold ' + (k4.gap_total >= 0 ? 'kpi-up' : 'kpi-dn');

// ---- Evento "A la Mexicana" ----
const amx = DATA4.evento_amx;
document.getElementById('amx-status-msg').textContent = amx.status_msg;
document.getElementById('amx-kpi-com').textContent = fmtM(amx.kpis.com_amx);
document.getElementById('amx-kpi-comly').textContent = fmtM(amx.kpis.com_amxly);
document.getElementById('amx-kpi-comly-comparable').textContent = amx.iniciado
  ? `dia comparable (${amx.dias_transcurridos}/${amx.dias_totales} dias): ${fmtM(amx.kpis.com_amxly_comparable)}`
  : '';

const amxCrecComEl = document.getElementById('amx-kpi-crec-com');
amxCrecComEl.textContent = fmtPct(amx.kpis.crec_com_amx);
amxCrecComEl.className = 'text-2xl font-bold ' + (amx.kpis.crec_com_amx == null ? 'kpi-muted' : (amx.kpis.crec_com_amx >= 0 ? 'kpi-up' : 'kpi-dn'));

const amxCrecPisoEl = document.getElementById('amx-kpi-crec-piso');
amxCrecPisoEl.textContent = fmtPct(amx.kpis.crec_piso_amx);
amxCrecPisoEl.className = 'text-2xl font-bold ' + (amx.kpis.crec_piso_amx == null ? 'kpi-muted' : (amx.kpis.crec_piso_amx >= 0 ? 'kpi-up' : 'kpi-dn'));

document.getElementById('amx-tbl-cats').innerHTML = amx.categorias.map(c => `
  <tr>
    <td class="px-3 py-1.5 font-medium">${c.cat_desc}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(c.com_amx)}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(c.com_amxly)}</td>
    <td class="px-3 py-1.5 text-right">${badge(c.crec_com_amx)}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(c.piso_amx)}</td>
    <td class="px-3 py-1.5 text-right">${badge(c.crec_piso_amx)}</td>
    <td class="px-3 py-1.5 text-right">${c.share_com_amx != null ? (c.share_com_amx*100).toFixed(1)+'%' : '-'}</td>
  </tr>`).join('');

// ---- Chart: FCST vs Estimado de tendencia por categoria ----
const RISK_COLOR = { 'Alto': '#ea1100', 'Moderado': '#ffc220', 'Bajo': '#2a8703' };
Chart.getChart('sept-chart')?.destroy();
new Chart(document.getElementById('sept-chart'), {
  type: 'bar',
  data: {
    labels: DATA4.categorias.map(c => c.cat_desc),
    datasets: [
      { label: 'FCST Sept (target)', data: DATA4.categorias.map(c => c.fcst_sept/1e6), backgroundColor: '#0053e2', borderRadius: 6 },
      { label: 'Estimado tendencia YTD', data: DATA4.categorias.map(c => c.trend_estimate/1e6),
        backgroundColor: DATA4.categorias.map(c => RISK_COLOR[c.risk]), borderRadius: 6 },
    ]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: 'top' } },
    scales: { y: { ticks: { callback: v => `$${v}M` } } }
  }
});

// ---- Tabla riesgo por categoria ----
const riskChip = r => ({ 'Alto': 'chip-red', 'Moderado': 'chip-gray', 'Bajo': 'chip-green' }[r] || 'chip-gray');
document.getElementById('sept-tbl-cats').innerHTML = DATA4.categorias.map(c => `
  <tr class="${c.gap < 0 ? 'tbl-row-neg' : 'tbl-row-pos'}">
    <td class="px-3 py-1.5 font-medium">${c.cat_desc}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(c.fcst_sept)}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(c.ly_sept)}</td>
    <td class="px-3 py-1.5 text-right">${fmtPct(c.growth_needed)}</td>
    <td class="px-3 py-1.5 text-right">${badge(c.crec_mtd_actual)}</td>
    <td class="px-3 py-1.5 text-right">${badge(c.crec_ytd_actual)}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(c.trend_estimate)}</td>
    <td class="px-3 py-1.5 text-right font-mono">${c.gap >= 0 ? '+' : ''}${fmtPesos(c.gap)}</td>
    <td class="px-3 py-1.5 text-right">${c.gap_pct >= 0 ? '+' : ''}${(c.gap_pct*100).toFixed(1)}%</td>
    <td class="px-3 py-1.5 text-center"><span class="chip ${riskChip(c.risk)}">${c.risk}</span></td>
  </tr>`).join('');

// ---- Tablas de items ----
document.getElementById('sept-tbl-apagar').innerHTML = DATA4.items.apagar_incendios.map(r => `
  <tr class="tbl-row-neg">
    <td class="px-3 py-1.5"><span class="font-medium">${r.item_desc}</span><br><span class="text-xs text-gray-400">#${r.item_nbr}</span></td>
    <td class="px-3 py-1.5 text-xs">${r.sub_cat_desc}<br><span class="text-gray-400">${r.boost_motivo}</span></td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(r.piso_mtd)}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(r.com_mtd)}</td>
    <td class="px-3 py-1.5 text-right"><span class="badge-flat">${(r.share_com_mtd*100).toFixed(1)}%</span></td>
    <td class="px-3 py-1.5 text-right">${badge(r.crec_com_l7d)}</td>
    <td class="px-3 py-1.5 text-center">${r.promo_vigente ? '<span class="chip chip-green">Sí</span>' : '<span class="chip chip-red">No</span>'}</td>
    <td class="px-3 py-1.5 text-center"><span class="chip ${semColor(r.semaforo)}">${r.semaforo}</span></td>
  </tr>`).join('');

document.getElementById('sept-tbl-doblar').innerHTML = DATA4.items.doblar_apuesta.map(r => `
  <tr class="tbl-row-pos">
    <td class="px-3 py-1.5"><span class="font-medium">${r.item_desc}</span><br><span class="text-xs text-gray-400">#${r.item_nbr}</span></td>
    <td class="px-3 py-1.5 text-xs">${r.sub_cat_desc}<br><span class="text-gray-400">${r.boost_motivo}</span></td>
    <td class="px-3 py-1.5 text-center">${r.fiestas_patrias ? '<span class="chip chip-green">Sí</span>' : '<span class="chip chip-gray">No</span>'}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(r.com_mtd)}</td>
    <td class="px-3 py-1.5 text-right">${badge(r.crec_com_mtd)}</td>
    <td class="px-3 py-1.5 text-right">${badge(r.crec_com_l7d)}</td>
  </tr>`).join('');

document.getElementById('sept-tbl-blanco').innerHTML = DATA4.items.blanco_total.map(r => `
  <tr>
    <td class="px-3 py-1.5"><span class="font-medium">${r.item_desc}</span><br><span class="text-xs text-gray-400">#${r.item_nbr}</span></td>
    <td class="px-3 py-1.5 text-xs">${r.sub_cat_desc}<br><span class="text-gray-400">${r.boost_motivo}</span></td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(r.piso_mtd)}</td>
    <td class="px-3 py-1.5 text-right"><span class="badge-flat">${(r.share_com_mtd*100).toFixed(1)}%</span></td>
    <td class="px-3 py-1.5 text-center">${r.en_parrilla ? '<span class="chip chip-green">Sí</span>' : '<span class="chip chip-gray">No</span>'}</td>
    <td class="px-3 py-1.5 text-center"><span class="chip ${semColor(r.semaforo)}">${r.semaforo}</span></td>
  </tr>`).join('');

}

// ---- Chips de contexto: terminos Fiestas Patrias (NO depende del
// toggle 'excluir bajas' -- viene de un reporte de busqueda aparte) ----
document.getElementById('sept-kw-chips').innerHTML = DATA4_ALL.sept_kw_context.fiestas_26_top.map(([term, n]) =>
  `<span class="chip chip-gray" style="font-size:13px;padding:6px 14px;">${term} <span class="text-gray-400">(${n})</span></span>`
).join('');

renderTab4(DATA4_ALL.todos);
