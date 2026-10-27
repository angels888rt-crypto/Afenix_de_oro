document.addEventListener('DOMContentLoaded', async () => {
  if (!Afenix.guardPage('CAJERO')) return;
  const $ = s => document.querySelector(s);
  const { api, toast, esc, money, date } = Afenix;

  const ordersContainer = $('#orders');
  const emptyState = $('#emptyState');
  const countBadge = $('#countBadge');
  const lastUpdate = $('#lastUpdate');
  const refreshBtn = $('#refreshOrders');
  const modal = $('#confirmModal');
  const closeConfirm = $('#closeConfirm');
  const cancelConfirm = $('#cancelConfirm');
  const acceptConfirm = $('#acceptConfirm');
  const confirmMessage = $('#confirmMessage');

  let entregados = [];
  let pendingPayId = null;
  let userMap = {};

  async function loadUsers() {
    try {
      const users = await api('/api/v1/users?limit=100') || [];
      userMap = {};
      users.forEach(u => { userMap[String(u.id)] = u.full_name || u.username; });
    } catch (e) { userMap = {}; }
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
    const estado = esc(o.status || 'ENTREGADO');
    const itemsRows = (o.items || []).map(it => {
      const qty = Number(it.quantity) || 0;
      const pu = Number(it.unit_price) || 0;
      const sub = qty * pu;
      const nombre = esc(it.dish_name || `Plato #${it.dish_id}`);
      return `<tr><td>${qty}</td><td>${nombre}</td><td>${money(pu)}</td><td>${money(sub)}</td></tr>`;
    }).join('') || '<tr><td colspan="4" style="text-align:center;padding:10px;">Sin platos</td></tr>';
    const total = money(o.total_amount || 0);
    const notas = o.notes ? `<div class="muted" style="margin-top:10px;font-size:.84rem;border-top:1px dashed #e6ddd1;padding-top:8px;"><strong>Notas:</strong> ${esc(o.notes)}</div>` : '';
    return `<article class="cajero-card" data-id="${o.id}"><div class="cajero-card__head"><div><h3 class="cajero-card__title">Orden #${esc(String(dispNum))} · Mesa ${dispMesa}</h3><div class="cajero-card__meta">Mesero: <strong>${meseroName}</strong> · ${fecha} · <span class="status status--${estado}">${estado}</span></div></div><span class="status status--${estado}">${estado}</span></div><table class="cajero-items"><thead><tr><th>Cant</th><th>Plato</th><th>P.Unit</th><th>Subtotal</th></tr></thead><tbody>${itemsRows}</tbody></table><div class="cajero-total"><div><div class="muted" style="font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;">Total</div><strong>${total}</strong></div></div>${notas}<div class="cajero-actions"><button class="btn btn--primary btn--small" data-pay="${o.id}">Marcar como pagado</button></div></article>`;
  }

  function render() {
    if (!ordersContainer) return;
    if (!entregados.length) {
      ordersContainer.innerHTML = '';
      if (emptyState) emptyState.hidden = false;
      if (countBadge) countBadge.textContent = '0 entregados';
      return;
    }
    if (emptyState) emptyState.hidden = true;
    if (countBadge) countBadge.textContent = `${entregados.length} entregado${entregados.length===1?'':'s'}`;
    ordersContainer.innerHTML = entregados.map(orderCard).join('');
  }

  async function loadEntregados() {
    try {
      const orders = await api('/api/v1/orders/cajero/entregados?limit=100') || [];
      entregados = orders.filter(o => o.status === 'ENTREGADO').sort((a,b)=> new Date(a.created_at)- new Date(b.created_at));
      render();
      if (lastUpdate) lastUpdate.textContent = `Actualizado: ${new Date().toLocaleTimeString('es-CO')}`;
    } catch (e) {
      toast(e.message || 'No se pudieron cargar entregados', 'error');
    }
  }

  function openModal(orderId) {
    pendingPayId = orderId;
    const order = entregados.find(o => String(o.id)===String(orderId));
    const dispNum = order ? (order.daily_number || order.id) : orderId;
    if (confirmMessage) confirmMessage.textContent = `¿Está seguro de que desea marcar la Orden #${dispNum} como pagada?`;
    if (modal) { modal.hidden = false; document.body.classList.add('modal-open'); }
  }
  function closeModal() {
    if (modal) { modal.hidden = true; document.body.classList.remove('modal-open'); }
    pendingPayId = null;
  }

  if (ordersContainer) {
    ordersContainer.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-pay]');
      if (!btn) return;
      openModal(btn.dataset.pay);
    });
  }

  if (closeConfirm) closeConfirm.addEventListener('click', closeModal);
  if (cancelConfirm) cancelConfirm.addEventListener('click', closeModal);
  if (modal) modal.addEventListener('click', (e)=>{ if(e.target===modal) closeModal(); });
  document.addEventListener('keydown', (e)=>{ if(e.key==='Escape' && modal && !modal.hidden) closeModal(); });

  if (acceptConfirm) {
    acceptConfirm.addEventListener('click', async () => {
      if (!pendingPayId) return;
      const id = pendingPayId;
      acceptConfirm.disabled = true;
      acceptConfirm.textContent = 'Procesando...';
      try {
        await api(`/api/v1/orders/${id}`, { method: 'PUT', body: JSON.stringify({ status: 'PAGADO' }) });
        toast('Orden marcada como PAGADO');
        closeModal();
        await loadEntregados();
      } catch (e) {
        toast(e.message || 'No se pudo marcar como pagado', 'error');
      } finally {
        acceptConfirm.disabled = false;
        acceptConfirm.textContent = 'Confirmar pago';
      }
    });
  }

  if (refreshBtn) refreshBtn.addEventListener('click', () => loadEntregados().catch(e=>toast(e.message,'error')));

  try {
    await loadUsers();
    await loadEntregados();
  } catch (e) { toast(e.message,'error'); }

  setInterval(() => { loadEntregados().catch(()=>{}); loadUsers().catch(()=>{}); }, 12000);
});
