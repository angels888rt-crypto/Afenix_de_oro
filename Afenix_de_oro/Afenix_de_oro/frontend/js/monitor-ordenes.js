document.addEventListener('DOMContentLoaded', async () => {
  if (!Afenix.guardPage('MONITOR')) return;
  const $ = s => document.querySelector(s);
  const { api, toast, esc, date } = Afenix;

  const mesaGrid = $('#mesaGrid');
  const detailPanel = $('#detailPanel');
  const ordersDetail = $('#ordersDetail');
  const detailTitle = $('#detailTitle');
  const detailSub = $('#detailSub');
  const lastUpdate = $('#lastUpdate');

  let pendingOrders = [];
  let userMap = {};
  let receiptConfig = { restaurant_name: 'RESTAURANTE', logo_url: null };
  let selectedMesa = null; // 1..12 or '>12'

  async function loadReceiptConfig(){
    try{
      const cfg = await api('/api/v1/receipt-config');
      if(cfg){
        receiptConfig.restaurant_name = cfg.restaurant_name || 'RESTAURANTE';
        receiptConfig.logo_url = cfg.logo_url || cfg.logo_path || null;
      }
    }catch(e){}
  }

  async function loadUsers(){
    try{
      const users = await api('/api/v1/users?limit=100') || [];
      userMap = {};
      users.forEach(u=>{ userMap[String(u.id)] = u.full_name || u.username; });
    }catch{ userMap={}; }
  }

  function getTableNumber(order){
    const n = order.table_number != null ? order.table_number : order.table_id;
    const v = Number(n);
    return Number.isFinite(v) ? v : null;
  }

  function groupByMesa(orders){
    const map = {};
    for(let i=1;i<=12;i++) map[String(i)] = [];
    map['>12'] = [];
    orders.forEach(o=>{
      const n = getTableNumber(o);
      if(n==null) return;
      if(n>=1 && n<=12) map[String(n)].push(o);
      else if(n>12) map['>12'].push(o);
    });
    return map;
  }

  function renderMesaGrid(){
    const grouped = groupByMesa(pendingOrders);
    const cards = [];
    for(let i=1;i<=12;i++){
      const key = String(i);
      const list = grouped[key] || [];
      const pending = list.length;
      const has = pending>0;
      cards.push(`
        <article class="mesa-card ${has?'has-pending':'no-pending'} ${selectedMesa===key?'is-selected':''}" data-mesa="${key}">
          <h3>Mesa ${String(i).padStart(2,'0')}</h3>
          <span class="mesa-count">${has? `${pending} ${pending===1?'orden pendiente':'órdenes pendientes'}` : 'Sin órdenes pendientes'}</span>
          <span class="mesa-sub">${has? 'Toque para ver' : '—'}</span>
        </article>
      `);
    }
    // >12
    const gt = grouped['>12'] || [];
    const hasGt = gt.length>0;
    cards.push(`
      <article class="mesa-card ${hasGt?'has-pending':'no-pending'} ${selectedMesa==='>12'?'is-selected':''}" data-mesa=">12">
        <h3>Mesas &gt; 12</h3>
        <span class="mesa-count">${hasGt? `${gt.length} ${gt.length===1?'orden pendiente':'órdenes pendientes'}` : 'Sin órdenes pendientes'}</span>
        <span class="mesa-sub">${hasGt? 'Agrupa 13,14,15...':'—'}</span>
      </article>
    `);
    mesaGrid.innerHTML = cards.join('');
    mesaGrid.querySelectorAll('[data-mesa]').forEach(el=>{
      el.addEventListener('click', ()=> openMesa(el.dataset.mesa));
    });
  }

  function openMesa(key){
    selectedMesa = key;
    renderMesaGrid();
    const grouped = groupByMesa(pendingOrders);
    let list = grouped[key] || [];
    detailPanel.hidden = false;
    if(key==='>12'){
      detailTitle.textContent = 'Mesas > 12';
      detailSub.textContent = list.length ? `${list.length} órdenes pendientes agrupadas` : 'Sin órdenes pendientes';
    } else {
      detailTitle.textContent = `Mesa ${String(Number(key)).padStart(2,'0')}`;
      detailSub.textContent = list.length ? `${list.length} órdenes pendientes` : 'Sin órdenes pendientes';
    }
    if(!list.length){
      ordersDetail.innerHTML = `<div class="empty-detail"><p style="font-size:1.05rem;margin:0 0 6px;">No hay órdenes pendientes</p><p class="muted">Las órdenes PENDIENTE del ciclo actual aparecerán aquí.</p></div>`;
      detailPanel.scrollIntoView({behavior:'smooth', block:'nearest'});
      return;
    }
    // For >12 agrupar por número de mesa dentro del detalle
    if(key==='>12'){
      // agrupar por mesa real
      const byReal = {};
      list.forEach(o=>{
        const n = getTableNumber(o);
        const k = String(n);
        if(!byReal[k]) byReal[k]=[];
        byReal[k].push(o);
      });
      const sortedKeys = Object.keys(byReal).sort((a,b)=>Number(a)-Number(b));
      ordersDetail.innerHTML = sortedKeys.map(mesaNum=>{
        const orders = byReal[mesaNum];
        return `<div style="margin-bottom:18px;"><h4 style="font-family:Cinzel,serif;font-size:.95rem;margin:0 0 10px;color:var(--ink);border-bottom:1px solid var(--line);padding-bottom:6px;">Mesa ${String(Number(mesaNum)).padStart(2,'0')} · ${orders.length} ${orders.length===1?'orden':'órdenes'}</h4>${orders.map(o=>orderCard(o)).join('')}</div>`;
      }).join('');
    } else {
      ordersDetail.innerHTML = list.map(o=>orderCard(o)).join('');
    }
    // bind print buttons
    ordersDetail.querySelectorAll('[data-print]').forEach(btn=>{
      btn.addEventListener('click', async ()=>{
        const id = btn.dataset.print;
        btn.disabled=true;
        const orig = btn.textContent;
        btn.textContent='Imprimiendo…';
        await handlePrint(id);
        setTimeout(()=>{ btn.disabled=false; btn.textContent=orig; },1200);
      });
    });
    detailPanel.scrollIntoView({behavior:'smooth', block:'start'});
  }

  function orderCard(o){
    const dispNum = o.daily_number || o.id;
    const dispMesa = (o.table_number != null ? String(o.table_number).padStart(2,'0') : String(o.table_id).padStart(2,'0'));
    const meseroName = esc(userMap[String(o.camarero_id)] || `Mesero #${o.camarero_id||'?'}`);
    const fecha = date(o.created_at);
    const estado = esc(o.status);
    const itemsHtml = (o.items||[]).map(it=>{
      const qty = Number(it.quantity)||0;
      const name = esc(it.dish_name || `Plato #${it.dish_id}`);
      const sel = (it.subcategory_selections||[]).map(s=> `${esc(s.subcategory_name)}: ${esc(s.option_name)}`).join(' · ');
      const selHtml = sel ? `<div style="font-size:.82rem;color:#6b5e56;margin-top:4px;">${sel}</div>` : '';
      return `<li><div><span>${name}</span>${selHtml}</div><span><strong>x${qty}</strong></span></li>`;
    }).join('') || '<li style="justify-content:center;color:var(--muted)">Sin platos</li>';
    const notas = o.notes ? `<div class="muted" style="margin-top:8px;font-size:.84rem;border-top:1px dashed #eadfcf;padding-top:8px;"><strong>Notas:</strong> ${esc(o.notes)}</div>` : '';
    const mesaTag = getTableNumber(o)>12 ? `<span class="mesa-badge">Mesa ${dispMesa}</span>` : '';
    return `<article class="order-card-monitor"><div class="order-card-monitor__head"><div><h4 class="order-card-monitor__title">Orden #${esc(String(dispNum))} · Mesa ${dispMesa} ${mesaTag}</h4><div class="monitor-card__meta">Mesero: <strong>${meseroName}</strong> · ${fecha} · <span class="status status--${estado}">${estado}</span></div></div><span class="status status--${estado}">${estado}</span></div><ul class="items-list">${itemsHtml}</ul>${notas}<div style="display:flex;justify-content:flex-end;margin-top:12px;"><button class="btn btn--primary btn--small" data-print="${o.id}">Imprimir</button></div></article>`;
  }

  function printKitchenTicket(order){
    const dispNum = order.daily_number || order.id;
    const dispMesaRaw = order.table_number != null ? order.table_number : order.table_id;
    const mesa = String(dispMesaRaw).padStart(2,'0');
    const mesero = userMap[String(order.camarero_id)] || ('Mesero #'+(order.camarero_id||'?'));
    const fecha = new Date(order.created_at.endsWith('Z')?order.created_at:order.created_at+'Z').toLocaleString('es-CO');
    const logoHtml = receiptConfig.logo_url ? `<div style="text-align:center;margin:6px 0 8px;"><img src="${receiptConfig.logo_url}" alt="Logo" style="max-width:38mm;max-height:16mm;object-fit:contain;display:inline-block;"></div>` : '';
    const nameHtml = `<div style="text-align:center;font-weight:700;font-size:13pt;text-transform:uppercase;margin:4px 0 6px;">${(receiptConfig.restaurant_name||'RESTAURANTE').toUpperCase()}</div>`;
    const metaHtml = `<div style="font-size:7.5pt;text-align:center;margin:4px 0 6px;">Pedido #${dispNum} · Mesa ${mesa} · ${mesero}<br>${fecha}</div>`;
    const itemsHtml = (order.items||[]).map(it=>{
      const qty = Number(it.quantity)||0;
      const nombre = (it.dish_name || ('Plato #'+it.dish_id));
      const short = nombre.length>22 ? nombre.slice(0,22)+'…' : nombre;
      const sel = (it.subcategory_selections||[]).map(s=> `${s.subcategory_name}: ${s.option_name}`).join(' / ');
      const selHtml = sel ? `<div style="font-size:7pt;text-align:left;padding-left:18px;color:#333;">${sel}</div>` : '';
      return `<div style="padding:4px 0;border-bottom:1px dashed #ddd;"><div style="display:flex;justify-content:center;align-items:center;gap:6px; font-size:10pt;"><span style="font-weight:700;">${qty}x</span><span style="flex:1;text-align:left;word-break:break-word;">${short}</span></div>${selHtml}</div>`;
    }).join('') || '<div style="text-align:center;padding:8px;color:#555;">Sin platos</div>';
    try{
      const w = window.open('', '_blank');
      if(!w) return false;
      w.document.write(`<html><head><title>Comprobante Cocina - Pedido #${dispNum}</title>
      <style>
        @page{size:57.5mm auto;margin:2mm;}
        *{box-sizing:border-box;}
        body{margin:0;padding:0;display:flex;justify-content:center;background:#fff;color:#000;font-family:'Courier New',Courier,monospace;}
        .ticket{width:57.5mm;max-width:57.5mm;background:#fff;padding:4mm 3mm;font-size:9pt;line-height:1.35;}
        .sep{border:none;border-top:1px solid #000;margin:8px 0;}
        .sep-dashed{border:none;border-top:1px dashed #000;margin:8px 0;}
        .items{margin:6px 0;}
      </style>
      </head><body><div class="ticket">
        ${logoHtml}
        ${nameHtml}
        <hr class="sep">
        ${metaHtml}
        <hr class="sep-dashed">
        <div class="items">${itemsHtml}</div>
        <hr class="sep-dashed">
        <div style="text-align:center;font-size:7pt;margin-top:8px;">— COMPROBANTE COCINA —</div>
      </div>
      <script>window.onload=function(){setTimeout(function(){window.print(); window.close();},300)}<\/script>
      </body></html>`);
      w.document.close();
      w.focus();
      return true;
    }catch(err){
      console.error('print error',err);
      return false;
    }
  }

  async function handlePrint(orderId){
    const order = pendingOrders.find(o=>String(o.id)===String(orderId));
    if(!order){ toast('Orden no encontrada','error'); return; }
    if(!['PENDIENTE','NUEVO'].includes(order.status)){ toast('Solo PENDIENTE se puede imprimir','error'); return; }
    const ok = printKitchenTicket(order);
    if(!ok){
      toast('La impresión falló. La orden permanece PENDIENTE.','error');
      return;
    }
    await new Promise(r=>setTimeout(r,700));
    try{
      await api(`/api/v1/orders/${order.id}`, { method:'PUT', body: JSON.stringify({ status:'EN_COCINA' }) });
      toast(`Orden #${order.daily_number||order.id} enviada a cocina (EN COCINA)`);
      await loadPending();
      // re-render detail if still selected
      if(selectedMesa) openMesa(selectedMesa);
      else renderMesaGrid();
    }catch(e){
      toast(e.message||'No se pudo actualizar a EN COCINA','error');
    }
  }

  async function loadPending(){
    try{
      const orders = await api('/api/v1/orders/monitor/pending?limit=100') || [];
      pendingOrders = orders.filter(o=>['PENDIENTE','NUEVO'].includes(o.status)).sort((a,b)=> new Date(a.created_at)- new Date(b.created_at));
      renderMesaGrid();
      if(lastUpdate) lastUpdate.textContent = `Actualizado: ${new Date().toLocaleTimeString('es-CO')}`;
      // if detail open, refresh it
      if(selectedMesa && !detailPanel.hidden){
        openMesa(selectedMesa);
      }
    }catch(e){
      toast(e.message||'No se pudieron cargar órdenes','error');
    }
  }

  // events
  $('#closeDetail')?.addEventListener('click', ()=>{
    detailPanel.hidden=true;
    selectedMesa=null;
    renderMesaGrid();
  });
  $('#refreshBtn')?.addEventListener('click', ()=> loadPending().catch(e=>toast(e.message,'error')));

  // init
  try{
    await Promise.all([loadUsers(), loadReceiptConfig()]);
    await loadPending();
  }catch(e){ toast(e.message,'error'); }

  setInterval(()=>{
    loadPending().catch(()=>{});
    loadUsers().catch(()=>{});
  }, 12000);
});
