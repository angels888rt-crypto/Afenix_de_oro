/* ============================================================
   AFENIX DE ORO — Gestión de Usuarios + Platillos
============================================================ */
document.addEventListener('DOMContentLoaded', () => {

  /* ---------- Control de acceso: solo administradores ---------- */
  const storedRole = (localStorage.getItem('afenix_role') || '').toUpperCase();
  const storedToken = localStorage.getItem('afenix_access_token');

  /* ---------- Utilidades ---------- */
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

  const API_USERS  = '/api/v1/users';
  const API_DISHES = '/api/v1/dishes';

  const token = () => localStorage.getItem('afenix_access_token');
  const authH = (extra = {}) => ({
    'Content-Type': 'application/json',
    ...extra,
    ...(token() ? { Authorization: `Bearer ${token()}` } : {}),
  });

  const escHtml = (s) => String(s).replace(/[&<>"']/g,
    (c) => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));

  const editIcon   = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>`;
  const deleteIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>`;

  /* ---------- Toasts ---------- */
  const toastStack = $('#toastStack');
  function showToast(type, msg) {
    if (!toastStack) return;
    const t = document.createElement('div');
    t.className = `toast toast--${type}`;
    t.innerHTML = `<span class="toast__icon" aria-hidden="true">${type === 'success' ? '✓' : '!'}</span>
                   <span class="toast__msg">${escHtml(msg)}</span>`;
    toastStack.appendChild(t);
    const remove = () => {
      t.classList.add('is-out');
      t.addEventListener('animationend', () => t.remove(), { once: true });
    };
    setTimeout(remove, 3600);
  }

  /* ---------- Header scroll + menú móvil ---------- */
  const header = $('#header');
  if (header) {
    window.addEventListener('scroll', () =>
      header.classList.toggle('is-scrolled', window.scrollY > 60), { passive: true });
  }
  const navToggle = $('#navToggle');
  const nav = $('#primaryNav');
  if (navToggle && nav) {
    const closeMenu = () => {
      nav.classList.remove('is-open');
      navToggle.classList.remove('is-open');
      navToggle.setAttribute('aria-expanded', 'false');
    };
    navToggle.addEventListener('click', () => {
      const open = nav.classList.toggle('is-open');
      navToggle.classList.toggle('is-open', open);
      navToggle.setAttribute('aria-expanded', String(open));
    });
    $$('.nav__link').forEach((l) => l.addEventListener('click', closeMenu));
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeMenu(); });
  }

  /* ============================================================
     SECCIÓN 1 — AUTENTICACIÓN + TOGGLE DE MÓDULO
  ============================================================ */
  const accessScreen = $('#accessScreen');
  const usersModule  = $('#usersModule');
  const loginForm    = $('#loginForm');
  const loginError   = $('#loginError');
  const logoutItem   = $('#logoutItem');
  const logoutBtn    = $('#logoutBtn');

  function showModule() {
    if (accessScreen) accessScreen.hidden = true;
    if (usersModule)  usersModule.hidden  = false;
    if (logoutItem)   logoutItem.hidden   = false;
    renderUsers();
    updateStats();
    loadDishes();
    if (window.AOS) AOS.refreshHard();
  }

  function showLogin() {
    if (usersModule)  usersModule.hidden  = true;
    if (logoutItem)   logoutItem.hidden   = true;
    if (accessScreen) accessScreen.hidden = false;
    if (loginForm)    loginForm.reset();
    if (loginError)   loginError.hidden   = true;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  /* Mostrar/ocultar contraseñas */
  $$('[data-toggle-pass]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const input = $('#' + btn.dataset.togglePass);
      if (!input) return;
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.textContent = show ? 'Ocultar' : 'Ver';
    });
  });

  /* Login — permite cualquier usuario válido y activo, sin importar el rol (para Auxiliares y recargas) */
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const user = $('#adminUser')?.value.trim();
      const pass = $('#adminPass')?.value;
      try {
        const res = await fetch(`${API_USERS}/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: user, password: pass }),
        });
        const payload = await res.json();
        if (!res.ok || !payload.success)
          throw new Error(payload.message || 'Credenciales incorrectas.');
        const role = (payload.data?.role || 'CAMARERO').toUpperCase();
        // No bloqueamos por rol aquí; cualquier usuario válido puede iniciar sesión
        // La sección Auxiliares es accesible con cualquier rol autenticado
        localStorage.setItem('afenix_access_token',  payload.data.access_token);
        localStorage.setItem('afenix_refresh_token', payload.data.refresh_token);
        localStorage.setItem('afenix_display_name',  payload.data.display_name || user);
        localStorage.setItem('afenix_role', role);
        if (loginError) loginError.hidden = true;
        showModule();
        showToast('success', `Bienvenido, ${payload.data.display_name || user}.`);
        await loadUsers();
      } catch (err) {
        if (loginError) { loginError.hidden = false; loginError.textContent = err.message; }
      }
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      localStorage.removeItem('afenix_access_token');
      localStorage.removeItem('afenix_refresh_token');
      localStorage.removeItem('afenix_role');
      localStorage.removeItem('afenix_display_name');
      window.location.href = '/';
    });
  }

  /* ============================================================
     SECCIÓN 2 — USUARIOS
  ============================================================ */
  let users = [];

  const normalizeUser = (u) => ({
    id:       String(u.id),
    fullName: u.full_name || u.username,
    username: u.username,
    role:     u.role === 'ADMIN' ? 'Administrador' : 'Mesero',
    status:   u.is_active ? 'Activo' : 'Inactivo',
  });

  const toBackendRole = (r) =>
    r === 'Administrador' ? 'ADMIN' : 'CAMARERO';

  async function loadUsers() {
    try {
      const res = await fetch(API_USERS, { headers: authH() });
      const p   = await res.json();
      if (!res.ok || !p.success) throw new Error(p.message || 'Error al cargar usuarios.');
      users = (p.data || []).map(normalizeUser);
    } catch (err) {
      showToast('error', err.message);
      users = [];
    }
    renderUsers();
    updateStats();
  }

  /* --- Tabla de usuarios --- */
  const tbody      = $('#usersTbody');
  const usersEmpty = $('#usersEmpty');
  const tableCount = $('#tableCount');
  const userSearch = $('#userSearch');
  let   userQ      = '';

  const rowTemplate = (u) => `
    <tr data-id="${u.id}">
      <td class="table__user-name">${escHtml(u.fullName)}</td>
      <td class="table__username">@${escHtml(u.username)}</td>
      <td><span class="tag tag--${u.role.toLowerCase()}">${u.role}</span></td>
      <td><span class="status-pill status-pill--${u.status.toLowerCase()}">${u.status}</span></td>
      <td class="table__actions-col"><div class="row-actions">
        <button class="icon-btn icon-btn--edit"   type="button" data-u-action="edit"
                aria-label="Editar ${escHtml(u.fullName)}">${editIcon}</button>
        <button class="icon-btn icon-btn--delete" type="button" data-u-action="delete"
                aria-label="Eliminar ${escHtml(u.fullName)}">${deleteIcon}</button>
      </div></td>
    </tr>`;

  function renderUsers() {
    if (!tbody) return;
    const visible = users.filter((u) =>
      u.fullName.toLowerCase().includes(userQ) || u.username.toLowerCase().includes(userQ));
    tbody.innerHTML = visible.map(rowTemplate).join('');
    if (usersEmpty)  usersEmpty.hidden  = visible.length !== 0;
    if (tableCount)  tableCount.textContent = `${users.length} usuario${users.length !== 1 ? 's' : ''}`;
  }

  if (userSearch) userSearch.addEventListener('input', (e) => { userQ = e.target.value.trim().toLowerCase(); renderUsers(); });

  /* --- Formulario de usuarios --- */
  const userForm      = $('#userForm');
  const formTitle     = $('#formTitle');
  const submitBtn     = $('#submitBtn');
  const cancelEditBtn = $('#cancelEditBtn');
  const userIdField   = $('#userId');
  const ROLES         = ['Administrador', 'Mesero'];

  const uFields = {
    fullName: $('#fullName'), username: $('#username'),
    password: $('#password'), confirmPassword: $('#confirmPassword'), role: $('#role'),
  };

  const setUError = (name, msg) => {
    const span = $(`[data-error-for="${name}"]`);
    if (span) span.textContent = msg || '';
    if (uFields[name]) uFields[name].classList.toggle('is-invalid', Boolean(msg));
  };
  const clearUErrors = () => Object.keys(uFields).forEach((n) => setUError(n, ''));

  const getStatus  = ()    => $('input[name="status"]:checked')?.value || 'Activo';
  const setStatus  = (v)   => { const t = $(`input[name="status"][value="${v}"]`); if (t) t.checked = true; };
  const isEditingU = ()    => Boolean(userIdField?.value);

  function validateUserForm() {
    clearUErrors(); let ok = true;
    const fn = uFields.fullName.value.trim();
    const un = uFields.username.value.trim();
    const pw = uFields.password.value;
    const cp = uFields.confirmPassword.value;
    const ro = uFields.role.value;
    if (!fn) { setUError('fullName', 'El nombre es obligatorio.'); ok = false; }
    if (!un) { setUError('username', 'El usuario es obligatorio.'); ok = false; }
    else if (/\s/.test(un)) { setUError('username', 'Sin espacios.'); ok = false; }
    else if (users.some((u) => u.username.toLowerCase() === un.toLowerCase() && u.id !== userIdField.value))
      { setUError('username', 'Usuario ya existe.'); ok = false; }
    if (!isEditingU() || pw || cp) {
      if (!isEditingU() && !pw) { setUError('password', 'La contraseña es obligatoria.'); ok = false; }
      else if (pw.length > 0 && pw.length < 4) { setUError('password', 'Mínimo 4 caracteres.'); ok = false; }
      if (pw !== cp) { setUError('confirmPassword', 'Las contraseñas no coinciden.'); ok = false; }
    }
    if (!ROLES.includes(ro)) { setUError('role', 'Selecciona un rol.'); ok = false; }
    return ok;
  }

  function resetUserForm() {
    if (userForm) userForm.reset();
    if (userIdField) userIdField.value = '';
    clearUErrors(); setStatus('Activo');
    if (formTitle)     formTitle.textContent  = 'Registrar nuevo usuario';
    if (submitBtn)     submitBtn.textContent  = 'Registrar usuario';
    if (cancelEditBtn) cancelEditBtn.hidden   = true;
    if (uFields.password) uFields.password.placeholder = '••••••••';
    if (uFields.confirmPassword) uFields.confirmPassword.placeholder = '••••••••';
  }

  function startUserEdit(id) {
    const u = users.find((x) => x.id === id);
    if (!u) return;
    userIdField.value = u.id;
    uFields.fullName.value = u.fullName;
    uFields.username.value = u.username;
    uFields.password.value = '';
    uFields.confirmPassword.value = '';
    uFields.role.value = u.role;
    setStatus(u.status); clearUErrors();
    if (formTitle)  formTitle.textContent = 'Editar usuario';
    if (submitBtn)  submitBtn.textContent = 'Guardar cambios';
    if (cancelEditBtn) cancelEditBtn.hidden = false;
    uFields.password.placeholder = 'Dejar en blanco para no cambiar';
    uFields.confirmPassword.placeholder = 'Dejar en blanco para no cambiar';
    userForm?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    uFields.fullName.focus();
  }

  if (cancelEditBtn) cancelEditBtn.addEventListener('click', resetUserForm);

  if (userForm) {
    userForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!validateUserForm()) { showToast('error', 'Revisa los campos.'); return; }
      const data = {
        full_name: uFields.fullName.value.trim(),
        username:  uFields.username.value.trim(),
        role:      toBackendRole(uFields.role.value),
        password:  uFields.password.value || undefined,
        is_active: getStatus() === 'Activo',
      };
      try {
        let res;
        if (isEditingU()) {
          res = await fetch(`${API_USERS}/${userIdField.value}/admin`,
            { method: 'PUT', headers: authH(), body: JSON.stringify(data) });
        } else {
          res = await fetch(`${API_USERS}/register`,
            { method: 'POST', headers: authH(), body: JSON.stringify({ ...data, password: uFields.password.value }) });
        }
        const p = await res.json();
        if (!res.ok || !p.success) throw new Error(p.message || 'Error al guardar.');
        showToast('success', `Usuario "${data.full_name}" ${isEditingU() ? 'actualizado' : 'registrado'}.`);
        resetUserForm(); await loadUsers();
      } catch (err) { showToast('error', err.message); }
    });
  }

  /* --- Modal eliminar usuario --- */
  const confirmModal    = $('#confirmModal');
  const modalText       = $('#modalText');
  const confirmDelBtn   = $('#confirmDeleteBtn');
  let   pendingDelUser  = null;

  const openUserModal  = (id) => {
    const u = users.find((x) => x.id === id); if (!u) return;
    pendingDelUser = id;
    if (modalText)    modalText.textContent = `¿Eliminar a "${u.fullName}" (@${u.username})?`;
    if (confirmModal) confirmModal.hidden   = false;
    confirmDelBtn?.focus();
  };
  const closeUserModal = () => { if (confirmModal) confirmModal.hidden = true; pendingDelUser = null; };

  if (confirmModal) confirmModal.addEventListener('click', (e) => { if (e.target.dataset.closeModal !== undefined) closeUserModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && confirmModal && !confirmModal.hidden) closeUserModal(); });

  if (confirmDelBtn) {
    confirmDelBtn.addEventListener('click', async () => {
      if (!pendingDelUser) return;
      const id = pendingDelUser; const u = users.find((x) => x.id === id);
      if (userIdField?.value === id) resetUserForm();
      try {
        const res = await fetch(`${API_USERS}/${id}`, { method: 'DELETE', headers: authH() });
        if (!res.ok) { const p = await res.json().catch(() => ({})); throw new Error(p.message || 'No se pudo eliminar.'); }
        closeUserModal(); await loadUsers();
        showToast('success', `Usuario "${u?.fullName || ''}" eliminado.`);
      } catch (err) { closeUserModal(); showToast('error', err.message); }
    });
  }

  if (tbody) {
    tbody.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-u-action]'); if (!btn) return;
      const id = btn.closest('tr').dataset.id;
      if (btn.dataset.uAction === 'edit')   startUserEdit(id);
      if (btn.dataset.uAction === 'delete') openUserModal(id);
    });
  }

  /* --- Contadores de usuarios --- */
  const statTotal     = $('#statTotal');
  const statCocineros = $('#statCocineros');
  const statMeseros   = $('#statMeseros');
  const statActivos   = $('#statActivos');

  function updateStats() {
    if (statTotal)     statTotal.textContent     = users.length;
    if (statCocineros) statCocineros.textContent = users.filter((u) => u.role === 'Administrador').length;
    if (statMeseros)   statMeseros.textContent   = users.filter((u) => u.role === 'Mesero').length;
    if (statActivos)   statActivos.textContent   = users.filter((u) => u.status === 'Activo').length;
  }

  /* ============================================================
     SECCIÓN 3 — PLATILLOS
     Formulario completamente independiente del loginForm.
     El submit se registra una sola vez aquí, con stopPropagation.
  ============================================================ */
  let dishes       = [];
  let dishEditId   = null;
  let dishQ        = '';

  const normalizeDish = (d) => ({
    id:            String(d.id),
    name:          d.name          || '',
    category:      d.category      || '',
    price:         Math.max(1, Math.round((d.price || 0) / 100)),
    stock:         typeof d.stock_quantity === 'number' ? d.stock_quantity : 0,
    estimatedTime: d.estimated_time ? Math.round(d.estimated_time / 60) : 15,
    description:   d.description   || '',
  });

  const dishState = (s) => s <= 0 ? 'agotado' : s <= 5 ? 'pocas' : 'disponible';

  async function loadDishes() {
    try {
      const res = await fetch(`${API_DISHES}?limit=100`, { headers: authH() });
      const p   = await res.json();
      if (!res.ok || !p.success) throw new Error(p.message || 'Error al cargar platillos.');
      dishes = (p.data || []).map(normalizeDish);
    } catch (err) { console.warn(err); dishes = []; }
    renderDishTable();
    updateDishStats();
  }

  /* --- DOM refs --- */
  const dishForm      = $('#dishForm');
  const dishFormTitle = $('#dishFormTitle');
  const dishSubmitBtn = $('#dishSubmitBtn');
  const dishCancelBtn = $('#dishCancelBtn');
  const dishIdField   = $('#dishId');
  const dishName      = $('#dishName');
  const dishCategory  = $('#dishCategory');
  const dishPrice     = $('#dishPrice');
  const dishStock     = $('#dishStock');
  const dishTime      = $('#dishTime');
  const dishDesc      = $('#dishDesc');
  const dishFeedErr   = $('#dishFormError');
  const dishFeedOk    = $('#dishFormOk');
  const dishSearch    = $('#dishSearch');
  const dishCount     = $('#dishTableCount');
  const dishTbody     = $('#dishTbody');
  const dishEmpty     = $('#dishEmpty');
  const dishStatTot   = $('#dishStatTotal');
  const dishStatDis   = $('#dishStatDisp');
  const dishStatLow   = $('#dishStatPocas');
  const dishStatOut   = $('#dishStatAgot');

  /* --- Feedback --- */
  const showDishErr = (m) => { if (dishFeedErr) { dishFeedErr.textContent = m; dishFeedErr.hidden = false; } if (dishFeedOk) dishFeedOk.hidden = true; };
  const showDishOk  = (m) => { if (dishFeedOk)  { dishFeedOk.textContent  = m; dishFeedOk.hidden  = false; } if (dishFeedErr) dishFeedErr.hidden = true; setTimeout(() => { if (dishFeedOk) dishFeedOk.hidden = true; }, 3500); };
  const clearDishFb = ()  => { if (dishFeedErr) { dishFeedErr.hidden = true; dishFeedErr.textContent = ''; } if (dishFeedOk) { dishFeedOk.hidden = true; dishFeedOk.textContent = ''; } };

  /* --- Validación --- */
  const setDE = (k, m) => { const el = $(`[data-dish-error="${k}"]`); if (el) el.textContent = m || ''; };
  const clearDE = () => ['name','category','price','time'].forEach((k) => setDE(k, ''));

  function validateDish() {
    clearDE(); let ok = true;
    if (!dishName?.value.trim())     { setDE('name',     'Obligatorio.');       ok = false; }
    if (!dishCategory?.value.trim()) { setDE('category', 'Obligatorio.');       ok = false; }
    if (!(Number(dishPrice?.value) >= 1)) { setDE('price', 'Precio ≥ 1.');      ok = false; }
    if (!(Number(dishTime?.value)  >= 1)) { setDE('time',  'Tiempo ≥ 1 min.');  ok = false; }
    return ok;
  }

  /* --- Render tabla --- */
  const stateLabel = { disponible: 'Disponible', pocas: 'Pocas uds.', agotado: 'Agotado' };
  const statePill  = { disponible: 'status-pill--activo', pocas: 'dish-pill--low', agotado: 'status-pill--inactivo' };

  function renderDishTable() {
    if (!dishTbody) return;
    const vis = dishes.filter((d) =>
      d.name.toLowerCase().includes(dishQ) || d.category.toLowerCase().includes(dishQ));
    if (dishCount) dishCount.textContent = `${dishes.length} platillo${dishes.length !== 1 ? 's' : ''}`;
    if (!vis.length) { dishTbody.innerHTML = ''; if (dishEmpty) dishEmpty.hidden = false; return; }
    if (dishEmpty) dishEmpty.hidden = true;
    dishTbody.innerHTML = vis.map((d) => {
      const st = dishState(d.stock);
      return `<tr data-dish-id="${d.id}">
        <td class="table__user-name">${escHtml(d.name)}</td>
        <td class="table__username">${escHtml(d.category)}</td>
        <td>$${d.price}</td>
        <td>${d.stock}</td>
        <td><span class="status-pill ${statePill[st]}">${stateLabel[st]}</span></td>
        <td class="table__actions-col"><div class="row-actions">
          <button class="icon-btn icon-btn--edit" type="button" data-d-action="edit" aria-label="Editar ${escHtml(d.name)}">${editIcon}</button>
        </div></td>
      </tr>`;
    }).join('');
  }

  function updateDishStats() {
    const c = { disponible: 0, pocas: 0, agotado: 0 };
    dishes.forEach((d) => c[dishState(d.stock)]++);
    if (dishStatTot) dishStatTot.textContent = dishes.length;
    if (dishStatDis) dishStatDis.textContent = c.disponible;
    if (dishStatLow) dishStatLow.textContent = c.pocas;
    if (dishStatOut) dishStatOut.textContent = c.agotado;
  }

  if (dishSearch) dishSearch.addEventListener('input', (e) => { dishQ = e.target.value.trim().toLowerCase(); renderDishTable(); });

  /* --- Delegación tabla --- */
  if (dishTbody) {
    dishTbody.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-d-action]'); if (!btn) return;
      const id = btn.closest('tr').dataset.dishId;
      if (btn.dataset.dAction === 'edit') startDishEdit(id);
    });
  }

  /* --- Editar / Reset formulario --- */
  function startDishEdit(id) {
    const d = dishes.find((x) => x.id === id); if (!d) return;
    dishEditId = id;
    if (dishIdField)   dishIdField.value   = id;
    if (dishName)      dishName.value      = d.name;
    if (dishCategory)  dishCategory.value  = d.category;
    if (dishPrice)     dishPrice.value     = d.price;
    if (dishStock)     dishStock.value     = d.stock;
    if (dishTime)      dishTime.value      = d.estimatedTime;
    if (dishDesc)      dishDesc.value      = d.description;
    clearDishFb(); clearDE();
    if (dishFormTitle) dishFormTitle.textContent = 'Editar platillo';
    if (dishSubmitBtn) dishSubmitBtn.textContent = 'Guardar cambios';
    if (dishCancelBtn) dishCancelBtn.hidden = false;
    dishForm?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    dishName?.focus();
  }

  function resetDishForm() {
    dishEditId = null;
    if (dishForm)    dishForm.reset();
    if (dishIdField) dishIdField.value  = '';
    if (dishStock)   dishStock.value    = '10';
    clearDishFb(); clearDE();
    if (dishFormTitle) dishFormTitle.textContent = 'Agregar platillo';
    if (dishSubmitBtn) dishSubmitBtn.textContent = 'Agregar platillo';
    if (dishCancelBtn) dishCancelBtn.hidden = true;
  }

  if (dishCancelBtn) dishCancelBtn.addEventListener('click', (e) => { e.preventDefault(); resetDishForm(); });

  /* --- Submit del formulario de platillos ---
     Usa click en el botón (type="button") en lugar de form submit,
     para evitar cualquier propagación nativa del navegador.          */
  async function handleDishSave() {
    clearDishFb();
    if (!validateDish()) return;

    const body = {
      name:           dishName.value.trim(),
      category:       dishCategory.value.trim(),
      price:          Math.round(Number(dishPrice.value) * 100),
      stock_quantity: Math.max(0, parseInt(dishStock?.value || '0', 10)),
      estimated_time: Math.round(Number(dishTime.value) * 60),
      description:    dishDesc?.value.trim() || undefined,
      is_available:   true,
    };

    if (dishSubmitBtn) { dishSubmitBtn.disabled = true; dishSubmitBtn.style.opacity = '0.7'; }

    try {
      let res;
      if (dishEditId) {
        res = await fetch(`${API_DISHES}/${dishEditId}`,
          { method: 'PUT', headers: authH(), body: JSON.stringify(body) });
      } else {
        res = await fetch(API_DISHES,
          { method: 'POST', headers: authH(), body: JSON.stringify(body) });
      }

      const payload = await res.json();
      if (!res.ok || !payload.success)
        throw new Error(payload.message || 'Error al guardar el platillo.');

      const saved = normalizeDish(payload.data);
      if (dishEditId) {
        const idx = dishes.findIndex((d) => d.id === dishEditId);
        if (idx !== -1) dishes[idx] = saved;
        showToast('success', `"${saved.name}" actualizado.`);
        showDishOk(`"${saved.name}" actualizado correctamente.`);
      } else {
        dishes.push(saved);
        showToast('success', `"${saved.name}" agregado al menú.`);
        showDishOk(`"${saved.name}" agregado correctamente.`);
      }

      resetDishForm();
      renderDishTable();
      updateDishStats();

    } catch (err) {
      showDishErr(err.message || 'No se pudo guardar el platillo.');
      showToast('error', err.message || 'No se pudo guardar.');
    } finally {
      if (dishSubmitBtn) { dishSubmitBtn.disabled = false; dishSubmitBtn.style.opacity = ''; }
    }
  }

  /* Bloquea cualquier submit nativo del dishForm por si acaso */
  if (dishForm) {
    dishForm.addEventListener('submit', (e) => { e.preventDefault(); e.stopImmediatePropagation(); });
  }

  /* Click en el botón guardar */
  if (dishSubmitBtn) {
    dishSubmitBtn.addEventListener('click', (e) => { e.preventDefault(); handleDishSave(); });
  }

  /* Enter en cualquier input del form también guarda */
  [dishName, dishCategory, dishPrice, dishStock, dishTime].forEach((inp) => {
    if (!inp) return;
    inp.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); handleDishSave(); }
    });
  });

  /* ============================================================
     INICIALIZACIÓN
  ============================================================ */
  resetUserForm();

  // Tras recarga, permite iniciar sesión a cualquier usuario válido y activo,
  // sin importar el rol, siempre que tenga un token (para Auxiliares).
  // No redirigimos automáticamente a /index.html por rol no ADMIN.
  if (storedToken) {
    // Token existe: intenta mostrar el módulo; el backend validará permisos reales
    // Si el token es inválido/expirado, loadUsers() fallará y se mostrará login
    showModule();
    loadUsers();
  } else {
    showLogin();
  }

  if (window.AOS) AOS.init({ duration: 700, easing: 'ease-out-cubic', once: true, offset: 60 });

}); // fin DOMContentLoaded
