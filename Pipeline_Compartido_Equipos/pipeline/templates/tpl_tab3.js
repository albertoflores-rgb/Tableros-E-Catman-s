// ===== TAB 3: Septiembre - FCST y Riesgo (generico) =====
if (DATA3.disponible === false) {
  document.getElementById('tab3-unavailable').style.display = 'block';
  document.getElementById('tab3-unavailable-motivo').textContent = DATA3.motivo || 'Archivo FCST no encontrado en este equipo.';
  document.getElementById('tab3-content').style.display = 'none';
} else {
document.getElementById('sept-insights').innerHTML = DATA3.insights_top.map(t =>
  `<div class="flex gap-2 items-start"><p>${t}</p></div>`).join('');

const k3 = DATA3.kpis;
document.getElementById('sept-kpi-fcst').textContent = fmtM(k3.fcst_total);
document.getElementById('sept-kpi-ly').textContent = fmtM(k3.ly_total);
document.getElementById('sept-kpi-needed').textContent = fmtPct(k3.growth_needed_total);
document.getElementById('sept-kpi-actual-trend').textContent = `MTD real: ${fmtPct(k3.crec_mtd_actual_total)} \u00b7 YTD real: ${fmtPct(k3.crec_ytd_actual_total)} \u00b7 L7D real: ${fmtPct(k3.crec_l7d_actual_total)}`;

const trendEl3 = document.getElementById('sept-kpi-trend');
trendEl3.textContent = fmtM(k3.trend_total);
trendEl3.className = 'text-2xl font-bold ' + (k3.gap_total >= 0 ? 'kpi-up' : 'kpi-dn');

const gapEl3 = document.getElementById('sept-kpi-gap');
const gapSign3 = k3.gap_total >= 0 ? '+' : '';
gapEl3.textContent = `${gapSign3}${fmtM(k3.gap_total)} (${fmtPct(k3.gap_pct_total)})`;
gapEl3.className = 'text-2xl font-bold ' + (k3.gap_total >= 0 ? 'kpi-up' : 'kpi-dn');

// ---- Evento "A la Mexicana" ----
const amx3 = DATA3.evento_amx;
document.getElementById('amx-status-msg').textContent = amx3.status_msg;
document.getElementById('amx-kpi-com').textContent = fmtM(amx3.kpis.com_amx);
document.getElementById('amx-kpi-comly').textContent = fmtM(amx3.kpis.com_amxly);

const amxCrecComEl3 = document.getElementById('amx-kpi-crec-com');
amxCrecComEl3.textContent = fmtPct(amx3.kpis.crec_com_amx);
amxCrecComEl3.className = 'text-2xl font-bold ' + (amx3.kpis.crec_com_amx == null ? 'kpi-muted' : (amx3.kpis.crec_com_amx >= 0 ? 'kpi-up' : 'kpi-dn'));

const amxCrecPisoEl3 = document.getElementById('amx-kpi-crec-piso');
amxCrecPisoEl3.textContent = fmtPct(amx3.kpis.crec_piso_amx);
amxCrecPisoEl3.className = 'text-2xl font-bold ' + (amx3.kpis.crec_piso_amx == null ? 'kpi-muted' : (amx3.kpis.crec_piso_amx >= 0 ? 'kpi-up' : 'kpi-dn'));

document.getElementById('amx-tbl-cats').innerHTML = amx3.categorias.map(c => `
  <tr>
    <td class="px-3 py-1.5 font-medium">${c.cat_desc}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(c.com_amx)}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(c.com_amxly)}</td>
    <td class="px-3 py-1.5 text-right">${badge(c.crec_com_amx)}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(c.piso_amx)}</td>
    <td class="px-3 py-1.5 text-right">${badge(c.crec_piso_amx)}</td>
    <td class="px-3 py-1.5 text-right">${c.share_com_amx != null ? (c.share_com_amx*100).toFixed(1)+'%' : '-'}</td>
  </tr>`).join('');

const RISK_COLOR3 = { 'Alto': '#ea1100', 'Moderado': '#ffc220', 'Bajo': '#2a8703', 'Sin dato': '#9ca3af' };
new Chart(document.getElementById('sept-chart'), {
  type: 'bar',
  data: {
    labels: DATA3.categorias.map(c => c.cat_desc),
    datasets: [
      { label: 'FCST Sept (target BP)', data: DATA3.categorias.map(c => c.fcst_sept / 1e6), backgroundColor: '#0053e2', borderRadius: 6 },
      { label: 'Estimado tendencia YTD', data: DATA3.categorias.map(c => c.trend_estimate != null ? c.trend_estimate / 1e6 : 0),
        backgroundColor: DATA3.categorias.map(c => RISK_COLOR3[c.risk] || '#9ca3af'), borderRadius: 6 },
    ]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: 'top' } },
    scales: { y: { ticks: { callback: v => `$${v}M` } } }
  }
});

const riskChip3 = r => ({ 'Alto': 'chip-red', 'Moderado': 'chip-gray', 'Bajo': 'chip-green', 'Sin dato': 'chip-gray' }[r] || 'chip-gray');
document.getElementById('sept-tbl-cats').innerHTML = DATA3.categorias.map(c => `
  <tr class="${c.gap != null && c.gap < 0 ? 'tbl-row-neg' : 'tbl-row-pos'}">
    <td class="px-3 py-1.5 font-medium">${c.cat_desc}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(c.fcst_sept)}</td>
    <td class="px-3 py-1.5 text-right font-mono">${c.fcst_vobo != null ? fmtPesos(c.fcst_vobo) : '-'}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(c.ly_sept)}</td>
    <td class="px-3 py-1.5 text-right">${fmtPct(c.growth_needed)}</td>
    <td class="px-3 py-1.5 text-right">${badge(c.crec_mtd_actual)}</td>
    <td class="px-3 py-1.5 text-right">${badge(c.crec_ytd_actual)}</td>
    <td class="px-3 py-1.5 text-right font-mono">${c.trend_estimate != null ? fmtPesos(c.trend_estimate) : '-'}</td>
    <td class="px-3 py-1.5 text-right font-mono">${c.gap != null ? (c.gap >= 0 ? '+' : '') + fmtPesos(c.gap) : '-'}</td>
    <td class="px-3 py-1.5 text-right">${c.gap_pct != null ? (c.gap_pct >= 0 ? '+' : '') + (c.gap_pct * 100).toFixed(1) + '%' : '-'}</td>
    <td class="px-3 py-1.5 text-center"><span class="chip ${riskChip3(c.risk)}">${c.risk}</span></td>
  </tr>`).join('');
} // fin del guard DATA3.disponible
