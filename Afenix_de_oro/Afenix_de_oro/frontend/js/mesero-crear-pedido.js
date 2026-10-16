document.addEventListener('DOMContentLoaded', async () => {
  if (!Afenix.guardPage('CAMARERO')) return;
  const $ = s => document.querySelector(s);
  const { api, toast, money, esc } = Afenix;
  let dishes = [];
  let categories = [];
  let selectedCategory = 'Todas';
  let searchQuery = '';

  function setMsg(t, ok = false) {
    const e = $('#orderMsg');
    if (!e) return;
    e.hidden = !t;
    e.textContent = t;
    e.className = `form-message${ok ? ' ok' : ''}`;
  }

  function getFiltered() {
    let filtered = dishes.slice();
    if (selectedCategory !== 'Todas') {
      filtered = filtered.filter(d => {
        const cname = (d.category_name || d.category || '').trim();
        return cname === selectedCategory;
      });
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(d => (d.name || '').toLowerCase().includes(q));
    }
    return filtered;
  }

  function groupByCategory(list) {
    const groups = {};
    const order = [];
    list.forEach(d => {
      const cname = (d.category_name || d.category || 'Sin categoría').trim() || 'Sin categoría';
      if (!groups[cname]) { groups[cname] = []; order.push(cname); }
      groups[cname].push(d);
    });
    const catOrder = categories.map(c => c.name);
    order.sort((a,b) => {
      const ia = catOrder.indexOf(a);
      const ib = catOrder.indexOf(b);
      if (ia !== -1 && ib !== -1) return ia - ib;
      if (ia !== -1) return -1;
      if (ib !== -1) return 1;
      return a.localeCompare(b);
    });
    return { groups, order };
  }

  function renderFilters() {
    const container = $('#categoryFilters');
    if (!container) return;
    const allCats = ['Todas', ...categories.map(c => c.name)];
    container.innerHTML = allCats.map(name => {
      const active = name === selectedCategory ? ' is-active' : '';
      return `<button type="button" class="afenix-filter-pill${active}" data-cat="${esc(name)}">${esc(name)}</button>`;
    }).join('');
    container.querySelectorAll('[data-cat]').forEach(btn => {
      btn.addEventListener('click', () => {
        selectedCategory = btn.dataset.cat;
        renderFilters();
        renderDishes();
      });
    });
  }

  function renderDishes() {
    const container = $('#dishes');
    if (!container) return;
    const filtered = getFiltered();
    if (!dishes.length) { container.innerHTML='<p class="muted">No hay platos registrados.</p>'; return; }
    if (!filtered.length) {
      const hint = searchQuery ? `No se encontraron platos para "${esc(searchQuery)}"${selectedCategory!=='Todas'?` en ${esc(selectedCategory)}`:''}.` : `No hay platos en ${esc(selectedCategory)}.`;
      container.innerHTML = `<p class="muted">${hint}</p>`;
      return;
    }

    if (selectedCategory !== 'Todas') {
      container.innerHTML = '<div class="inventory-grid inventory-grid--order" style="gap:16px">' + filtered.map(d => dishCard(d)).join('') + '</div>';
    } else if (searchQuery) {
      const { groups, order } = groupByCategory(filtered);
      container.innerHTML = order.map(cat => {
        const items = groups[cat];
        return `<div class="afenix-category-block"><h5 class="afenix-category-title">${esc(cat)} <span class="count">${items.length}</span></h5><div class="inventory-grid inventory-grid--order" style="gap:16px">${items.map(d => dishCard(d)).join('')}</div></div>`;
      }).join('');
    } else {
      const { groups, order } = groupByCategory(filtered);
      container.innerHTML = order.map(cat => {
        const items = groups[cat];
        return `<div class="afenix-category-block"><h5 class="afenix-category-title">${esc(cat)} <span class="count">${items.length}</span></h5><div class="inventory-grid inventory-grid--order" style="gap:16px">${items.map(d => dishCard(d)).join('')}</div></div>`;
      }).join('');
    }
    container.querySelectorAll('[data-dish]').forEach(i => i.addEventListener('input', () => updateTotal(i)));
    updateTotal();
  }

  function dishCard(d){
    const disponible = !!d.is_available;
    const img = d.image_url || d.image_path || '';
    const imgHtml = img ? `<img src="${esc(img)}" alt="${esc(d.name)}" style="width:100%; height:120px; object-fit:cover; border-radius:10px; border:1px solid var(--line); margin-bottom:10px; ${disponible?'':'filter:grayscale(0.6); opacity:0.6;'}">` : `<div style="width:100%; height:120px; display:flex; align-items:center; justify-content:center; background:#f6f1e7; border:1px solid var(--line); border-radius:10px; color:var(--muted); font-size:.85rem;">Sin imagen</div>`;
    if (!disponible) {
      const badge = '<span style="display:inline-block; background:#f6e5e4; color:#8a2925; font-size:.7rem; font-weight:700; padding:4px 8px; border-radius:999px;">🔴 AGOTADO</span>';
      return `<article class="inventory-card" style="opacity:0.88;"><div style="margin-bottom:10px;">${imgHtml}</div><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;"><h3 style="margin:0;">${esc(d.name)}</h3>${badge}</div><p class="muted">${money(d.price)} · <span style="color:#8a2925; font-weight:600;">AGOTADO</span></p></article>`;
    }
    const badge = '<span style="display:inline-block; background:#eaf6e9; color:#246126; font-size:.7rem; font-weight:700; padding:4px 8px; border-radius:999px;">🟢 Disponible</span>';
    let subHtml = '';
    const subs = d.subcategories || [];
    if(subs.length){
      subHtml = subs.map(sub=>{
        const opts = sub.options || [];
        const optsHtml = opts.map(o=>`<option value="${o.id}">${esc(o.name)}</option>`).join('');
        return `<div class="field" style="margin-top:8px"><label for="sub-${d.id}-${sub.id}" style="font-size:.82rem">${esc(sub.name)} <span style="color:#b00">*</span></label><select id="sub-${d.id}-${sub.id}" data-sub-dish="${d.id}" data-sub="${sub.id}" style="background:rgba(255,255,255,0.06);border:1px solid rgba(199,154,69,0.22);color:#fffdf9;padding:8px 10px;border-radius:10px;width:100%"><option value="">▼ Seleccionar</option>${optsHtml}</select></div>`;
      }).join('');
    }
    return `<article class="inventory-card"><div style="margin-bottom:10px;">${imgHtml}</div><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;"><h3 style="margin:0;">${esc(d.name)}</h3>${badge}</div><p class="muted">${money(d.price)} · Disponible</p><div class="field"><label for="q${d.id}">Cantidad</label><input id="q${d.id}" data-dish="${d.id}" type="number" min="0" value="" placeholder="Cantidad" inputmode="numeric"></div>${subHtml}<div class="line-total" id="line${d.id}">Subtotal: ${money(0)}</div></article>`;
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

  async function loadOptions() {
    try {
      const [cats, dishesData] = await Promise.all([
        api('/api/v1/categories?limit=100').catch(() => []),
        api('/api/v1/dishes?limit=100')
      ]);
      categories = Array.isArray(cats) ? cats : [];
      dishes = Array.isArray(dishesData) ? dishesData : (dishesData||[]);
      if (!categories.length && dishes.length) {
        const seen = new Set();
        dishes.forEach(d => {
          const n = (d.category_name || d.category || '').trim();
          if (n && !seen.has(n)) seen.add(n);
        });
        if (seen.size) categories = Array.from(seen).map(name => ({id: name, name}));
      }
      renderFilters();
      renderDishes();
    } catch(e){ toast(e.message,'error'); }
  }

  const searchInput = $('#dishSearch');
  if (searchInput) {
    let t;
    searchInput.addEventListener('input', () => {
      clearTimeout(t);
      t = setTimeout(()=>{ searchQuery = searchInput.value.trim(); renderDishes(); }, 250);
    });
  }

  try { await loadOptions(); } catch(e){ toast(e.message,'error'); }

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
      let items = [];
      try {
        items = Array.from(document.querySelectorAll('[data-dish]')).map(inp=>{
          const dish_id = Number(inp.dataset.dish);
          const quantity = Number(inp.value) || 0;
          if(quantity<=0) return null;
          const dish = dishes.find(x=> String(x.id)===String(dish_id));
          if(!dish) return null;
          const subs = dish.subcategories||[];
          const selections=[];
          for(const sub of subs){
            const sel = document.querySelector(`[data-sub-dish="${dish_id}"][data-sub="${sub.id}"]`);
            const val = sel ? Number(sel.value) : 0;
            if(!val){
              throw new Error(`Debes seleccionar ${sub.name} para el plato "${dish.name}"`);
            }
            selections.push({subcategory_id: sub.id, option_id: val});
          }
          return { dish_id, quantity, subcategory_selections: selections };
        }).filter(Boolean);
      } catch(err){
        setMsg(err.message);
        toast(err.message,'error');
        return;
      }
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
        if (searchInput) { searchInput.value=''; searchQuery=''; }
        selectedCategory='Todas';
        renderFilters();
        await loadOptions();
      } catch (e) {
        setMsg(e.message);
        toast(e.message, 'error');
      }
    });
  }

  const refreshBtn = $('#refreshData');
  if (refreshBtn) refreshBtn.addEventListener('click', () => loadOptions().catch(e => toast(e.message, 'error')));
});
