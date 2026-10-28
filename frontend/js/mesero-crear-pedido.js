document.addEventListener('DOMContentLoaded', async () => {
  if (!Afenix.guardPage('CAMARERO')) return;
  const $ = s => document.querySelector(s);
  const { api, toast, money, esc } = Afenix;
  let dishes = [];
  let categories = [];
  let currentFilter = '';
  let currentSearch = '';

  function setMsg(t, ok = false) {
    const e = $('#orderMsg');
    if (!e) return;
    e.hidden = !t;
    e.textContent = t;
    e.className = `form-message${ok ? ' ok' : ''}`;
  }

  async function loadCategories() {
    try {
      categories = await api('/api/v1/categories?limit=100') || [];
      const sel = $('#categoryFilter');
      if (sel) {
        sel.innerHTML = '<option value="">Todas las categorías</option>' +
          categories.map(c => `<option value="${esc(c.name)}">${esc(c.name)}</option>`).join('');
      }
    } catch (e) {
      console.error('Error cargando categorías:', e);
    }
  }

  async function loadDishes() {
    try {
      dishes = await api('/api/v1/dishes?limit=100') || [];
      renderDishes();
    } catch (e) {
      toast(e.message, 'error');
    }
  }

  function filterDishes() {
    const search = currentSearch.toLowerCase();
    const cat = currentFilter;
    return dishes.filter(d => {
      const matchSearch = !search || d.name.toLowerCase().includes(search);
      const matchCat = !cat || d.category === cat;
      return matchSearch && matchCat;
    });
  }

  function renderDishes() {
    const container = $('#dishes');
    if (!container) return;
    const filtered = filterDishes();

    if (!filtered.length) {
      container.innerHTML = '<p class="muted">No hay platos que coincidan con los filtros.</p>';
      return;
    }

    // Agrupar por categoría
    const grouped = {};
    filtered.forEach(d => {
      const cat = d.category || 'Sin categoría';
      if (!grouped[cat]) grouped[cat] = [];
      grouped[cat].push(d);
    });

    let html = '';
    Object.keys(grouped).sort().forEach(cat => {
      html += `<div class="category-group" style="margin-bottom:24px;">
        <h3 style="font-family:Cinzel,serif; color:#c79a45; font-size:1rem; border-bottom:1px solid rgba(199,154,69,0.25); padding-bottom:6px; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.1em;">${esc(cat)}</h3>
        <div style="display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:16px;">
          ${grouped[cat].map(d => {
            const disponible = !!d.is_available;
            const img = d.image_url || d.image_path || '';
            const imgHtml = img
              ? `<img src="${esc(img)}" alt="${esc(d.name)}" style="width:100%; height:120px; object-fit:cover; border-radius:10px; border:1px solid var(--line); margin-bottom:10px; ${disponible ? '' : 'filter:grayscale(0.6); opacity:0.6;'}">`
              : `<div style="width:100%; height:120px; display:flex; align-items:center; justify-content:center; background:#f6f1e7; border:1px solid var(--line); border-radius:10px; color:var(--muted); font-size:.85rem;">Sin imagen</div>`;
            if (!disponible) {
              const badge = '<span style="display:inline-block; background:#f6e5e4; color:#8a2925; font-size:.7rem; font-weight:700; padding:4px 8px; border-radius:999px;">🔴 AGOTADO</span>';
              return `<article class="inventory-card" style="opacity:0.88;"><div style="margin-bottom:10px;">${imgHtml}</div><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;"><h3 style="margin:0; font-size:.9rem;">${esc(d.name)}</h3>${badge}</div><p class="muted">${money(d.price)} · <span style="color:#8a2925; font-weight:600;">AGOTADO</span></p></article>`;
            }
            const badge = '<span style="display:inline-block; background:#eaf6e9; color:#246126; font-size:.7rem; font-weight:700; padding:4px 8px; border-radius:999px;">🟢 Disponible</span>';
            return `<article class="inventory-card"><div style="margin-bottom:10px;">${imgHtml}</div><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;"><h3 style="margin:0; font-size:.9rem;">${esc(d.name)}</h3>${badge}</div><p class="muted">${money(d.price)} · Disponible</p><div class="field"><label for="q${d.id}">Cantidad</label><input id="q${d.id}" data-dish="${d.id}" type="number" min="0" value="" placeholder="Cantidad" inputmode="numeric"></div><div class="line-total" id="line${d.id}">Subtotal: ${money(0)}</div></article>`;
          }).join('')}
        </div>
      </div>`;
    });
    container.innerHTML = html;

    // Event listeners para cantidad
    document.querySelectorAll('[data-dish]:not([disabled])').forEach(i => i.addEventListener('input', () => updateTotal(i)));
    updateTotal();
  }

  function updateTotal(changed) {
    if (changed) {
      const d = dishes.find(x => String(x.id) === String(changed.dataset.dish));
      const q = Number(changed.value) || 0;
      const line = $(`#line${d.id}`);
      if (line) line.textContent = `Subtotal: ${money(q * (Number(d?.price) || 0))}`;
    }
    let totalCents = 0;
    document.querySelectorAll('[data-dish]').forEach(i => {
      const d = dishes.find(x => String(x.id) === String(i.dataset.dish));
      totalCents += (Number(i.value) || 0) * (Number(d?.price) || 0);
    });
    const totalEl = $('#total');
    if (totalEl) totalEl.textContent = `Total: ${money(totalCents)}`;
  }

  // Eventos de filtro y búsqueda
  $('#categoryFilter')?.addEventListener('change', (e) => {
    currentFilter = e.target.value;
    renderDishes();
  });

  $('#dishSearch')?.addEventListener('input', (e) => {
    currentSearch = e.target.value;
    renderDishes();
  });

  try {
    await loadCategories();
    await loadDishes();
  } catch (e) {
    toast(e.message, 'error');
  }

  // Crear pedido
  const orderForm = $('#orderForm');
  if (orderForm) {
    orderForm.addEventListener('submit', async e => {
      e.preventDefault();
      setMsg('');
      const tableNumber = Number($('#table').value);
      if (!Number.isInteger(tableNumber) || tableNumber <= 0) {
        setMsg('Ingresa un número de mesa válido.');
        return;
      }
      const items = Array.from(document.querySelectorAll('[data-dish]')).map(i => ({ dish_id: Number(i.dataset.dish), quantity: Number(i.value) })).filter(x => x.quantity > 0);
      if (!items.length) {
        setMsg('Selecciona al menos un plato.');
        return;
      }
      try {
        await api('/api/v1/orders', { method: 'POST', body: JSON.stringify({ table_number: tableNumber, items, notes: $('#notes').value.trim() || null }) });
        setMsg('Pedido creado y enviado a cocina.', true);
        toast('Pedido creado correctamente');
        $('#table').value = '';
        $('#notes').value = '';
        await loadDishes();
      } catch (e) {
        setMsg(e.message);
        toast(e.message, 'error');
      }
    });
  }

  const refreshBtn = $('#refreshData');
  if (refreshBtn) refreshBtn.addEventListener('click', () => loadDishes().catch(e => toast(e.message, 'error')));
});