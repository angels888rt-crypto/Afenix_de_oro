/* ============================================================
   AFENIX DE ORO — Panel de sesión (mesero)
   Secciones:
   1. Utilidades + API helpers
   2. Header con scroll
   3. Menú hamburguesa
   4. Carga de datos desde el backend (platos y órdenes)
   5. Inventario: render, estado de stock, filtros, búsqueda y ajuste
   6. Meseros y órdenes: render agrupado
   7. Resumen del panel (contadores)
   8. Inicialización de librerías (AOS, VanillaTilt)
============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  /* --------------------------------------------------------
     1. UTILIDADES + API HELPERS
  -------------------------------------------------------- */
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const yearEl = $('#year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

 // Define la URL base de tu backend (si usas variable de entorno o la de Render directamente)
  const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000'                  // Para cuando pruebes en local
    : 'https://pollo-api.hostless.app';      // Tu backend oficial en Render

  const API = {
    DISHES: `${API_BASE_URL}/api/v1/dishes`,
    ORDERS: `${API_BASE_URL}/api/v1/orders`,
    USERS: `${API_BASE_URL}/api/v1/users`,
  };

  const authHeaders = (extra = {}) => {
    const token = localStorage.getItem('afenix_access_token');
    return { 'Content-Type': 'application/json', ...extra,
             ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  };

  const centsToDisplay = (cents) => Math.max(1, Math.round((cents || 0) / 100));

  const normalizeDish = (d) => ({
    id:    String(d.id),
    name:  d.name,
    price: centsToDisplay(d.price),
    stock: typeof d.stock_quantity === 'number' ? d.stock_quantity : (d.is_available ? 10 : 0),
    img:   '',
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
  const LOW_THRESHOLD = 5;
  const STOCK_MAX     = 25;

  const fallbackInventory = [
    { id: 'd1', name: 'Xiao Long Bao',    price: 12, stock: 18, img: '' },
    { id: 'd2', name: 'Pato Pekín',       price: 28, stock: 3,  img: '' },
    { id: 'd3', name: 'Kung Pao',         price: 16, stock: 0,  img: '' },
    { id: 'd4', name: 'Fideos Lamian',    price: 14, stock: 24, img: '' },
    { id: 'd5', name: 'Arroz Yangzhou',   price: 11, stock: 9,  img: '' },
    { id: 'd6', name: 'Wontons picantes', price: 10, stock: 2,  img: '' },
    { id: 'd7', name: 'Ternera Sichuan',  price: 19, stock: 0,  img: '' },
    { id: 'd8', name: 'Rollos primavera', price: 8,  stock: 15, img: '' },
  ];

  const fallbackWaiters = [
    {
      id: 'w1', name: 'Mesero Demo', role: 'Mesa · conexión local',
      orders: [
        { table: 1, status: 'pendiente', items: [{ name: 'Xiao Long Bao', qty: 2 }] },
      ],
    },
  ];

  let inventory = [];
  let waiters   = [];

  /** Carga platos, órdenes y usuarios del backend; usa fallback si falla */
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

      // Agrupa órdenes por camarero
      const ordersRaw = orderPayload.data || [];

      // Construye mapa camarero_id → datos de usuario
      const waiterMap = {};
      if (userRes.ok) {
        const userPayload = await userRes.json();
        (userPayload.data || []).forEach((u) => {
          waiterMap[String(u.id)] = {
            id:   String(u.id),
            name: u.full_name || u.username,
            role: u.role === 'ADMIN' ? 'Administrador' : 'Mesero',
          };
        });
      }

      // Agrupa órdenes por camarero (usa table_number correcto, no table_id)
      const byWaiter = {};
      ordersRaw.forEach((o) => {
        const wId = o.camarero_id ? String(o.camarero_id) : 'unknown';
        if (!byWaiter[wId]) {
          byWaiter[wId] = waiterMap[wId]
            ? { ...waiterMap[wId], orders: [] }
            : { id: wId, name: `Mesero #${wId}`, role: 'Mesero', orders: [] };
        }
        byWaiter[wId].orders.push({
          table:  o.table_number != null ? o.table_number : (o.table_id || 1),
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
      console.warn('No se pudo cargar desde la API, usando datos locales.', err);
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

  const getState = (stock) => {
    if (stock <= 0)             return 'agotado';
    if (stock <= LOW_THRESHOLD) return 'pocas';
    return 'disponible';
  };

  const stateLabel = { disponible: 'Disponible', pocas: 'Pocas unidades', agotado: 'Agotado' };

  const itemTemplate = (dish) => {
    const state     = getState(dish.stock);
    const pct       = Math.min(100, Math.round((dish.stock / STOCK_MAX) * 100));
    const stockText = state === 'agotado' ? 'Sin existencias' : `${dish.stock} unidades`;
    return `
      <article class="item" data-id="${dish.id}" data-name="${dish.name.toLowerCase()}" data-state="${state}">
        <div class="item__media">
          <span class="item__badge item__badge--${state}">${stateLabel[state]}</span>
          ${dish.img ? `<img src="${dish.img}" alt="${dish.name}" loading="lazy" />` : '<div class="item__img-placeholder"></div>'}
        </div>
        <div class="item__body">
          <h3 class="item__name">${dish.name}</h3>
          <div class="item__meta">
            <span class="item__stock"><strong>${state === 'agotado' ? '0' : dish.stock}</strong> ${stockText}</span>
            <span class="item__price">$${dish.price}</span>
          </div>
          <div class="item__bar" aria-hidden="true">
            <div class="item__bar-fill item__bar-fill--${state}" style="width:${pct}%"></div>
          </div>
          <div class="item__controls">
            <button class="item__btn" type="button" data-action="dec" aria-label="Restar una unidad de ${dish.name}">−</button>
            <button class="item__btn" type="button" data-action="inc" aria-label="Sumar una unidad de ${dish.name}">+</button>
            <span class="item__controls-label">Ajustar stock</span>
          </div>
        </div>
      </article>
    `;
  };

  const renderInventory = () => {
    if (!grid) return;
    const visible = inventory.filter((d) => {
      const matchesFilter = currentFilter === 'todos' || getState(d.stock) === currentFilter;
      const matchesSearch = d.name.toLowerCase().includes(currentSearch);
      return matchesFilter && matchesSearch;
    });
    grid.innerHTML = visible.map(itemTemplate).join('');
    if (emptyMsg) emptyMsg.hidden = visible.length !== 0;
    if (window.VanillaTilt && !prefersReducedMotion) {
      VanillaTilt.init($$('.item', grid), { speed: 400, scale: 1.02, max: 6, glare: true, 'max-glare': 0.15 });
    }
  };

  /** Ajusta stock localmente y persiste el cambio al backend */
  const adjustStock = async (id, delta) => {
    const dish = inventory.find((d) => d.id === id);
    if (!dish) return;
    dish.stock = Math.max(0, dish.stock + delta);
    renderInventory();
    updatePanelStats();

    const token = localStorage.getItem('afenix_access_token');
    if (!token || isNaN(Number(id))) return;
    try {
      await fetch(`${API.DISHES}/${id}`, {
        method:  'PUT',
        headers: authHeaders(),
        body:    JSON.stringify({ stock_quantity: dish.stock }),
      });
    } catch (err) {
      console.warn('No se pudo actualizar el stock en el servidor:', err);
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
        ${w.orders.length ? w.orders.map(orderTemplate).join('') : '<p class="waiter__empty">Sin órdenes asignadas.</p>'}
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
    inventory.forEach((d) => { counts[getState(d.stock)]++; });
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

    if (window.AOS) {
      AOS.init({ duration: 800, easing: 'ease-out-cubic', once: true, offset: 80,
                 disable: prefersReducedMotion });
    }
  }

  // Arranca cargando datos del backend
  loadDashboardData();
});
