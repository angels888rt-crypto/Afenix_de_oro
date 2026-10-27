(function () {
  'use strict';

  const API = {
    users: '/api/v1/users',
    dishes: '/api/v1/dishes',
    tables: '/api/v1/tables',
    orders: '/api/v1/orders',
  };

  const role = (localStorage.getItem('afenix_role') || '').toUpperCase();
  const token = localStorage.getItem('afenix_access_token');
  const name = localStorage.getItem('afenix_display_name') || 'Usuario';

  if (!token || !['ADMIN', 'CAMARERO', 'CAJERO', 'MONITOR'].includes(role)) {
    window.location.href = '/secion.html';
    return;
  }

  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => Array.from(c.querySelectorAll(s));
  const money = cents => `$${Math.max(0, Math.round((Number(cents) || 0) / 100)).toLocaleString('es-CO')}`;
  const date = d => d ? new Date(d.endsWith('Z') ? d : d + 'Z').toLocaleString('es-CO') : '—';
  const escapeHtml = v => String(v ?? '').replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[ch]));
  const headers = () => ({'Content-Type':'application/json', Authorization:`Bearer ${token}`});
  const api = async (url, options = {}) => {
    const res = await fetch(url, { ...options, headers: { ...headers(), ...(options.headers || {}) } });
    let payload = null;
    try { payload = await res.json(); } catch (_) {}
    if (res.status === 401) { logout(); throw new Error('Sesión expirada.'); }
    if (!res.ok || payload?.success === false) throw new Error(payload?.message || payload?.detail || 'No se pudo completar la operación.');
    return payload?.data;
  };

  function logout() {
    ['afenix_access_token','afenix_refresh_token','afenix_display_name','afenix_role'].forEach(k => localStorage.removeItem(k));
    window.location.href = '/secion.html';
  }

  const roleNames = { ADMIN:'Administrador', CAMARERO:'Mesero', CAJERO:'Cajero', MONITOR:'Monitor' };
  $('#roleLabel').textContent = `Panel · ${roleNames[role] || role}`;
  $('#userChip').textContent = name;
  $('#welcomeTitle').textContent = `Bienvenido, ${name}`;
  const welcomeText = {
    CAMARERO: 'Crea pedidos y sigue únicamente las órdenes que tú registraste.',
    MONITOR: 'Consulta las órdenes pendientes e imprímelas para enviarlas a cocina.',
  };
  $('#welcomeText').textContent = welcomeText[role]
    || 'Gestiona inventario, usuarios y el historial completo de órdenes.';
  $('#year').textContent = new Date().getFullYear();
  $('#logoutBtn').addEventListener('click', logout);

  const stateLabel = {NUEVO:'Nuevo', EN_COCINA:'En cocina', COMPLETADO:'Completado', ENTREGADO:'Entregado', CANCELADO:'Cancelado'};
  let dishes = [], tables = [], editingUser = null;

  const moduleMap = {
    CAMARERO: [
      { view:'orders', icon:'🧾', title:'Pedidos', text:'Crear pedidos y entregar los que tú creaste.' },
    ],
    ADMIN: [
      { view:'inventory', icon:'📦', title:'Inventario', text:'Actualizar existencias y disponibilidad de platos.' },
      { view:'users', icon:'👤', title:'Usuarios', text:'Gestionar credenciales, roles y estado de cuentas.' },
      { view:'history', icon:'📚', title:'Historial', text:'Consultar todas las órdenes registradas.' },
    ],
    CAJERO: [
      { view:'orders', icon:'💰', title:'Caja', text:'Estructura preparada para futuras funciones de caja.' },
    ],
    MONITOR: [
      { href:'/monitor-ordenes.html', icon:'🍳', title:'Órdenes de cocina', text:'Visualiza e imprime las órdenes pendientes por mesa.' },
    ],
  };

  const grid = $('#moduleGrid');
  (moduleMap[role] || []).forEach(module => {
    const card = document.createElement(module.href ? 'a' : 'button');
    card.className = 'module-btn';
    if (module.href) card.href = module.href;
    else {
      card.type = 'button';
      card.addEventListener('click', () => showView(module.view));
    }
    card.innerHTML = `<span class="module-btn__icon">${module.icon}</span><h3>${module.title}</h3><p>${module.text}</p>`;
    grid.appendChild(card);
  });

  function showView(view) {
    $$('.app-section').forEach(s => { s.hidden = true; });
    const target = $(`#view-${view}`);
    if (!target) return;
    target.hidden = false;
    target.scrollIntoView({behavior:'smooth', block:'start'});
    loadView(view).catch(err => toast(err.message, 'error'));
  }

  async function loadView(view) {
    if (view === 'orders') await Promise.all([loadDishes(), loadTables(), loadMyOrders()]);
    if (view === 'inventory') await loadInventory();
    if (view === 'users') await loadUsers();
    if (view === 'history') await loadHistory();
  }

  function toast(msg, type = 'ok') {
    const el = $('#toast'); el.textContent = msg; el.className = `toast is-visible`;
    if (type === 'error') el.style.background = '#7a0c12'; else el.style.background = '#1a1614';
    setTimeout(() => el.classList.remove('is-visible'), 2600);
  }

  function message(el, text, ok = false) {
    el.hidden = !text; el.textContent = text; el.className = `form-message ${ok ? 'form-message--ok' : 'form-message--error'}`;
  }

  function orderCard(o, {showDeliver=false, showComplete=false} = {}) {
    const items = (o.items || []).map(i => `<li>${i.quantity} × plato #${escapeHtml(i.dish_id)}${i.special_notes ? ` — ${escapeHtml(i.special_notes)}` : ''}</li>`).join('');
    const dispNum = o.daily_number || o.id;
    const dispMesa = o.table_number != null ? o.table_number : o.table_id;
    return `<article class="order-card"><div class="order-card__top"><div><span class="order-card__title">Pedido #${dispNum} · Mesa ${dispMesa}</span><div><small>${date(o.created_at)}</small></div></div><span class="status status--${escapeHtml(o.status)}">${stateLabel[o.status] || o.status}</span></div><ul class="order-card__items">${items}</ul><div class="order-card__actions">${showComplete && ['NUEVO','EN_COCINA'].includes(o.status) ? `<button class="btn btn--primary btn--small" data-complete="${o.id}">Marcar COMPLETADO</button>`:''}${showDeliver && o.status === 'COMPLETADO' ? `<button class="btn btn--primary btn--small" data-deliver="${o.id}">Marcar ENTREGADO</button>`:''}</div></article>`;
  }

  async function loadDishes() {
    dishes = await api(`${API.dishes}?limit=100`);
    dishes = dishes || [];
    renderDishPicker();
  }

  async function loadTables() {
    tables = await api(`${API.tables}?limit=100`);
    const select = $('#orderTable');
    select.innerHTML = (tables || []).filter(t => t.status !== 'RESERVADA').map(t => `<option value="${t.id}">Mesa ${t.table_number} · ${t.capacity} personas · ${t.status}</option>`).join('');
  }

  function renderDishPicker() {
    $('#dishPicker').innerHTML = (dishes || []).filter(d => d.is_available).map(d => `<article class="dish-card"><div class="dish-card__top"><div><h4>${escapeHtml(d.name)}</h4><small>${money(d.price)} · ${d.is_available ? 'Disponible' : 'Agotado'}</small></div></div><div class="dish-card__controls"><label class="field-block"><span>Cantidad</span><input class="qty" type="number" min="0" value="0" data-dish-id="${d.id}" ${d.is_available ? '' : 'disabled'}></label><span></span></div></article>`).join('') || '<p>No hay platos disponibles.</p>';
    $$('.qty', $('#dishPicker')).forEach(i => i.addEventListener('input', updateOrderTotal));
    updateOrderTotal();
  }

  function updateOrderTotal() {
    let total = 0;
    $$('.qty', $('#dishPicker')).forEach(input => {
      const d = dishes.find(x => String(x.id) === String(input.dataset.dishId));
      total += (Number(input.value) || 0) * (Number(d?.price) || 0);
    });
    $('#orderTotal').textContent = money(total);
  }

  $('#orderForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const items = $$('.qty', $('#dishPicker')).map(i => ({dish_id:Number(i.dataset.dishId), quantity:Number(i.value)})).filter(i => i.quantity > 0);
    if (!items.length) { message($('#orderMessage'), 'Selecciona al menos un plato.'); return; }
    try {
      await api(API.orders, {method:'POST', body:JSON.stringify({table_id:Number($('#orderTable').value), items, notes:$('#orderNotes').value.trim() || null})});
      message($('#orderMessage'), 'Pedido creado y enviado a cocina.', true); $('#orderForm').reset(); renderDishPicker();
      await Promise.all([loadDishes(), loadMyOrders()]); toast('Pedido creado correctamente.');
    } catch (err) { message($('#orderMessage'), err.message); }
  });

  async function loadMyOrders() {
    let orders = await api(`${API.orders}/mine?limit=100`) || [];
    orders = orders.filter(o => o.status !== 'ENTREGADO');
    orders.sort((a,b) => (a.status === 'COMPLETADO' ? 0 : 1) - (b.status === 'COMPLETADO' ? 0 : 1) || new Date(b.created_at) - new Date(a.created_at));
    $('#myOrdersList').innerHTML = orders.map(o => orderCard(o, {showDeliver:true})).join('') || '<p>No tienes pedidos creados todavía.</p>';
  }

  $('#refreshMyOrders')?.addEventListener('click', () => loadMyOrders().catch(e => toast(e.message,'error')));
  $('#myOrdersList')?.addEventListener('click', async e => { const btn=e.target.closest('[data-deliver]'); if(!btn) return; try { await api(`${API.orders}/${btn.dataset.deliver}`, {method:'PUT', body:JSON.stringify({status:'ENTREGADO'})}); toast('Pedido marcado como ENTREGADO.'); await loadMyOrders(); } catch(err) { toast(err.message,'error'); } });

  async function loadInventory() {
    const list = await api(`${API.dishes}?limit=100`);
    $('#inventoryList').innerHTML = (list || []).map(d => `<article class="inventory-card"><h3>${escapeHtml(d.name)}</h3><p>${escapeHtml(d.category)} · ${money(d.price)}</p><div class="inventory-card__meta"><strong>${d.is_available ? 'Disponible' : 'Agotado'}</strong><span>${d.is_available ? '🟢' : '🔴'}</span></div><div class="inventory-card__actions"><button class="btn btn--ghost btn--small" data-toggle="${d.id}">${d.is_available ? 'Marcar Agotado' : 'Marcar Disponible'}</button></div></article>`).join('') || '<p>No hay platos registrados.</p>';
  }
  $('#refreshInventory')?.addEventListener('click', () => loadInventory().catch(e => toast(e.message,'error')));
  $('#inventoryList')?.addEventListener('click', async e => { const b=e.target.closest('[data-toggle]'); if(!b) return; const id=b.dataset.toggle; const dish = await api(`${API.dishes}/${id}`); const next = !dish.is_available; try { await api(`${API.dishes}/${id}`,{method:'PUT',body:JSON.stringify({is_available: next})}); await loadInventory(); toast(next ? 'Disponible' : 'Agotado'); } catch(err){toast(err.message,'error');} });

  async function loadUsers() {
    const users = await api(`${API.users}?limit=100`);
    $('#usersTable').innerHTML = (users || []).map(u => `<tr><td>${escapeHtml(u.full_name)}</td><td>@${escapeHtml(u.username)}</td><td>${escapeHtml(roleNames[u.role] || u.role)}</td><td>${u.is_active ? 'Activo' : 'Inactivo'}</td><td><button class="btn btn--primary btn--small" data-edit-user="${u.id}">Editar</button></td></tr>`).join('') || '<tr><td colspan="5">No hay usuarios.</td></tr>';
    window.__afenixUsers = users || [];
  }

  function startUserEdit(id) {
    const u = (window.__afenixUsers || []).find(x => String(x.id) === String(id)); if(!u) return;
    editingUser = u;
    $('#userId').value = u.id; $('#userFullName').value = u.full_name; $('#userUsername').value = u.username; $('#userPassword').value = ''; $('#userRole').value = u.role; $('#userPhone').value = u.phone || ''; $('#userActive').value = String(u.is_active);
    $('#userFormTitle').textContent = 'Editar usuario'; $('#saveUserBtn').textContent = 'Guardar cambios'; $('#cancelUserEdit').hidden = false; $('#userForm').classList.add('is-editing'); $('#userFullName').focus(); $('#userForm').scrollIntoView({behavior:'smooth',block:'start'});
  }
  $('#usersTable')?.addEventListener('click', e => { const b=e.target.closest('[data-edit-user]'); if(b) startUserEdit(b.dataset.editUser); });
  $('#cancelUserEdit')?.addEventListener('click', resetUserForm);
  function resetUserForm(){editingUser=null; $('#userForm').reset(); $('#userId').value=''; $('#userFormTitle').textContent='Registrar usuario'; $('#saveUserBtn').textContent='Registrar usuario'; $('#cancelUserEdit').hidden=true; $('#userForm').classList.remove('is-editing');}
  $('#userForm')?.addEventListener('submit', async e => { e.preventDefault(); const data={username:$('#userUsername').value.trim(), full_name:$('#userFullName').value.trim(), role:$('#userRole').value, is_active:$('#userActive').value === 'true', phone:$('#userPhone').value.trim() || null}; const pass=$('#userPassword').value; if(!editingUser && pass.length<8){message($('#userMessage'),'La contraseña debe tener al menos 8 caracteres.');return;} if(pass) data.password=pass; try { if(editingUser) await api(`${API.users}/${editingUser.id}/admin`,{method:'PUT',body:JSON.stringify(data)}); else await api(`${API.users}/register`,{method:'POST',body:JSON.stringify({...data,password:pass})}); message($('#userMessage'), editingUser ? 'Usuario actualizado.' : 'Usuario registrado.', true); resetUserForm(); await loadUsers(); toast('Operación de usuario completada.'); } catch(err){message($('#userMessage'),err.message);} });
  $('#refreshUsers')?.addEventListener('click', () => loadUsers().catch(e => toast(e.message,'error')));

  async function loadHistory() {
    let [orders, users] = await Promise.all([
      api(`${API.orders}/history?limit=100`).then(r => r || []),
      window.__afenixUsers && window.__afenixUsers.length ? window.__afenixUsers : api(`${API.users}?limit=100`).then(r => r || [])
    ]);
    const userMap = {};
    for (const u of users) userMap[u.id] = u.full_name;
    orders.sort((a,b) => new Date(b.created_at) - new Date(a.created_at));
    $('#historyTable').innerHTML = orders.map(o => `<tr><td>#${o.id}</td><td>${o.table_id}</td><td>${escapeHtml(userMap[o.camarero_id] || '—')}</td><td><span class="status status--${escapeHtml(o.status)}">${stateLabel[o.status] || o.status}</span></td><td>${money(o.total_amount)}</td><td>${date(o.created_at)}</td><td>${date(o.delivered_at)}</td></tr>`).join('') || '<tr><td colspan="7">No hay órdenes registradas.</td></tr>';
  }
  $('#refreshHistory')?.addEventListener('click', () => loadHistory().catch(e => toast(e.message,'error')));

  showView(moduleMap[role][0].view);
})();
