document.addEventListener('DOMContentLoaded', async () => {
  const role = (localStorage.getItem('afenix_role')||'').toUpperCase();
  if (!['CAJERO','ADMIN'].includes(role)){
    // allow both roles
    const r = role.toLowerCase();
    if(role==='ADMIN'){} else if(role==='CAJERO'){} else { if(!Afenix.guardPage('CAJERO') && !Afenix.guardPage('ADMIN')) return; }
  }
  const $ = s => document.querySelector(s);
  const { api, toast, esc, money } = Afenix;
  const filterDate = $('#filterDate');
  const filterStart = $('#filterStart');
  const filterEnd = $('#filterEnd');
  const filterDish = $('#filterDish');
  const filterMesero = $('#filterMesero');
  const applyBtn = $('#applyFilters');
  const clearBtn = $('#clearFilters');
  const exportBtn = $('#exportExcel');
  const statOrders = $('#statOrders');
  const statPlatos = $('#statPlatos');
  const statTotal = $('#statTotal');
  const platoBody = $('#platoBody');
  const platoTable = $('#platoTable');
  const platosEmpty = $('#platosEmpty');
  const platoCount = $('#platoCount');
  const detailBody = $('#detailBody');
  const detailWrap = $('#detailWrap');
  const detailEmpty = $('#detailEmpty');
  const detailCount = $('#detailCount');

  let currentData = null;
  let userMap = {};
  let dishMap = {};

  function fmtDate(d){
    try{
      const dt = new Date(d.endsWith('Z')?d:d+'Z');
      return dt.toLocaleDateString('es-CO');
    }catch{ return d||'—';}
  }
  function fmtTime(d){
    try{
      const dt = new Date(d.endsWith('Z')?d:d+'Z');
      return dt.toLocaleTimeString('es-CO',{hour:'2-digit',minute:'2-digit'});
    }catch{ return '—';}
  }

  async function loadFilters(){
    try{
      const dishes = await api('/api/v1/dishes?limit=100')||[];
      dishMap={};
      if(filterDish){
        filterDish.innerHTML='<option value="">Todos los platos</option>'+dishes.map(d=>{ dishMap[String(d.id)]=d.name; return `<option value="${d.id}">${esc(d.name)}</option>`;}).join('');
      }
    }catch(e){ console.error(e); }
    try{
      const users = await api('/api/v1/users?limit=100')||[];
      const meseros = users.filter(u=> u.role==='CAMARERO' || u.role==='MESERO');
      userMap={};
      users.forEach(u=> userMap[String(u.id)]=u.full_name||u.username);
      if(filterMesero){
        filterMesero.innerHTML='<option value="">Todos los meseros</option>'+meseros.map(u=> `<option value="${u.id}">${esc(u.full_name||u.username)}</option>`).join('');
        if(!meseros.length){
          // fallback show all
          filterMesero.innerHTML='<option value="">Todos los meseros</option>'+users.map(u=> `<option value="${u.id}">${esc(u.full_name||u.username)} (${u.role})</option>`).join('');
        }
      }
    }catch(e){ console.error(e); }
  }

  function buildQuery(){
    const params = new URLSearchParams();
    if(filterDate && filterDate.value){
      params.set('date', filterDate.value);
    } else {
      if(filterStart && filterStart.value) params.set('start_date', filterStart.value);
      if(filterEnd && filterEnd.value) params.set('end_date', filterEnd.value);
    }
    if(filterDish && filterDish.value) params.set('dish_id', filterDish.value);
    if(filterMesero && filterMesero.value) params.set('camarero_id', filterMesero.value);
    params.set('limit','500');
    return params.toString();
  }

  async function fetchReport(){
    const qs = buildQuery();
    const url = '/api/v1/orders/reports/sales' + (qs?`?${qs}`:'');
    const data = await api(url);
    return data;
  }

  function render(data){
    currentData = data;
    // Stats
    if(statOrders) statOrders.textContent = data.num_ordenes_pagadas ?? data.num_orders_pagadas ?? 0;
    if(statPlatos) statPlatos.textContent = data.total_platos_vendidos ?? 0;
    if(statTotal) statTotal.textContent = data.total_ventas_formatted || `$${((data.total_ventas_cents||data.total_ventas||0)/100).toLocaleString('es-CO')}` || '$0';
    // Platos table
    const platos = data.platos || [];
    if(platos.length){
      if(platoTable) platoTable.hidden=false;
      if(platosEmpty) platosEmpty.hidden=true;
      if(platoCount) platoCount.textContent = `${platos.length} plato${platos.length===1?'':'s'}`;
      if(platoBody) platoBody.innerHTML = platos.map(p=> `<tr><td>${esc(p.dish_name)}</td><td style="text-align:center;font-weight:700;">${p.quantity}</td><td style="text-align:right;">${p.total_formatted||money(p.total_cents)}</td></tr>`).join('');
    } else {
      if(platoTable) platoTable.hidden=true;
      if(platosEmpty) platosEmpty.hidden=false;
      if(platoCount) platoCount.textContent='';
      if(platoBody) platoBody.innerHTML='';
    }
    // Detail table: each order item row
    const orders = data.orders || [];
    const rows = [];
    orders.forEach(o=>{
      const dispNum = o.daily_number || o.id;
      const mesa = o.table_number != null ? String(o.table_number).padStart(2,'0') : String(o.table_id);
      const meseroName = esc(userMap[String(o.camarero_id)] || `Mesero #${o.camarero_id||'?'}`);
      const fecha = fmtDate(o.created_at);
      const hora = fmtTime(o.created_at);
      const estado = esc(o.status);
      (o.items||[]).forEach(it=>{
        // filter dish if selected? backend already filtered but keep logic for display: if filterDish selected, only show that dish
        if(filterDish && filterDish.value && String(it.dish_id)!==String(filterDish.value)) return;
        const plato = esc(it.dish_name || dishMap[String(it.dish_id)] || `Plato #${it.dish_id}`);
        const cant = Number(it.quantity)||0;
        const pu = money(it.unit_price);
        const tot = money((it.unit_price||0)*cant);
        rows.push(`<tr><td>${esc(String(dispNum))}</td><td>${fecha}</td><td>${hora}</td><td>${mesa}</td><td>${meseroName}</td><td>${plato}</td><td style="text-align:center;">${cant}</td><td style="text-align:right;">${pu}</td><td style="text-align:right;font-weight:700;">${tot}</td><td><span class="status status--${estado}">${estado}</span></td></tr>`);
      });
    });
    if(rows.length){
      if(detailWrap) detailWrap.hidden=false;
      if(detailEmpty) detailEmpty.hidden=true;
      if(detailCount) detailCount.textContent = `${rows.length} línea${rows.length===1?'':'s'} · ${orders.length} orden${orders.length===1?'':'es'}`;
      if(detailBody) detailBody.innerHTML = rows.join('');
    } else {
      if(detailWrap) detailWrap.hidden=true;
      if(detailEmpty) detailEmpty.hidden=false;
      if(detailCount) detailCount.textContent='';
      if(detailBody) detailBody.innerHTML='';
    }
  }

  async function applyFilters(){
    if(applyBtn){ applyBtn.disabled=true; applyBtn.textContent='Cargando...'; }
    try{
      const data = await fetchReport();
      render(data);
      toast('Reporte actualizado');
    }catch(e){
      toast(e.message||'No se pudo cargar el reporte','error');
    } finally {
      if(applyBtn){ applyBtn.disabled=false; applyBtn.textContent='Aplicar filtros'; }
    }
  }

  function clearFilters(){
    if(filterDate) filterDate.value='';
    if(filterStart) filterStart.value='';
    if(filterEnd) filterEnd.value='';
    if(filterDish) filterDish.value='';
    if(filterMesero) filterMesero.value='';
    applyFilters();
  }

  function exportExcel(){
    if(!currentData || !currentData.orders || !currentData.orders.length){
      toast('No hay datos para exportar','error');
      return;
    }
    const orders = currentData.orders;
    const rows = [];
    orders.forEach(o=>{
      const dispNum = o.daily_number || o.id;
      const mesa = o.table_number != null ? String(o.table_number).padStart(2,'0') : String(o.table_id);
      const meseroName = userMap[String(o.camarero_id)] || `Mesero #${o.camarero_id||'?'}`;
      const fecha = fmtDate(o.created_at);
      const hora = fmtTime(o.created_at);
      (o.items||[]).forEach(it=>{
        if(filterDish && filterDish.value && String(it.dish_id)!==String(filterDish.value)) return;
        rows.push({
          'Número orden': dispNum,
          'Fecha': fecha,
          'Hora': hora,
          'Mesa': mesa,
          'Mesero': meseroName,
          'Plato': it.dish_name || dishMap[String(it.dish_id)] || `Plato #${it.dish_id}`,
          'Cantidad': Number(it.quantity)||0,
          'Precio unitario': (it.unit_price/100).toFixed(2),
          'Total': ((it.unit_price||0)*(it.quantity||0)/100).toFixed(2),
          'Estado': o.status
        });
      });
    });
    if(!rows.length){
      toast('No hay filas para exportar con los filtros actuales','error');
      return;
    }
    // Summary sheet also
    const ws = XLSX.utils.json_to_sheet(rows);
    // Set column widths
    const colWidths = [{wch:12},{wch:12},{wch:10},{wch:8},{wch:18},{wch:22},{wch:10},{wch:14},{wch:12},{wch:12}];
    ws['!cols']=colWidths;
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Ventas');
    // Add summary sheet
    const summary = [
      {'Métrica':'Número de órdenes pagadas','Valor': currentData.num_ordenes_pagadas||currentData.num_orders_pagadas||0},
      {'Métrica':'Total platos vendidos','Valor': currentData.total_platos_vendidos||0},
      {'Métrica':'Total ventas','Valor': currentData.total_ventas_formatted||''},
      {'Métrica':'Filtros aplicados','Valor': buildQuery()||'ninguno'}
    ];
    const ws2 = XLSX.utils.json_to_sheet(summary);
    XLSX.utils.book_append_sheet(wb, ws2, 'Resumen');
    const fechaStr = new Date().toISOString().slice(0,10);
    const fname = `Reporte_Ventas_${fechaStr}.xlsx`;
    XLSX.writeFile(wb, fname);
    toast('Excel exportado: '+fname);
  }

  if(applyBtn) applyBtn.addEventListener('click', applyFilters);
  if(clearBtn) clearBtn.addEventListener('click', clearFilters);
  if(exportBtn) exportBtn.addEventListener('click', exportExcel);

  // Filters: if date specific set, clear start/end
  if(filterDate) filterDate.addEventListener('change', ()=>{ if(filterDate.value){ if(filterStart) filterStart.value=''; if(filterEnd) filterEnd.value=''; } });
  if(filterStart) filterStart.addEventListener('change', ()=>{ if(filterStart.value || (filterEnd && filterEnd.value)) if(filterDate) filterDate.value=''; });
  if(filterEnd) filterEnd.addEventListener('change', ()=>{ if(filterEnd.value || (filterStart && filterStart.value)) if(filterDate) filterDate.value=''; });

  await loadFilters();
  await applyFilters();
});
