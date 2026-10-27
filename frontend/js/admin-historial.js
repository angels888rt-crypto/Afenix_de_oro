document.addEventListener('DOMContentLoaded', async () => {
  if (!Afenix.guardPage('ADMIN')) return;
  const { api, toast, esc, date } = Afenix;
  const body = document.querySelector('#history');
  const resultInfo = document.querySelector('#resultInfo');
  const emptyMsg = document.querySelector('#emptyMsg');
  const chips = Array.from(document.querySelectorAll('.filter-chip'));
  const table = document.querySelector('#historyTable');
  const toggleBtn = document.querySelector('#toggleHistory');

  let currentFilter = 'RECENT';
  const BATCH = 10;
  let allRows = [];
  let visibleCount = BATCH;
  let hasMoreOnServer = true;
  let hasReachedEnd = false;
  let isLoading = false;

  const labels = {
    ORDENES: 'Órdenes',
    PLATOS: 'Platos',
    LOGIN: 'Usuarios ingresados',
    USUARIOS: 'Usuarios',
    RECENT: 'Historial más reciente en general'
  };

  function setActive(filter) {
    currentFilter = filter;
    chips.forEach(c => {
      const isActive = c.dataset.filter === filter;
      c.classList.toggle('is-active', isActive);
      c.setAttribute('aria-selected', String(isActive));
    });
  }

  function setButtonState(action) {
    if (!toggleBtn) return;
    const iconMore = '▾';
    const iconLess = '▴';
    if (action === 'more') {
      toggleBtn.innerHTML = `<span class="toggle-icon">${iconMore}</span> <span class="toggle-text">Mostrar más</span>`;
      toggleBtn.dataset.action = 'more';
      toggleBtn.className = 'btn-historial btn-historial--more';
    } else {
      toggleBtn.innerHTML = `<span class="toggle-icon">${iconLess}</span> <span class="toggle-text">Mostrar menos</span>`;
      toggleBtn.dataset.action = 'less';
      toggleBtn.className = 'btn-historial btn-historial--less';
    }
    toggleBtn.style.display = 'inline-flex';
    toggleBtn.disabled = false;
    toggleBtn.style.opacity = '';
    toggleBtn.style.cursor = 'pointer';
  }

  function updateButton() {
    if (!toggleBtn) return;
    const total = allRows.length;
    if (total === 0) {
      toggleBtn.style.display = 'none';
      return;
    }
    // Sube y baja: comienza en 10 con Mostrar más, al llegar al final solo Mostrar menos hasta volver a 10
    if (hasReachedEnd) {
      // Ya llegamos al final alguna vez, ahora estamos bajando
      if (visibleCount <= BATCH) {
        // Volvimos al inicio, reinicia ciclo
        hasReachedEnd = false;
        setButtonState('more');
      } else {
        setButtonState('less');
      }
      toggleBtn.style.display = 'inline-flex';
      toggleBtn.disabled = false;
      return;
    }
    // Aún subiendo
    if (visibleCount < total) {
      setButtonState('more');
      return;
    }
    if (hasMoreOnServer) {
      setButtonState('more');
      return;
    }
    // Llegamos al final (visible == total y no hay más)
    if (total > BATCH) {
      hasReachedEnd = true;
      setButtonState('less');
    } else {
      // Total <= BATCH y ya mostramos todo: no hay paginación, mantener Mostrar más
      setButtonState('more');
      toggleBtn.disabled = true;
      toggleBtn.style.opacity = '0.6';
      toggleBtn.style.cursor = 'not-allowed';
    }
  }

  function render() {
    if (!allRows || !allRows.length) {
      body.innerHTML = '';
      if (emptyMsg) emptyMsg.hidden = false;
      if (table) table.style.display = 'none';
      resultInfo.textContent = `0 registros — ${labels[currentFilter] || currentFilter}`;
      if (toggleBtn) toggleBtn.style.display = 'none';
      return;
    }
    if (emptyMsg) emptyMsg.hidden = true;
    if (table) table.style.display = '';

    const toShow = allRows.slice(0, visibleCount);
    resultInfo.textContent = `${toShow.length} de ${allRows.length}${hasMoreOnServer ? '+' : ''} registros — ${labels[currentFilter] || currentFilter}`;

    body.innerHTML = toShow.map(r => {
      const cat = esc(r.category || '');
      const act = esc(r.action || '');
      const desc = esc(r.description || '');
      const entity = r.entity_name ? `${esc(r.entity_type || '')} ${r.entity_id ? '#' + r.entity_id : ''} — ${esc(r.entity_name)}` : (r.entity_id ? `${esc(r.entity_type || '')} #${r.entity_id}` : esc(r.entity_type || '—'));
      const who = r.performed_by_username ? esc(r.performed_by_username) : (r.performed_by ? `#${r.performed_by}` : '—');
      const when = date(r.created_at);
      return `<tr>
        <td title="${esc(r.created_at)}">${when}</td>
        <td><span class="badge-cat badge-cat--${cat}">${cat}</span></td>
        <td><span class="badge-action">${act}</span></td>
        <td style="white-space:normal;max-width:420px">${desc}</td>
        <td style="white-space:normal;max-width:200px">${entity}</td>
        <td>${who}</td>
      </tr>`;
    }).join('');

    updateButton();
  }

  async function fetchBatch(skip, limit) {
    const q = encodeURIComponent(currentFilter);
    const data = await api(`/api/v1/history?category=${q}&skip=${skip}&limit=${limit}`);
    return Array.isArray(data) ? data : [];
  }

  async function loadInitial() {
    if (isLoading) return;
    isLoading = true;
    try {
      resultInfo.textContent = 'Cargando...';
      body.innerHTML = '';
      allRows = [];
      visibleCount = BATCH;
      hasMoreOnServer = true;
      hasReachedEnd = false;

      const firstBatch = await fetchBatch(0, BATCH);
      firstBatch.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      allRows = firstBatch;
      if (firstBatch.length < BATCH) hasMoreOnServer = false;
      if (allRows.length < visibleCount) visibleCount = allRows.length;
      // Si no hay datos, visibleCount será 0, pero lo ajustamos a BATCH para la próxima carga
      if (visibleCount === 0 && allRows.length === 0) visibleCount = BATCH;

      render();
    } catch (e) {
      toast(e.message || 'No se pudo cargar el historial', 'error');
      resultInfo.textContent = 'Error al cargar';
      if (toggleBtn) toggleBtn.style.display = 'none';
    } finally {
      isLoading = false;
    }
  }

  async function handleToggle() {
    if (isLoading) return;
    const action = toggleBtn?.dataset.action || 'more';
    if (action === 'more') {
      if (visibleCount < allRows.length) {
        const remaining = allRows.length - visibleCount;
        const toAdd = Math.min(BATCH, remaining);
        visibleCount += toAdd;
        // Si acabamos de llegar al final y no hay más en servidor, marcar hasReachedEnd
        if (visibleCount >= allRows.length && !hasMoreOnServer && allRows.length > BATCH) {
          hasReachedEnd = true;
        }
        render();
        return;
      }
      if (visibleCount >= allRows.length && hasMoreOnServer) {
        isLoading = true;
        toggleBtn.innerHTML = `<span class="toggle-icon">…</span> <span class="toggle-text">Cargando...</span>`;
        toggleBtn.disabled = true;
        try {
          const nextBatch = await fetchBatch(allRows.length, BATCH);
          nextBatch.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
          if (nextBatch.length === 0) {
            hasMoreOnServer = false;
          } else {
            allRows = allRows.concat(nextBatch);
            if (nextBatch.length < BATCH) hasMoreOnServer = false;
          }
          const toAdd = Math.min(BATCH, allRows.length - visibleCount);
          if (toAdd > 0) visibleCount += toAdd;
          // Si tras el fetch ya estamos al final, marcar hasReachedEnd
          if (visibleCount >= allRows.length && !hasMoreOnServer && allRows.length > BATCH) {
            hasReachedEnd = true;
          }
          render();
        } catch (e) {
          toast(e.message || 'No se pudo cargar más', 'error');
        } finally {
          isLoading = false;
          if (toggleBtn) toggleBtn.disabled = false;
        }
        return;
      }
      if (visibleCount >= allRows.length && !hasMoreOnServer && allRows.length > BATCH) {
        hasReachedEnd = true;
        setButtonState('less');
        render();
      }
    } else if (action === 'less') {
      visibleCount = Math.max(BATCH, visibleCount - BATCH);
      if (visibleCount <= BATCH) {
        hasReachedEnd = false;
      }
      render();
    }
  }

  chips.forEach(chip => {
    chip.addEventListener('click', async () => {
      setActive(chip.dataset.filter);
      await loadInitial();
    });
  });

  document.querySelector('#refresh')?.addEventListener('click', loadInitial);
  if (toggleBtn) toggleBtn.addEventListener('click', handleToggle);

  setActive('RECENT');
  await loadInitial();
});
