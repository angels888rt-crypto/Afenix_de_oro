document.addEventListener('DOMContentLoaded', async () => {
  if (!Afenix.guardPage('ADMIN')) return;

  const $ = (s) => document.querySelector(s);
  const { api, toast, esc } = Afenix;
  let users = [];
  let editing = null;
  let userToDelete = null;
  const roleNames = { ADMIN: 'Administrador', CAMARERO: 'Mesero', CAJERO: 'Cajero', MONITOR: 'Monitor' };

  function msg(text, ok = false) {
    const e = $('#msg');
    e.hidden = !text;
    e.textContent = text;
    e.className = `form-message${ok ? ' ok' : ''}`;
  }

  function reset() {
    editing = null;
    $('#userForm').reset();
    $('#userId').value = '';
    $('#formTitle').textContent = 'Registrar usuario';
    $('#save').textContent = 'Registrar usuario';
    $('#cancel').hidden = true;
    $('#editor').classList.remove('editing');
    $('#editNote').hidden = true;
  }

  function start(u) {
    editing = u;
    $('#userId').value = u.id;
    $('#fullName').value = u.full_name || '';
    $('#username').value = u.username || '';
    $('#password').value = '';
    $('#role').value = u.role || 'CAMARERO';
    $('#phone').value = u.phone || '';
    $('#active').value = String(u.is_active);
    $('#formTitle').textContent = 'Editar usuario';
    $('#save').textContent = 'Guardar cambios';
    $('#cancel').hidden = false;
    $('#editor').classList.add('editing');
    $('#editNote').hidden = false;
    $('#fullName').focus();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function openDeleteModal(u) {
    userToDelete = u;
    $('#deleteMessage').textContent = `Desea eliminar el usuario "${u.full_name || u.username}"?`;
    $('#deleteModal').hidden = false;
    document.body.classList.add('modal-open');
  }

  function closeDeleteModal() {
    userToDelete = null;
    $('#deleteModal').hidden = true;
    document.body.classList.remove('modal-open');
  }

  async function load() {
    try {
      users = (await api('/api/v1/users?limit=100')) || [];
      $('#users').innerHTML = users.map(u => `
        <tr>
          <td>${esc(u.full_name)}</td>
          <td>@${esc(u.username)}</td>
          <td>${esc(roleNames[u.role] || u.role)}</td>
          <td>${u.is_active ? 'Activo' : 'Inactivo'}</td>
          <td>
            <div class="row-actions">
              <button class="btn btn--primary btn--small" data-edit="${u.id}">Editar</button>
              <button class="btn btn--danger btn--small" data-delete="${u.id}" type="button">Eliminar</button>
            </div>
          </td>
        </tr>
      `).join('') || '<tr><td colspan="5">No hay usuarios.</td></tr>';
    } catch (e) {
      toast(e.message, 'error');
    }
  }

  $('#users').addEventListener('click', (e) => {
    const deleteBtn = e.target.closest('[data-delete]');
    if (deleteBtn) {
      const u = users.find((x) => String(x.id) === String(deleteBtn.dataset.delete));
      if (u) openDeleteModal(u);
      return;
    }

    const editBtn = e.target.closest('[data-edit]');
    if (editBtn) {
      const u = users.find((x) => String(x.id) === String(editBtn.dataset.edit));
      if (u) start(u);
    }
  });

  $('#cancel').addEventListener('click', reset);
  $('#refresh').addEventListener('click', () => { msg(''); load(); });
  $('#closeDeleteModal').addEventListener('click', closeDeleteModal);
  $('#cancelDelete').addEventListener('click', closeDeleteModal);
  $('#deleteModal').addEventListener('click', (e) => {
    if (e.target.id === 'deleteModal') closeDeleteModal();
  });

  $('#confirmDelete').addEventListener('click', async () => {
    if (!userToDelete) return;

    try {
      await api(`/api/v1/users/${userToDelete.id}`, { method: 'DELETE' });
      toast('Usuario eliminado correctamente');
      msg(`Usuario ${userToDelete.full_name || userToDelete.username} eliminado.`, true);
      closeDeleteModal();
      await load();
    } catch (err) {
      toast(err.message, 'error');
      msg(err.message);
      closeDeleteModal();
    }
  });

  $('#userForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const data = {
      username: $('#username').value.trim(),
      full_name: $('#fullName').value.trim(),
      role: $('#role').value,
      is_active: $('#active').value === 'true',
      phone: $('#phone').value.trim() || null,
    };

    const pass = $('#password').value;
    if (!editing && pass.length < 8) {
      msg('La contraseña debe tener al menos 8 caracteres.');
      return;
    }

    if (pass) data.password = pass;

    try {
      if (editing) {
        await api(`/api/v1/users/${editing.id}/admin`, {
          method: 'PUT',
          body: JSON.stringify(data),
        });
      } else {
        await api('/api/v1/users/register', {
          method: 'POST',
          body: JSON.stringify({ ...data, password: pass }),
        });
      }

      msg(editing ? 'Usuario actualizado.' : 'Usuario registrado.', true);
      toast('Operacion completada');
      reset();
      load();
    } catch (err) {
      msg(err.message);
    }
  });

  load();
});