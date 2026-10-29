document.addEventListener('DOMContentLoaded', async () => {
  if (!Afenix.guardPage('ADMIN')) return;
  const $ = s => document.querySelector(s);
  const { api, toast, esc, money } = Afenix;

  let subcats = [];
  let allDishes = [];
  let editingId = null;
  let editingSubcat = null;
  let tempOptions = []; // {name, sort_order}
  let selectedDishIds = new Set();
  let dishesLoading = true;
  let dishesLoadError = '';

  const $subName = $('#subName');
  const $subDesc = $('#subDesc');
  const $subId = $('#subId');
  const $subMsg = $('#subMsg');
  const $optList = $('#subOptList');
  const $dishBoxes = $('#dishCheckboxes');
  const $editor = $('#editor');
  const $subcatsList = $('#subcatsList');

  function setMsg(t, ok = false) {
    $subMsg.hidden = !t;
    $subMsg.textContent = t;
    $subMsg.className = `form-message${ok ? ' ok' : ''}`;
  }

  function reset() {
    editingId = null;
    editingSubcat = null;
    tempOptions = [];
    selectedDishIds = new Set();
    $subForm().reset();
    $subId.value = '';
    $('#formTitle').textContent = 'Crear subcategoría';
    $editor.style.display = 'none';
    setMsg('');
    renderOptions();
    renderDishes();
  }

  function $subForm() { return $('#subcatForm'); }

  async function load() {
    dishesLoading = true;
    dishesLoadError = '';
    renderDishes();

    const subcategoriesRequest = api('/api/v1/subcategories?limit=100')
      .then(data => {
        subcats = data || [];
        renderList();
      })
      .catch(error => {
        toast(error.message, 'error');
        $subcatsList.innerHTML = `<p class="muted">No se pudieron cargar las subcategorías: ${esc(error.message)}</p>`;
      });

    const dishesRequest = api('/api/v1/dishes?limit=100')
      .then(data => {
        allDishes = Array.isArray(data) ? data : [];
      })
      .catch(error => {
        allDishes = [];
        dishesLoadError = error.message;
        toast(error.message, 'error');
      })
      .finally(() => {
        dishesLoading = false;
        renderDishes();
      });

    await Promise.all([subcategoriesRequest, dishesRequest]);
  }

  function renderList() {
    if (!subcats.length) {
      $subcatsList.innerHTML = '<p class="muted" style="text-align:center;padding:24px;">No hay subcategorías. Crea la primera.</p>';
      return;
    }
    $subcatsList.innerHTML = `
      <table style="width:100%;border-collapse:collapse;margin-top:12px;">
        <thead>
          <tr>
            <th style="text-align:left;padding:12px;border-bottom:2px solid #7a0c12;">Nombre</th>
            <th style="text-align:left;padding:12px;border-bottom:2px solid #7a0c12;">Descripción</th>
            <th style="text-align:center;padding:12px;border-bottom:2px solid #7a0c12;">Platos</th>
            <th style="text-align:center;padding:12px;border-bottom:2px solid #7a0c12;">Opciones</th>
            <th style="text-align:right;padding:12px;border-bottom:2px solid #7a0c12;">Acciones</th>
          </tr>
        </thead>
        <tbody>
          ${subcats.map(s => `
            <tr>
              <td style="padding:12px;border-bottom:1px solid #eadfcf;"><span class="subcat-badge">${esc(s.name)}</span></td>
              <td style="padding:12px;border-bottom:1px solid #eadfcf;" class="muted">${esc(s.description || '—')}</td>
              <td style="padding:12px;border-bottom:1px solid #eadfcf;" class="muted" id="dishCount-${s.id}">Cargando...</td>
              <td style="padding:12px;border-bottom:1px solid #eadfcf;" class="muted" id="optCount-${s.id}">Cargando...</td>
              <td style="padding:12px;border-bottom:1px solid #eadfcf;text-align:right;">
                <div class="row-actions">
                  <button class="btn btn--primary btn--small" data-edit="${s.id}">Editar</button>
                  <button class="btn btn--danger btn--small" data-delete="${s.id}">Eliminar</button>
                </div>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
    // Load counts
    subcats.forEach(s => {
      loadDishCount(s.id);
      loadOptCount(s.id);
    });
    // Events
    $subcatsList.querySelectorAll('[data-edit]').forEach(b => {
      b.addEventListener('click', () => {
        const s = subcats.find(x => String(x.id) === b.dataset.edit);
        if (s) startEdit(s);
      });
    });
    $subcatsList.querySelectorAll('[data-delete]').forEach(b => {
      b.addEventListener('click', () => {
        const s = subcats.find(x => String(x.id) === b.dataset.delete);
        if (s) confirmDelete(s);
      });
    });
  }

  async function loadDishCount(id) {
    try {
      const res = await api(`/api/v1/subcategories/${id}/dishes`);
      const count = res.data ? res.data.length : 0;
      $('#dishCount-' + id).textContent = count + ' plato' + (count !== 1 ? 's' : '');
    } catch { $('#dishCount-' + id).textContent = '—'; }
  }

  async function loadOptCount(id) {
    try {
      const res = await api(`/api/v1/subcategories/${id}/options`);
      const count = res.data ? res.data.length : 0;
      $('#optCount-' + id).textContent = count + ' opción' + (count !== 1 ? 's' : '');
    } catch { $('#optCount-' + id).textContent = '—'; }
  }

  function startEdit(s) {
    editingId = s.id;
    editingSubcat = s;
    $subId.value = s.id;
    $subName.value = s.name;
    $subDesc.value = s.description || '';
    $('#formTitle').textContent = 'Editar subcategoría';
    $editor.style.display = 'block';
    tempOptions = [];
    selectedDishIds = new Set();
    renderOptions();
    renderDishes();
    $subName.focus();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function renderOptions() {
    if (!tempOptions.length) {
      $optList.innerHTML = '<p class="muted" style="text-align:center;padding:16px;">No hay opciones. Agrega al menos una.</p>';
      return;
    }
    $optList.innerHTML = tempOptions.map((opt, i) => `
      <div class="subcat-option-row">
        <span style="font-weight:600;color:#7a0c12;">${i + 1}.</span>
        <span style="flex:1;">${esc(opt.name)}</span>
        <span class="muted" style="font-size:.8rem;">orden: ${opt.sort_order}</span>
        <div class="sub-opt-actions">
          <button class="btn btn--ghost btn--small" data-opt-edit="${i}">Editar</button>
          <button class="btn btn--danger btn--small" data-opt-del="${i}">Eliminar</button>
        </div>
      </div>
    `).join('');
    $optList.querySelectorAll('[data-opt-edit]').forEach(b => {
      b.addEventListener('click', () => {
        const i = parseInt(b.dataset.optEdit);
        const newName = prompt('Nuevo nombre para la opción:', tempOptions[i].name);
        if (newName && newName.trim()) {
          tempOptions[i].name = newName.trim();
          renderOptions();
        }
      });
    });
    $optList.querySelectorAll('[data-opt-del]').forEach(b => {
      b.addEventListener('click', () => {
        const i = parseInt(b.dataset.optDel);
        if (confirm('¿Eliminar esta opción?')) {
          tempOptions.splice(i, 1);
          renderOptions();
        }
      });
    });
  }

  function renderDishes() {
    if (dishesLoading) {
      $dishBoxes.innerHTML = '<p class="muted">Cargando platos...</p>';
      return;
    }
    if (dishesLoadError) {
      $dishBoxes.innerHTML = `<p class="muted">No se pudieron cargar los platos: ${esc(dishesLoadError)}</p>`;
      return;
    }
    if (!allDishes.length) {
      $dishBoxes.innerHTML = '<p class="muted">No hay platos disponibles.</p>';
      return;
    }
    $dishBoxes.innerHTML = allDishes.map(d => {
      const checked = selectedDishIds.has(d.id) ? 'checked' : '';
      const cls = checked ? 'checked' : '';
      return `<label class="dish-checkbox ${cls}">
        <input type="checkbox" value="${d.id}" ${checked}> ${esc(d.name)}
        <span class="muted" style="margin-left:6px;font-size:.8rem;">${money(d.price)}</span>
      </label>`;
    }).join('');
    $dishBoxes.querySelectorAll('input').forEach(inp => {
      inp.addEventListener('change', (e) => {
        if (e.target.checked) selectedDishIds.add(parseInt(e.target.value));
        else selectedDishIds.delete(parseInt(e.target.value));
        renderDishes();
      });
    });
  }

  $('#addSubcat').addEventListener('click', () => {
    reset();
    $editor.style.display = 'block';
    $subName.focus();
  });

  $('#cancelEdit').addEventListener('click', reset);
  $('#cancelSubcat').addEventListener('click', reset);

  $('#addOptBtn').addEventListener('click', () => {
    const name = prompt('Nombre de la opción:');
    if (!name || !name.trim()) return;
    tempOptions.push({ name: name.trim(), sort_order: tempOptions.length + 1 });
    renderOptions();
  });

  $subForm().addEventListener('submit', async (e) => {
    e.preventDefault(); setMsg('');
    const name = $subName.value.trim();
    const desc = $subDesc.value.trim() || null;
    if (name.length < 2) { setMsg('El nombre debe tener al menos 2 caracteres.'); return; }
    const duplicate = subcats.find(sub =>
      sub.name.trim().toLowerCase() === name.toLowerCase() &&
      String(sub.id) !== String(editingId)
    );
    if (duplicate) {
      setMsg(`Ya existe la subcategoría "${duplicate.name}". Edita la existente o elige otro nombre.`);
      return;
    }
    if (!tempOptions.length) { setMsg('Debe agregar al menos una opción.'); return; }
    if (!selectedDishIds.size) { setMsg('Debe seleccionar al menos un plato.'); return; }
    try {
      const payload = { name, description: desc, dish_ids: Array.from(selectedDishIds) };
      if (editingId) {
        await api(`/api/v1/subcategories/${editingId}`, {
          method: 'PUT',
          body: JSON.stringify({ name, description: desc })
        });
        // Update options: delete all and recreate
        const existing = await api(`/api/v1/subcategories/${editingId}/options`);
        const opts = existing.data || [];
        for (const o of opts) {
          await api(`/api/v1/subcategories/options/${o.id}`, { method: 'DELETE' });
        }
        for (const opt of tempOptions) {
          await api(`/api/v1/subcategories/${editingId}/options`, {
            method: 'POST',
            body: JSON.stringify({ subcategory_id: editingId, name: opt.name, sort_order: opt.sort_order })
          });
        }
        setMsg('Subcategoría actualizada.', true);
        toast('Subcategoría actualizada');
      } else {
        const created = await api('/api/v1/subcategories', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        for (const opt of tempOptions) {
          await api(`/api/v1/subcategories/${created.data.id}/options`, {
            method: 'POST',
            body: JSON.stringify({ subcategory_id: created.data.id, name: opt.name, sort_order: opt.sort_order })
          });
        }
        setMsg('Subcategoría creada.', true);
        toast('Subcategoría creada');
      }
      reset(); await load();
    } catch (err) { setMsg(err.message); toast(err.message, 'error'); }
  });

  async function confirmDelete(s) {
    if (!confirm(`¿Eliminar la subcategoría "${s.name}"?`)) return;
    try {
      await api(`/api/v1/subcategories/${s.id}`, { method: 'DELETE' });
      toast('Subcategoría eliminada');
      await load();
    } catch (err) { toast(err.message, 'error'); }
  }

  $('#refresh').addEventListener('click', () => { setMsg(''); load(); });
  await load();
});