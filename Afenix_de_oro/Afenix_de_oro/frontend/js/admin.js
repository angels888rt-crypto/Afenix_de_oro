/* ============================================================
   AFENIX DE ORO — Panel de administración · Lógica principal
   Secciones:
   1. Utilidades + API helpers
   2. Header con scroll
   3. Menú hamburguesa
   4. Carga de datos desde el backend (platos, órdenes, usuarios)
   5. Inventario: render, estado de stock, filtros, búsqueda y ajuste
   6. Meseros y órdenes: render agrupado por mesero
   7. Resumen del panel (contadores)
   8. Inicialización
============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  /* --------------------------------------------------------
     0. CONTROL DE ACCESO — Solo administradores
  -------------------------------------------------------- */
  const storedRole = (localStorage.getItem('afenix_role') || '').toUpperCase();
  const storedToken = localStorage.getItem('afenix_access_token');
  if (!storedToken || storedRole !== 'ADMIN') {
    window.location.href = '/';
    return;
  }

  /* --------------------------------------------------------
     1. UTILIDADES + API HELPERS
  -------------------------------------------------------- */
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const yearEl = $('#year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  const logoutItem = $('#logoutItem');
  const logoutBtn  = $('#logoutBtn');
  if (logoutItem) logoutItem.hidden = false;
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      localStorage.removeItem('afenix_access_token');
      localStorage.removeItem('afenix_refresh_token');
      localStorage.removeItem('afenix_role');
      localStorage.removeItem('afenix_display_name');
      window.location.href = '/';
    });
  }

  const API = {
    DISHES: '/api/v1/dishes',
    ORDERS: '/api/v1/orders',
    USERS:  '/api/v1/users',
  };

  const authHeaders = (extra = {}) => {
    const token = localStorage.getItem('afenix_access_token');
    return { 'Content-Type': 'application/json', ...extra,
             ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  };

  const centsToDisplay = (cents) => Math.max(1, Math.round((cents || 0) / 100));

  const normalizeDish = (d) => ({
    id:            String(d.id),
    name:          d.name,
    price:         centsToDisplay(d.price),
    is_available:  !!d.is_available,
    stock:         d.is_available ? 1 : 0,
    img:           '',
    category:      d.category     || '',
    description:   d.description  || '',
    estimatedTime: d.estimated_time ? Math.round(d.estimated_time / 60) : 15,
  });

  const mapStatus = (s) => {
    const map = { NUEVO: 'pendiente', EN_COCINA: 'preparando',
                  COMPLETADO: 'servido', ENTREGADO: 'servido', CANCELADO: 'servido' };
    return map[s] || 'pendiente';
  };

  const dishNameById = (id) => {
    const dish = inventory.find((d) => d.id === id);
    return dish ? dish.name : `Plato #${id}`;
  };

  /* --------------------------------------------------------
     2. HEADER — cambia de estilo al hacer scroll
  -------------------------------------------------------- */
  const header = $('#header');
  if (header) {
    const onScrollHeader = () => header.classList.toggle('is-scrolled', window.scrollY > 60);
    onScrollHeader();
    window.addEventListener('scroll', onScrollHeader, { passive: true });
  }

  /* --------------------------------------------------------
     3. MENÚ HAMBURGUESA (móvil)
  -------------------------------------------------------- */
  const navToggle = $('#navToggle');
  const nav       = $('#primaryNav');

  if (navToggle && nav) {
    const closeMenu = () => {
      nav.classList.remove('is-open');
      navToggle.classList.remove('is-open');
      navToggle.setAttribute('aria-expanded', 'false');
      navToggle.setAttribute('aria-label', 'Abrir menú');
    };
    navToggle.addEventListener('click', () => {
      const isOpen = nav.classList.toggle('is-open');
      navToggle.classList.toggle('is-open', isOpen);
      navToggle.setAttribute('aria-expanded', String(isOpen));
      navToggle.setAttribute('aria-label', isOpen ? 'Cerrar menú' : 'Abrir menú');
    });
    $$('.nav__link').forEach((link) => link.addEventListener('click', closeMenu));
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeMenu(); });
  }

  /* --------------------------------------------------------
     4. DATOS — cargados desde el backend con fallback local
  -------------------------------------------------------- */
  const STOCK_MAX     = 1;

  const fallbackInventory = [
    { id: 'd1', name: 'Xiao Long Bao',    price: 12, stock: 1, is_available: true, img: '' },
    { id: 'd2', name: 'Pato Pekín',       price: 28, stock: 1, is_available: true,  img: '' },
    { id: 'd3', name: 'Kung Pao',         price: 16, stock: 0, is_available: false,  img: '' },
    { id: 'd4', name: 'Fideos Lamian',    price: 14, stock: 1, is_available: true, img: '' },
    { id: 'd5', name: 'Arroz Yangzhou',   price: 11, stock: 1, is_available: true,  img: '' },
    { id: 'd6', name: 'Wontons picantes', price: 10, stock: 0, is_available: false,  img: '' },
  ];

  const fallbackWaiters = [
    {
      id: 'w1', name: 'Mesero Demo', role: 'Mesa · conexión local',
      orders: [{ table: 4, status: 'preparando', items: [{ name: 'Xiao Long Bao', qty: 2 }] }],
    },
  ];

  let inventory = [];
  let waiters   = [];

  async function loadDashboardData() {
    const token = localStorage.getItem('afenix_access_token');

    if (!token) {
      inventory = fallbackInventory;
      waiters   = fallbackWaiters;
      initUI();
      return;
    }

    try {
      const [dishRes, orderRes, userRes] = await Promise.all([
        fetch(`${API.DISHES}?limit=100`, { headers: authHeaders() }),
        fetch(`${API.ORDERS}?limit=100`, { headers: authHeaders() }),
        fetch(`${API.USERS}?limit=100`,  { headers: authHeaders() }),
      ]);

      if (!dishRes.ok || !orderRes.ok) throw new Error('API error');

      const dishPayload  = await dishRes.json();
      const orderPayload = await orderRes.json();

      inventory = (dishPayload.data || []).map(normalizeDish);
      if (!inventory.length) inventory = fallbackInventory;

      // Construye mapa de usuarios (id → datos)
      const userMap = {};
      if (userRes.ok) {
        const userPayload = await userRes.json();
        (userPayload.data || []).forEach((u) => {
          userMap[String(u.id)] = {
            id:   String(u.id),
            name: u.full_name || u.username,
            role: u.role === 'ADMIN' ? 'Administrador' : 'Mesero',
          };
        });
      }

      // Agrupa órdenes por camarero_id
      const byWaiter = {};
      (orderPayload.data || []).forEach((o) => {
        const wId = o.camarero_id ? String(o.camarero_id) : 'unknown';
        if (!byWaiter[wId]) {
          byWaiter[wId] = userMap[wId]
            ? { ...userMap[wId], orders: [] }
            : { id: wId, name: `Mesero #${wId}`, role: 'Mesero', orders: [] };
        }
        byWaiter[wId].orders.push({
          table:  o.table_id || 1,
          status: mapStatus(o.status),
          items:  (o.items || []).map((it) => ({
            name: dishNameById(String(it.dish_id)),
            qty:  it.quantity || 1,
          })),
        });
      });

      waiters = Object.values(byWaiter);
      if (!waiters.length) waiters = fallbackWaiters;

    } catch (err) {
      console.warn('No se pudo cargar el panel desde la API:', err);
      inventory = fallbackInventory;
      waiters   = fallbackWaiters;
    }

    initUI();
  }

  /* --------------------------------------------------------
     5. INVENTARIO — render, filtros, búsqueda y ajuste de stock
  -------------------------------------------------------- */
  const grid        = $('#inventoryGrid');
  const emptyMsg    = $('#inventoryEmpty');
  const searchInput = $('#inventorySearch');
  const filterBtns  = $$('.chip');

  let currentFilter = 'todos';
  let currentSearch = '';

  const getState = (stockOrAvailable) => {
    // stock is 1/0 derived from is_available; keep compat with is_available bool
    const available = typeof stockOrAvailable === 'boolean' ? stockOrAvailable : stockOrAvailable > 0;
    return available ? 'disponible' : 'agotado';
  };

  const stateLabel = { disponible: 'Disponible', pocas: 'Pocas unidades', agotado: 'Agotado' };

  const itemTemplate = (dish) => {
    const available = dish.is_available ?? dish.stock > 0;
    const state     = getState(available);
    const pct       = available ? 100 : 0;
    const stockText = state === 'agotado' ? 'Agotado' : 'Disponible';
    return `
      <article class="item" data-id="${dish.id}" data-name="${dish.name.toLowerCase()}" data-state="${state}">
        <div class="item__media">
          <span class="item__badge item__badge--${state}">${stateLabel[state]}</span>
          ${dish.img ? `<img src="${dish.img}" alt="${dish.name}" loading="lazy" />` : '<div class="item__img-placeholder"></div>'}
        </div>
        <div class="item__body">
          <h3 class="item__name">${dish.name}</h3>
          <div class="item__meta">
            <span class="item__stock"><strong>${state === 'agotado' ? 'AGOTADO' : 'Disponible'}</strong> ${stockText}</span>
            <span class="item__price">$${dish.price}</span>
          </div>
          <div class="item__bar" aria-hidden="true">
            <div class="item__bar-fill item__bar-fill--${state}" style="width:${pct}%"></div>
          </div>
          <div class="item__controls">
            <button class="item__btn" type="button" data-action="dec" aria-label="Restar una unidad de ${dish.name}">−</button>
            <button class="item__btn" type="button" data-action="inc" aria-label="Sumar una unidad de ${dish.name}">+</button>
            <span class="item__controls-label">${state === 'agotado' ? 'Marcar Disponible' : 'Marcar Agotado'}</span>
          </div>
        </div>
      </article>
    `;
  };

  const renderInventory = () => {
    if (!grid) return;
    const visible = inventory.filter((d) => {
      const avail = d.is_available ?? d.stock > 0;
      const matchesFilter = currentFilter === 'todos' || getState(avail) === currentFilter;
      const matchesSearch = d.name.toLowerCase().includes(currentSearch);
      return matchesFilter && matchesSearch;
    });
    grid.innerHTML = visible.map(itemTemplate).join('');
    if (emptyMsg) emptyMsg.hidden = visible.length !== 0;
    if (window.VanillaTilt && !prefersReducedMotion) {
      VanillaTilt.init($$('.item', grid), { speed: 400, scale: 1.02, max: 6, glare: true, 'max-glare': 0.15 });
    }
  };

  /** Cambia disponibilidad (Disponible/Agotado) y persiste en backend */
  const adjustStock = async (id, delta) => {
    const dish = inventory.find((d) => d.id === id);
    if (!dish) return;
    const nextAvailable = !(dish.is_available ?? dish.stock > 0);
    dish.is_available = nextAvailable;
    dish.stock = nextAvailable ? 1 : 0;
    renderInventory();
    updatePanelStats();

    const token = localStorage.getItem('afenix_access_token');
    if (!token || isNaN(Number(id))) return;
    try {
      await fetch(`${API.DISHES}/${id}`, {
        method:  'PUT',
        headers: authHeaders(),
        body:    JSON.stringify({ is_available: nextAvailable }),
      });
    } catch (err) {
      console.warn('No se pudo sincronizar disponibilidad con backend:', err);
    }
  };

  if (grid) {
    grid.addEventListener('click', (e) => {
      const btn = e.target.closest('.item__btn');
      if (!btn) return;
      const card = btn.closest('.item');
      adjustStock(card.dataset.id, btn.dataset.action === 'inc' ? 1 : -1);
    });
  }

  filterBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      filterBtns.forEach((b) => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      currentFilter = btn.dataset.filter;
      renderInventory();
    });
  });

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      currentSearch = e.target.value.trim().toLowerCase();
      renderInventory();
    });
  }

  /* --------------------------------------------------------
     6. MESEROS Y ÓRDENES — render agrupado por mesero
  -------------------------------------------------------- */
  const ordersGrid = $('#ordersGrid');

  const statusLabel = { preparando: 'Preparando', servido: 'Servido', pendiente: 'Pendiente' };
  const initials    = (name) => name.split(' ').map((n) => n[0]).slice(0, 2).join('');

  const orderTemplate = (order) => `
    <div class="order">
      <div class="order__top">
        <span class="order__table">Mesa <span>#${order.table}</span></span>
        <span class="order__status order__status--${order.status}">${statusLabel[order.status] || order.status}</span>
      </div>
      <div class="order__items">
        ${order.items.map((it) => `
          <div class="order__item">
            <span>${it.name}</span>
            <span class="order__qty">x${it.qty}</span>
          </div>`).join('')}
      </div>
    </div>
  `;

  const waiterTemplate = (w) => `
    <article class="waiter">
      <div class="waiter__head">
        <span class="waiter__avatar" aria-hidden="true">${initials(w.name)}</span>
        <div>
          <p class="waiter__name">${w.name}</p>
          <span class="waiter__role">${w.role}</span>
        </div>
        <span class="waiter__count">${w.orders.length} ${w.orders.length === 1 ? 'mesa' : 'mesas'}</span>
      </div>
      <div class="waiter__orders">
        ${w.orders.length
          ? w.orders.map(orderTemplate).join('')
          : '<p class="waiter__empty">Sin órdenes asignadas.</p>'}
      </div>
    </article>
  `;

  const renderOrders = () => {
    if (ordersGrid) ordersGrid.innerHTML = waiters.map(waiterTemplate).join('');
  };

  /* --------------------------------------------------------
     7. RESUMEN DEL PANEL (contadores)
  -------------------------------------------------------- */
  const statDisponibles = $('#statDisponibles');
  const statPocas       = $('#statPocas');
  const statAgotados    = $('#statAgotados');
  const statOrdenes     = $('#statOrdenes');

  const updatePanelStats = () => {
    const counts     = { disponible: 0, pocas: 0, agotado: 0 };
    inventory.forEach((d) => { const avail = d.is_available ?? d.stock > 0; const st = getState(avail); if(st==='disponible') counts.disponible++; else if(st==='agotado') counts.agotado++; });
    const totalOrders = waiters.reduce((sum, w) => sum + w.orders.length, 0);

    const setNum = (el, value) => {
      if (!el) return;
      if (window.anime && !prefersReducedMotion) {
        const obj = { v: parseInt(el.textContent, 10) || 0 };
        anime({ targets: obj, v: value, round: 1, duration: 700, easing: 'easeOutQuad',
                update: () => { el.textContent = obj.v; } });
      } else {
        el.textContent = value;
      }
    };

    setNum(statDisponibles, counts.disponible);
    setNum(statPocas,       counts.pocas);
    setNum(statAgotados,    counts.agotado);
    setNum(statOrdenes,     totalOrders);
  };

  /* --------------------------------------------------------
     8. INICIALIZACIÓN
  -------------------------------------------------------- */
  function initUI() {
    renderInventory();
    renderOrders();
    updatePanelStats();
    renderFoodTable();   // tabla de gestión de alimentos

    if (window.AOS) {
      AOS.init({ duration: 800, easing: 'ease-out-cubic', once: true,
                 offset: 80, disable: prefersReducedMotion });
    }
  }

  // Arranca cargando datos del backend
  loadDashboardData();

  /* ============================================================
     9. GESTIÓN DE ALIMENTOS — Crear / Eliminar platos
        Usa los mismos datos de `inventory` ya cargados.
        Tras cada operación refresca:
          · La tabla de gestión (#foodTbody)
          · El grid de inventario (#inventoryGrid)
          · Los contadores del panel
  ============================================================ */

  /* ---- Elementos del DOM ---- */
  const foodForm          = $('#foodForm');
  const foodFormTitle     = $('#foodFormTitle');
  const foodSubmitBtn     = $('#foodSubmitBtn');
  const foodCancelBtn     = $('#foodCancelBtn');
  const foodNameInput     = $('#foodName');
  const foodCategoryInput = $('#foodCategory');
  const foodPriceInput    = $('#foodPrice');
  const foodStockInput    = $('#foodStock');
  const foodTimeInput     = $('#foodTime');
  const foodDescInput     = $('#foodDesc');
  const foodNameError     = $('#foodNameError');
  const foodCategoryError = $('#foodCategoryError');
  const foodPriceError    = $('#foodPriceError');
  const foodTimeError     = $('#foodTimeError');
  const foodFormError     = $('#foodFormError');
  const foodFormOk        = $('#foodFormOk');
  const foodSearch        = $('#foodSearch');
  const foodCount         = $('#foodCount');
  const foodTbody         = $('#foodTbody');
  const foodEmpty         = $('#foodEmpty');

  let foodEditingId    = null;   // id del plato en edición (null = modo crear)
  let foodSearch_      = '';     // término de búsqueda actual

  /* ---- Helpers de feedback ---- */
  const showFoodError = (msg) => {
    if (!foodFormError) return;
    foodFormError.textContent = msg;
    foodFormError.hidden = false;
    if (foodFormOk) foodFormOk.hidden = true;
  };
  const showFoodOk = (msg) => {
    if (!foodFormOk) return;
    foodFormOk.textContent = msg;
    foodFormOk.hidden = false;
    if (foodFormError) foodFormError.hidden = true;
    setTimeout(() => { if (foodFormOk) foodFormOk.hidden = true; }, 3500);
  };
  const clearFoodFeedback = () => {
    if (foodFormError) { foodFormError.hidden = true; foodFormError.textContent = ''; }
    if (foodFormOk)    { foodFormOk.hidden    = true; foodFormOk.textContent    = ''; }
  };
  const setFieldError = (el, msg) => { if (el) { el.textContent = msg; el.hidden = !msg; } };
  const clearFieldErrors = () => {
    [foodNameError, foodCategoryError, foodPriceError, foodTimeError]
      .forEach((e) => setFieldError(e, ''));
  };

  /* ---- Validación del formulario ---- */
  const validateFoodForm = () => {
    clearFieldErrors();
    let ok = true;
    if (!foodNameInput?.value.trim())     { setFieldError(foodNameError,     'El nombre es obligatorio.'); ok = false; }
    if (!foodCategoryInput?.value.trim()) { setFieldError(foodCategoryError, 'La categoría es obligatoria.'); ok = false; }
    const price = Number(foodPriceInput?.value);
    if (!price || price < 1)              { setFieldError(foodPriceError,    'Indica un precio válido (≥ 1).'); ok = false; }
    const time  = Number(foodTimeInput?.value);
    if (!time  || time  < 1)              { setFieldError(foodTimeError,     'Indica un tiempo válido (≥ 1 min).'); ok = false; }
    return ok;
  };

  /* ---- Render de la tabla de gestión ---- */
  const escHtml = (s) => String(s).replace(/[&<>"']/g,
    (c) => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));

  const renderFoodTable = () => {
    if (!foodTbody) return;
    const q = foodSearch_.toLowerCase();
    const visible = inventory.filter((d) => d.name.toLowerCase().includes(q));

    if (foodCount) foodCount.textContent = `${inventory.length} plato${inventory.length !== 1 ? 's' : ''}`;

    if (!visible.length) {
      foodTbody.innerHTML = '';
      if (foodEmpty) foodEmpty.hidden = false;
      return;
    }
    if (foodEmpty) foodEmpty.hidden = true;

    foodTbody.innerHTML = visible.map((d) => {
      const avail = d.is_available ?? d.stock > 0;
      const state = getState(avail);
      const stateClass = { disponible: 'tag--ok', pocas: 'tag--low', agotado: 'tag--out' }[state];
      const stateText  = { disponible: 'Disponible', pocas: 'Pocas uds.', agotado: 'Agotado' }[state];
      return `
        <tr data-id="${d.id}">
          <td class="food-table__name">${escHtml(d.name)}</td>
          <td>${escHtml(d.category || '—')}</td>
          <td>$${d.price}</td>
          <td>${d.stock}</td>
          <td><span class="tag ${stateClass}">${stateText}</span></td>
          <td class="food-table__actions-col">
            <div class="row-actions">
              <button class="icon-btn icon-btn--edit" type="button" data-food-action="edit"
                      aria-label="Editar ${escHtml(d.name)}" title="Editar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                     stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z"/>
                </svg>
              </button>
            </div>
          </td>
        </tr>`;
    }).join('');
  };

  /* ---- Búsqueda en tabla ---- */
  if (foodSearch) {
    foodSearch.addEventListener('input', (e) => {
      foodSearch_ = e.target.value.trim();
      renderFoodTable();
    });
  }

  /* ---- Delegación de acciones editar en la tabla ---- */
  if (foodTbody) {
    foodTbody.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-food-action]');
      if (!btn) return;
      const id = btn.closest('tr').dataset.id;
      if (btn.dataset.foodAction === 'edit') startFoodEdit(id);
    });
  }

  /* ---- Refrescar todo lo que depende del inventario ---- */
  const refreshInventoryUI = () => {
    renderInventory();
    renderFoodTable();
    updatePanelStats();
  };

  /* ---- Modo edición: rellena el formulario ---- */
  const startFoodEdit = (id) => {
    const dish = inventory.find((d) => d.id === id);
    if (!dish) return;
    foodEditingId = id;
    if (foodNameInput)     foodNameInput.value     = dish.name;
    if (foodCategoryInput) foodCategoryInput.value = dish.category || '';
    if (foodPriceInput)    foodPriceInput.value    = dish.price;
    if (foodStockInput)    foodStockInput.value    = dish.stock;
    if (foodTimeInput)     foodTimeInput.value     = dish.estimatedTime || 15;
    if (foodDescInput)     foodDescInput.value     = dish.description  || '';
    clearFoodFeedback(); clearFieldErrors();
    if (foodFormTitle)  foodFormTitle.textContent            = 'Editar plato';
    if (foodSubmitBtn)  foodSubmitBtn.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" width="16" height="16">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
        <polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
      </svg>
      Guardar cambios`;
    if (foodCancelBtn)  foodCancelBtn.hidden = false;
    foodForm?.scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth', block: 'start' });
    foodNameInput?.focus();
  };

  /* ---- Resetear formulario a modo "Agregar" ---- */
  const resetFoodForm = () => {
    foodEditingId = null;
    foodForm?.reset();
    if (foodStockInput) foodStockInput.value = '10';
    clearFoodFeedback(); clearFieldErrors();
    if (foodFormTitle)  foodFormTitle.textContent = 'Agregar nuevo plato';
    if (foodSubmitBtn)  foodSubmitBtn.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" width="16" height="16">
        <path d="M12 5v14M5 12h14"/>
      </svg>
      Agregar plato`;
    if (foodCancelBtn) foodCancelBtn.hidden = true;
  };

  if (foodCancelBtn) foodCancelBtn.addEventListener('click', resetFoodForm);

  /* ---- Envío del formulario: crear o editar ---- */
  if (foodForm) {
    foodForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearFoodFeedback();
      if (!validateFoodForm()) return;

      const token = localStorage.getItem('afenix_access_token');
      const availVal = foodStockInput ? (foodStockInput.value === 'true' || foodStockInput.value === '1' || Number(foodStockInput.value) > 0) : true;
      const body = {
        name:              foodNameInput.value.trim(),
        category:          foodCategoryInput.value.trim(),
        price:             Math.round(Number(foodPriceInput.value) * 100),
        estimated_time:    Math.round(Number(foodTimeInput.value) * 60),
        description:       foodDescInput?.value.trim() || undefined,
        is_available:      availVal,
        preparation_notes: undefined,
      };

      if (foodSubmitBtn) { foodSubmitBtn.disabled = true; foodSubmitBtn.style.opacity = '0.7'; }

      try {
        let response;
        if (foodEditingId && token && !isNaN(Number(foodEditingId))) {
          // ── Editar plato existente ──
          response = await fetch(`${API.DISHES}/${foodEditingId}`, {
            method:  'PUT',
            headers: authHeaders(),
            body:    JSON.stringify(body),
          });
        } else {
          // ── Crear nuevo plato ──
          if (!token) throw new Error('Inicia sesión como administrador para agregar platos.');
          response = await fetch(API.DISHES, {
            method:  'POST',
            headers: authHeaders(),
            body:    JSON.stringify(body),
          });
        }

        const payload = await response.json();
        if (!response.ok || !payload.success) throw new Error(payload.message || 'Error al guardar el plato.');

        const savedDish = normalizeDish(payload.data);
        savedDish.category    = payload.data.category    || body.category;
        savedDish.description = payload.data.description || '';
        savedDish.estimatedTime = payload.data.estimated_time || body.estimated_time;

        if (foodEditingId) {
          const idx = inventory.findIndex((d) => d.id === foodEditingId);
          if (idx !== -1) inventory[idx] = savedDish;
          showFoodOk(`Plato "${savedDish.name}" actualizado correctamente.`);
        } else {
          inventory.push(savedDish);
          showFoodOk(`Plato "${savedDish.name}" agregado correctamente.`);
        }

        resetFoodForm();
        refreshInventoryUI();

      } catch (err) {
        showFoodError(err.message || 'No se pudo guardar el plato.');
      } finally {
        if (foodSubmitBtn) { foodSubmitBtn.disabled = false; foodSubmitBtn.style.opacity = ''; }
      }
    });
  }
});
