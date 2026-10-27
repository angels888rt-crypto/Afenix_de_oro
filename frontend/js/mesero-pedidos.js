document.addEventListener('DOMContentLoaded', async () => {
  if (!Afenix.guardPage('CAMARERO')) return;
  const $ = s => document.querySelector(s);
  const { api, toast, esc, date, money } = Afenix;
  const states = { PENDIENTE: 'Pendiente', NUEVO: 'Pendiente', EN_COCINA: 'En cocina', COMPLETADO: 'En cocina', ENTREGADO: 'Entregado', CANCELADO: 'Cancelado', PAGADO: 'Pagado' };
  let allOrders = [];
  let allDishes = [];
  let selectedMesa = 'all';
  let editingOrderId = null;

  const editModal = $('#editOrderModal');
  const editOrderNum = $('#editOrderNum');
  const editNotes = $('#editNotes');
  const editDishes = $('#editDishes');
  const editMsg = $('#editOrderMsg');
  const closeEditBtn = $('#closeEditModal');
  const cancelEditBtn = $('#cancelEditOrder');
  const saveEditBtn = $('#saveEditOrder');

  function setEditMsg(t, ok=false){
    if(!editMsg) return;
    editMsg.hidden = !t;
    editMsg.textContent = t;
    editMsg.className = 'form-message' + (ok ? ' ok' : '');
  }

  function isPending(o){ return o.status === 'PENDIENTE' || o.status === 'NUEVO'; }
  function isEnCocina(o){ return o.status === 'EN_COCINA' || o.status === 'COMPLETADO'; }
  function isEntregado(o){ return o.status === 'ENTREGADO'; }

  function card(o) {
    const items = (o.items || []).map(i => `<li><strong>${i.quantity} × ${esc(i.dish_name || `Plato #${i.dish_id}`)}</strong> ${money ? `· ${money(i.unit_price)}` : ''}${i.special_notes ? ` - ${esc(i.special_notes)}` : ''}</li>`).join('');
    let actions = '';
    if (isPending(o)){
      actions = `<button class="btn btn--ghost btn--small" data-edit="${o.id}">Editar</button><button class="btn btn--danger btn--small" data-cancel="${o.id}">Cancelar</button>`;
    } else if (isEnCocina(o)){
      actions = `<button class="btn btn--primary btn--small" data-deliver="${o.id}">Entregado</button><button class="btn btn--danger btn--small" data-cancel="${o.id}">Cancelar</button>`;
    } else if (isEntregado(o)){
      actions = `<span class="muted" style="font-size:.82rem;align-self:center;">En espera de pago en caja</span>`;
    } else if (o.status === 'PAGADO'){
      actions = `<span class="muted" style="font-size:.82rem;align-self:center;">Pagado · Finalizado</span>`;
    } else if (o.status === 'CANCELADO'){
      actions = `<span class="muted" style="font-size:.82rem;align-self:center;color:#7a2c2c;">Cancelado · Inactivo</span>`;
    } else {
      actions = `<span class="muted" style="font-size:.82rem;align-self:center;">${esc(o.status)}</span>`;
    }
    const dispNum = o.daily_number || o.id;
    const dispMesa = o.table_number != null ? o.table_number : o.table_id;
    const statusLabel = states[o.status] || esc(o.status);
    const statusClass = esc(o.status);
    return `<article class="order-card"><div class="order-card__top"><div><span class="order-card__title">Pedido #${dispNum} · Mesa ${dispMesa}</span><div class="muted">${date(o.created_at)} · Total ${money(o.total_amount)}</div></div><span class="status status--${statusClass}">${statusLabel}</span></div><ul class="order-card__items">${items}</ul>${o.notes ? `<div class="muted" style="font-size:.84rem;margin-bottom:8px;"><strong>Notas:</strong> ${esc(o.notes)}</div>` : ''}<div class="order-card__actions">${actions}</div></article>`;
  }

  function getMesa(o) {
    return o.table_number != null ? String(o.table_number) : String(o.table_id);
  }

  function renderFilter() {
    const sel = $('#filterMesa');
    if (!sel) return;
    const mesas = [...new Set(allOrders.map(o => getMesa(o)))].filter(Boolean).sort((a, b) => Number(a) - Number(b));
    const prev = sel.value;
    sel.innerHTML = '<option value="all">Todas las mesas</option>' + mesas.map(m => `<option value="${esc(m)}">Mesa ${esc(m)}</option>`).join('');
    if (mesas.includes(prev) || prev === 'all') sel.value = prev;
    else sel.value = 'all';
    selectedMesa = sel.value;
  }

  function getFiltered() {
    if (selectedMesa === 'all') return allOrders;
    return allOrders.filter(o => getMesa(o) === String(selectedMesa));
  }

  function renderOrders() {
    const filtered = getFiltered();
    $('#orders').innerHTML = filtered.map(card).join('') || '<p class="muted">No tienes pedidos activos.</p>';
  }

  async function loadDishes() {
    try {
      const dishes = await api('/api/v1/dishes?limit=100') || [];
      allDishes = dishes;
    } catch(e){
      allDishes = [];
    }
  }

  async function loadOrders() {
    let orders = await api('/api/v1/orders/mine?limit=100') || [];
    orders = orders.filter(o => !['PAGADO','CANCELADO','ENTREGADO'].includes(o.status));
    const prio = s => isPending({status:s}) ? 0 : isEnCocina({status:s}) ? 1 : 2;
    orders.sort((a, b) => prio(a.status) - prio(b.status) || new Date(b.created_at) - new Date(a.created_at));
    allOrders = orders;
    renderFilter();
    renderOrders();
  }

  function openEdit(orderId){
    const o = allOrders.find(x=> String(x.id)===String(orderId));
    if(!o) return;
    if(!isPending(o)){
      toast('Solo se pueden editar pedidos PENDIENTE','error');
      return;
    }
    editingOrderId = o.id;
    if(editOrderNum) editOrderNum.textContent = o.daily_number || o.id;
    if(editNotes) editNotes.value = o.notes || '';
    setEditMsg('');
    const qtyMap = {};
    (o.items||[]).forEach(it=>{ qtyMap[String(it.dish_id)] = Number(it.quantity)||0; });
    if(editDishes){
      editDishes.innerHTML = allDishes.map(d=>{
        const disponible = !!d.is_available;
        const curQty = qtyMap[String(d.id)] || 0;
        const disabled = !disponible && curQty===0 ? 'disabled' : '';
        const badge = disponible ? '<span style="font-size:.68rem;font-weight:700;color:#246126;background:#eaf6e9;padding:2px 6px;border-radius:999px;">🟢 Disponible</span>' : '<span style="font-size:.68rem;font-weight:700;color:#8a2925;background:#f6e5e4;padding:2px 6px;border-radius:999px;">🔴 Agotado</span>';
        const img = d.image_url||d.image_path||'';
        const imgHtml = img ? `<img src="${esc(img)}" alt="${esc(d.name)}" style="width:100%;height:80px;object-fit:cover;border-radius:8px;border:1px solid var(--line);${disponible?'':'opacity:.6;filter:grayscale(.6)'}">` : `<div style="height:80px;display:grid;place-items:center;background:#f6f1e7;border:1px solid var(--line);border-radius:8px;color:var(--muted);font-size:.78rem;">Sin imagen</div>`;
        return `<article class="inventory-card" style="padding:12px;${!disponible && curQty===0 ? 'opacity:.75':''}"><div style="margin-bottom:8px;">${imgHtml}</div><h4 style="margin:0 0 4px;font-family:Cinzel,serif;font-size:.9rem;">${esc(d.name)}</h4><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;"><span class="muted" style="font-size:.8rem;">${money(d.price)}</span>${badge}</div><div class="field"><label for="eq${d.id}" style="font-size:.78rem;">Cantidad</label><input id="eq${d.id}" data-dish="${d.id}" type="number" min="0" value="${curQty||''}" placeholder="${disponible?'0':'Agotado'}" ${disabled} style="${!disponible && curQty===0 ? 'background:#f3e9e9;cursor:not-allowed;':''}"></div></article>`;
      }).join('') || '<p class="muted">No hay platos disponibles.</p>';
    }
    if(editModal){ editModal.hidden=false; document.body.classList.add('modal-open'); }
  }
  function closeEdit(){
    if(editModal){ editModal.hidden=true; document.body.classList.remove('modal-open'); }
    editingOrderId=null;
    setEditMsg('');
  }

  const filterSel = $('#filterMesa');
  if (filterSel) {
    filterSel.addEventListener('change', (e) => {
      selectedMesa = e.target.value;
      renderOrders();
    });
  }

  $('#orders').addEventListener('click', async e => {
    const editBtn = e.target.closest('[data-edit]');
    if(editBtn){
      e.preventDefault();
      await loadDishes();
      openEdit(editBtn.dataset.edit);
      return;
    }
    const cancelBtn = e.target.closest('[data-cancel]');
    if(cancelBtn){
      const id = cancelBtn.dataset.cancel;
      const order = allOrders.find(x=> String(x.id)===String(id));
      const dispNum = order ? (order.daily_number||order.id) : id;
      if(!confirm(`¿Está seguro de que desea CANCELAR la Orden #${dispNum}?\n\nEsta acción no se puede deshacer. La orden quedará inactiva y no generará venta.`)){
        return;
      }
      try{
        await api(`/api/v1/orders/${id}`, { method: 'PUT', body: JSON.stringify({ status: 'CANCELADO' }) });
        toast('Orden cancelada correctamente');
        await loadOrders();
      }catch(err){
        toast(err.message||'No se pudo cancelar','error');
      }
      return;
    }
    const b = e.target.closest('[data-deliver]');
    if (!b) return;
    const id = b.dataset.deliver;
    const order = allOrders.find(x=> String(x.id)===String(id));
    const dispNum = order ? (order.daily_number||order.id) : id;
    if(!confirm(`¿Confirmar que la Orden #${dispNum} fue ENTREGADA al cliente?`)){
      return;
    }
    try {
      await api(`/api/v1/orders/${b.dataset.deliver}`, { method: 'PUT', body: JSON.stringify({ status: 'ENTREGADO' }) });
      toast('Pedido marcado como ENTREGADO');
      await loadOrders();
    } catch (e) {
      toast(e.message, 'error');
    }
  });

  $('#refreshOrders').addEventListener('click', () => loadOrders().catch(e => toast(e.message, 'error')));

  if(closeEditBtn) closeEditBtn.addEventListener('click', closeEdit);
  if(cancelEditBtn) cancelEditBtn.addEventListener('click', closeEdit);
  if(editModal) editModal.addEventListener('click', e=>{ if(e.target===editModal) closeEdit(); });
  document.addEventListener('keydown', e=>{ if(e.key==='Escape' && editModal && !editModal.hidden) closeEdit(); });

  if(saveEditBtn){
    saveEditBtn.addEventListener('click', async ()=>{
      if(!editingOrderId) return;
      setEditMsg('');
      const items = Array.from(document.querySelectorAll('#editDishes [data-dish]')).map(inp=>{
        const dishId = Number(inp.dataset.dish);
        const qty = Number(inp.value) || 0;
        return { dish_id: dishId, quantity: qty };
      }).filter(x=> x.quantity>0);
      if(!items.length){
        setEditMsg('Debes mantener al menos un plato');
        return;
      }
      saveEditBtn.disabled=true;
      saveEditBtn.textContent='Guardando...';
      try{
        await api(`/api/v1/orders/${editingOrderId}/edit`, { method:'PUT', body: JSON.stringify({ items, notes: (editNotes.value||'').trim()||null }) });
        toast('Pedido actualizado');
        closeEdit();
        await loadOrders();
      }catch(err){
        setEditMsg(err.message);
        toast(err.message,'error');
      } finally {
        saveEditBtn.disabled=false;
        saveEditBtn.textContent='Guardar cambios';
      }
    });
  }

  setInterval(()=>{ loadOrders().catch(()=>{}); }, 15000);

  try {
    await Promise.all([loadDishes(), loadOrders()]);
  } catch (e) {
    toast(e.message, 'error');
  }
});
