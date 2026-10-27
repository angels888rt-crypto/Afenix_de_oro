document.addEventListener('DOMContentLoaded', async () => {
  if (!Afenix.guardPage('CAJERO')) return;
  const $ = s => document.querySelector(s);
  const { api, toast, esc, money, date } = Afenix;

  const ordersContainer = $('#orders');
  const emptyState = $('#emptyState');
  const countBadge = $('#countBadge');
  const lastUpdate = $('#lastUpdate');
  const refreshBtn = $('#refreshOrders');

  let pendingOrders = [];
  let userMap = {};
  let receiptConfig = { restaurant_name: 'RESTAURANTE', logo_url: null };

  async function loadReceiptConfig(){
    try{
      const cfg = await api('/api/v1/receipt-config');
      if(cfg){
        receiptConfig.restaurant_name = cfg.restaurant_name || 'RESTAURANTE';
        receiptConfig.logo_url = cfg.logo_url || cfg.logo_path || null;
      }
    }catch(e){}
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
      return `<div style="display:flex;justify-content:center;align-items:center;gap:6px;padding:4px 0;border-bottom:1px dashed #ddd; font-size:10pt;">`+
             `<span style="font-weight:700;">${qty}x</span><span style="flex:1;text-align:left;word-break:break-word;">${short}</span></div>`;
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

  async function loadUsers() {
    try {
      const users = await api('/api/v1/users?limit=100') || [];
      userMap = {};
      users.forEach(u => { userMap[String(u.id)] = u.full_name || u.username; });
    } catch (e) {
      userMap = {};
    }
  }

  function formatMesa(o) {
    const n = o.table_number != null ? o.table_number : o.table_id;
    const v = Number(n);
    if (!Number.isFinite(v)) return esc(String(n));
    return String(v).padStart(2, '0');
  }

  function orderCard(o) {
    const dispNum = o.daily_number || o.id;
    const dispMesa = formatMesa(o);
    const meseroName = esc(userMap[String(o.camarero_id)] || `Mesero #${o.camarero_id || '?'}`);
    const fecha = date(o.created_at);
    const estado = esc(o.status || 'PENDIENTE');
    const itemsRows = (o.items || []).map(it => {
      const qty = Number(it.quantity) || 0;
      const pu = Number(it.unit_price) || 0;
      const sub = qty * pu;
      const nombre = esc(it.dish_name || `Plato #${it.dish_id}`);
      return `<tr><td>${qty}</td><td>${nombre}</td><td>${money(pu)}</td><td>${money(sub)}</td></tr>`;
    }).join('') || '<tr><td colspan="4" style="text-align:center;padding:10px;">Sin platos</td></tr>';
    const subtotal = money(o.total_amount || 0);
    const total = money(o.total_amount || 0);
    const notas = o.notes ? `<div class="muted" style="margin-top:10px;font-size:.84rem;border-top:1px dashed #e6ddd1;padding-top:8px;"><strong>Notas:</strong> ${esc(o.notes)}</div>` : '';
    return `<article class="cajero-card" data-id="${o.id}"><div class="cajero-card__head"><div><h3 class="cajero-card__title">Orden #${esc(String(dispNum))} · Mesa ${dispMesa}</h3><div class="cajero-card__meta">Mesero: <strong>${meseroName}</strong> · ${fecha} · <span class="status status--${estado}">${estado}</span></div></div><span class="status status--${estado}">${estado}</span></div><table class="cajero-items"><thead><tr><th>Cant</th><th>Plato</th><th>P.Unit</th><th>Subtotal</th></tr></thead><tbody>${itemsRows}</tbody></table><div class="cajero-total"><div><div class="muted" style="font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;">Subtotal</div><strong>${subtotal}</strong></div><div style="text-align:right;"><div class="muted" style="font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;">Total</div><strong>${total}</strong></div></div>${notas}<div class="cajero-actions"><button class="btn btn--primary btn--small" data-print="${o.id}">Imprimir</button></div></article>`;
  }

  function render() {
    if (!ordersContainer) return;
    if (!pendingOrders.length) {
      ordersContainer.innerHTML = '';
      if (emptyState) emptyState.hidden = false;
      if (countBadge) countBadge.textContent = '0 pendientes';
      return;
    }
    if (emptyState) emptyState.hidden = true;
    if (countBadge) countBadge.textContent = `${pendingOrders.length} pendiente${pendingOrders.length===1?'':'s'}`;
    ordersContainer.innerHTML = pendingOrders.map(orderCard).join('');
  }

  async function loadPending() {
    try {
      const orders = await api('/api/v1/orders/cajero/pending?limit=100') || [];
      pendingOrders = orders.filter(o => ['PENDIENTE','NUEVO'].includes(o.status)).sort((a,b)=> new Date(a.created_at)- new Date(b.created_at));
      render();
      if (lastUpdate) lastUpdate.textContent = `Actualizado: ${new Date().toLocaleTimeString('es-CO')}`;
    } catch (e) {
      toast(e.message || 'No se pudieron cargar las órdenes', 'error');
    }
  }

  async function handlePrint(orderId){
    const order = pendingOrders.find(o=> String(o.id)===String(orderId));
    if(!order) { toast('Orden no encontrada','error'); return; }
    if(!['PENDIENTE','NUEVO'].includes(order.status)){
      toast('Solo se pueden imprimir órdenes PENDIENTE','error');
      return;
    }
    const ok = printKitchenTicket(order);
    if(!ok){
      toast('La impresión falló. La orden permanece PENDIENTE. Intente nuevamente.', 'error');
      return;
    }
    await new Promise(r=> setTimeout(r, 700));
    try{
      await api(`/api/v1/orders/${order.id}`, { method: 'PUT', body: JSON.stringify({ status: 'EN_COCINA' }) });
      toast(`Orden #${order.daily_number||order.id} enviada a cocina (EN COCINA)`);
      await loadPending();
    }catch(e){
      toast(e.message||'No se pudo actualizar a EN COCINA','error');
    }
  }

  if (ordersContainer) {
    ordersContainer.addEventListener('click', async (e) => {
      const printBtn = e.target.closest('[data-print]');
      if (printBtn){
        const id = printBtn.dataset.print;
        printBtn.disabled = true;
        const orig = printBtn.textContent;
        printBtn.textContent = 'Imprimiendo...';
        await handlePrint(id);
        setTimeout(()=>{ printBtn.disabled=false; printBtn.textContent=orig; }, 1200);
        return;
      }
    });
  }

  if (refreshBtn) refreshBtn.addEventListener('click', () => loadPending().catch(e=>toast(e.message,'error')));

  try {
    await Promise.all([loadUsers(), loadReceiptConfig()]);
    await loadPending();
  } catch (e) {
    toast(e.message,'error');
  }

  setInterval(() => {
    loadPending().catch(()=>{});
    loadUsers().catch(()=>{});
    loadReceiptConfig().catch(()=>{});
  }, 12000);
});
