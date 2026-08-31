// ===== TAB 3: Promos Vigentes + Mapeo en Sitio =====
document.getElementById('promosDisclaimer').textContent = DATA3.disclaimer;

const s3 = DATA3.summary;
document.getElementById('promoTotal').textContent = s3.n_total;
document.getElementById('promoVistos').textContent = `${s3.n_vistos} (${(s3.pct_vistos*100).toFixed(0)}%)`;
document.getElementById('promoNoVistos').textContent = s3.n_no_vistos;
document.getElementById('promoHome').textContent = s3.n_home;
document.getElementById('promoLPs').textContent = `${s3.n_despensa} / ${s3.n_socio_negocio}`;

function promoCell(pageData) {
  if (!pageData.visto) return '<span class="chip chip-gray">No</span>';
  const tip = `${pageData.carrusel || ''}: ${pageData.producto || ''} (score ${pageData.score})`;
  return `<span class="chip chip-green" title="${tip.replace(/"/g,'')}">Sí</span>`;
}

function promoPeriodoCells(p) {
  const shareTxt = p.share_com == null ? '-' : `<span class="badge-flat">${fmtPct(p.share_com).replace('+','')}</span>`;
  return `
    <td class="px-3 py-1.5 text-right font-mono">${p.piso_pzas == null ? '-' : p.piso_pzas.toLocaleString('es-MX')}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(p.piso_pesos)}</td>
    <td class="px-3 py-1.5 text-right font-mono">${p.com_pzas == null ? '-' : p.com_pzas.toLocaleString('es-MX')}</td>
    <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(p.com_pesos)}</td>
    <td class="px-3 py-1.5 text-right">${badge(p.crec_piso)}</td>
    <td class="px-3 py-1.5 text-right">${badge(p.crec_com)}</td>
    <td class="px-3 py-1.5 text-right">${shareTxt}</td>`;
}

function promoPeriodoTotals(items, period) {
  const pisoPzas = sumOrNull(items.map(i => i[period].piso_pzas));
  const pisoPesos = sumOrNull(items.map(i => i[period].piso_pesos));
  const comPzas = sumOrNull(items.map(i => i[period].com_pzas));
  const comPesos = sumOrNull(items.map(i => i[period].com_pesos));
  const crecPiso = exactGrowth(items.map(i => i[period].piso_pesos), items.map(i => i[period].piso_pesos_ly));
  const crecCom = exactGrowth(items.map(i => i[period].com_pesos), items.map(i => i[period].com_pesos_ly));
  const sumCom = comPesos || 0, sumPiso = pisoPesos || 0;
  const share = (sumCom + sumPiso) > 0 ? sumCom / (sumCom + sumPiso) : null;
  return `
    <td class="px-3 py-1.5 text-right">${pisoPzas == null ? '-' : Math.round(pisoPzas).toLocaleString('es-MX')}</td>
    <td class="px-3 py-1.5 text-right">${fmtPesos(pisoPesos)}</td>
    <td class="px-3 py-1.5 text-right">${comPzas == null ? '-' : Math.round(comPzas).toLocaleString('es-MX')}</td>
    <td class="px-3 py-1.5 text-right">${fmtPesos(comPesos)}</td>
    <td class="px-3 py-1.5 text-right">${badge(crecPiso)}</td>
    <td class="px-3 py-1.5 text-right">${badge(crecCom)}</td>
    <td class="px-3 py-1.5 text-right"><span class="badge-flat">${fmtPct(share).replace('+','')}</span></td>`;
}

function promoBuildTotals(items) {
  const tiendasAvg = avgOrNull(items.map(i => i.tiendas_con_inv));
  const invPzas = sumOrNull(items.map(i => i.inv_pzas_total));
  const invMxn = sumOrNull(items.map(i => i.inv_mxn_total));
  const nHome = items.filter(i => i.home.visto).length;
  const nDespensa = items.filter(i => i.despensa.visto).length;
  const nSocio = items.filter(i => i.socio_negocio.visto).length;
  const html = `
    <td class="px-3 py-1.5 text-left">TOTAL (${items.length} promos)</td>
    <td class="px-3 py-1.5">-</td>
    <td class="px-3 py-1.5">-</td>
    <td class="px-3 py-1.5 text-right">${avgOrNull(items.map(i => i.pct_ahorro)) == null ? '-' : (avgOrNull(items.map(i => i.pct_ahorro))*100).toFixed(1)+'% (prom)'}</td>
    <td class="px-3 py-1.5">-</td>
    <td class="px-3 py-1.5">-</td>
    <td class="px-3 py-1.5 text-right">${tiendasAvg == null ? '-' : tiendasAvg.toFixed(1)} (prom)</td>
    <td class="px-3 py-1.5 text-right">${invPzas == null ? '-' : Math.round(invPzas).toLocaleString('es-MX')}</td>
    <td class="px-3 py-1.5 text-right">${fmtPesos(invMxn)}</td>
    ${promoPeriodoTotals(items, 'ytd')}
    ${promoPeriodoTotals(items, 'mtd')}
    ${promoPeriodoTotals(items, 'l7d')}
    <td class="px-3 py-1.5">-</td>
    <td class="px-3 py-1.5 text-right">${nHome}/${items.length}</td>
    <td class="px-3 py-1.5 text-right">${nDespensa}/${items.length}</td>
    <td class="px-3 py-1.5 text-right">${nSocio}/${items.length}</td>`;
  document.getElementById('promoFoot').innerHTML = `<tr class="totals-row">${html}</tr>`;
}

function promoRender() {
  const filter = document.getElementById('promoFilter').value;
  let items = DATA3.items;
  if (filter === 'no_vistos') items = items.filter(i => i.n_paginas === 0);
  if (filter === 'vistos') items = items.filter(i => i.n_paginas > 0);

  document.getElementById('promoBody').innerHTML = items.map(r => `
    <tr class="${r.n_paginas === 0 ? 'tbl-row-neg' : 'tbl-row-pos'}">
      <td class="px-3 py-1.5"><span class="font-medium">${r.item_desc}</span><br><span class="text-xs text-gray-400">#${r.item_nbr}</span></td>
      <td class="px-3 py-1.5 text-xs">${r.cat_desc || '-'}</td>
      <td class="px-3 py-1.5 text-xs">${r.promo_desc || '—'}</td>
      <td class="px-3 py-1.5 text-right">${r.pct_ahorro == null ? '-' : (r.pct_ahorro*100).toFixed(1)+'%'}</td>
      <td class="px-3 py-1.5 text-xs">${r.promo_fin || '—'}</td>
      <td class="px-3 py-1.5 text-center"><span class="chip ${semColor(r.semaforo)}">${r.semaforo || '-'}</span></td>
      <td class="px-3 py-1.5 text-right font-mono">${r.tiendas_con_inv ?? '-'}</td>
      <td class="px-3 py-1.5 text-right font-mono">${r.inv_pzas_total == null ? '-' : r.inv_pzas_total.toLocaleString('es-MX')}</td>
      <td class="px-3 py-1.5 text-right font-mono">${fmtPesos(r.inv_mxn_total)}</td>
      ${promoPeriodoCells(r.ytd)}
      ${promoPeriodoCells(r.mtd)}
      ${promoPeriodoCells(r.l7d)}
      <td class="px-3 py-1.5 text-center text-xs">#${r.top_l7d_cat ?? '-'}</td>
      <td class="px-3 py-1.5 text-center">${promoCell(r.home)}</td>
      <td class="px-3 py-1.5 text-center">${promoCell(r.despensa)}</td>
      <td class="px-3 py-1.5 text-center">${promoCell(r.socio_negocio)}</td>
    </tr>`).join('');

  promoBuildTotals(items);
}

promoRender();
