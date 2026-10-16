/* ============================================================
   FÉNIX DE ORO — Lógica del formulario de inicio de sesión
   Solo frontend: validación visual y estados de la interfaz.
   La autenticación real se conectará después a la API.
============================================================ */

(function () {
  'use strict';

  function initLogin() {
    const form = document.getElementById('loginForm');
    const submitBtn = document.getElementById('submitBtn');
    const alertBox = document.getElementById('formAlert');
    const alertText = document.getElementById('formAlertText');
    const toggleBtn = document.getElementById('togglePassword');
    const passInput = document.getElementById('password');
    const yearEl = document.getElementById('year');
    if (yearEl) yearEl.textContent = new Date().getFullYear();
    // Reset estado visual tras recarga/bfcache (evita botón bloqueado)
    if (submitBtn) {
      submitBtn.classList.remove('is-loading');
      submitBtn.removeAttribute('aria-busy');
      submitBtn.disabled = false;
    }
    if (alertBox) alertBox.hidden = true;
    // Si no hay formulario (página distinta), salir
    if (!form || !submitBtn || !alertBox || !alertText || !passInput) return;

  /* ---------- Definición de campos y reglas de validación ---------- */
  const fields = [
    {
      input: document.getElementById('usuario'),
      wrapper: document.getElementById('fieldUser'),
      error: document.getElementById('errorUser'),
      validate: (value) => {
        if (!value) return 'Ingresa tu usuario.';
        if (value.length < 3) return 'El usuario debe tener al menos 3 caracteres.';
        return '';
      }
    },
    {
      input: passInput,
      wrapper: document.getElementById('fieldPass'),
      error: document.getElementById('errorPass'),
      validate: (value) => {
        if (!value) return 'Ingresa tu contraseña.';
        if (value.length < 6) return 'La contraseña debe tener al menos 6 caracteres.';
        return '';
      }
    }
  ];

  /* ---------- Utilidades de estado visual ---------- */
  function setFieldError(field, message) {
    field.wrapper.classList.add('is-invalid');
    field.input.setAttribute('aria-invalid', 'true');
    field.error.textContent = message;
  }

  function clearFieldError(field) {
    field.wrapper.classList.remove('is-invalid');
    field.input.removeAttribute('aria-invalid');
    field.error.textContent = '';
  }

  function showAlert(message) {
    alertText.textContent = message;
    alertBox.hidden = false;
  }

  function hideAlert() {
    alertBox.hidden = true;
  }

  /* ---------- Validación de un campo ---------- */
  function validateField(field) {
    const message = field.validate(field.input.value.trim());
    if (message) {
      setFieldError(field, message);
      return false;
    }
    clearFieldError(field);
    return true;
  }

  /* Limpia el error mientras el usuario corrige */
  fields.forEach((field) => {
    if (!field.input) return;
    field.input.addEventListener('input', () => {
      if (field.wrapper.classList.contains('is-invalid')) {
        clearFieldError(field);
        hideAlert();
      }
    });
    field.input.addEventListener('blur', () => {
      if (field.input.value.trim()) validateField(field);
    });
  });

  /* ---------- Mostrar / ocultar contraseña - mejorado ---------- */
  if (toggleBtn && passInput) {
    // Evitar listeners duplicados en pageshow/bfcache
    if (!toggleBtn.dataset.toggleBound) {
      toggleBtn.dataset.toggleBound = 'true';
      toggleBtn.addEventListener('click', () => {
        const isVisible = passInput.type === 'text';
        // Preservar posición del cursor/selección
        const start = passInput.selectionStart;
        const end = passInput.selectionEnd;
        passInput.type = isVisible ? 'password' : 'text';
        // Restaurar cursor
        try {
          if (typeof start === 'number' && typeof end === 'number') {
            passInput.setSelectionRange(start, end);
          }
        } catch {}
        const nowVisible = !isVisible;
        toggleBtn.setAttribute('aria-pressed', String(nowVisible));
        toggleBtn.setAttribute('aria-label', nowVisible ? 'Ocultar contraseña' : 'Mostrar contraseña');
        toggleBtn.setAttribute('title', nowVisible ? 'Ocultar contraseña' : 'Mostrar contraseña');
        passInput.focus({ preventScroll: true });
      });
      // Soporte teclado ya incluido en <button>, pero asegurar accesibilidad
      toggleBtn.setAttribute('title', 'Mostrar contraseña');
      toggleBtn.setAttribute('aria-controls', 'password');
    }
    // Sincronizar estado visual inicial (por si el navegador autocompleta)
    if (passInput.type === 'text') {
      toggleBtn.setAttribute('aria-pressed', 'true');
      toggleBtn.setAttribute('aria-label', 'Ocultar contraseña');
    }
  }

  function redirectByRole(role) {
    const resolvedRole = (role || 'CAMARERO').toUpperCase();
    const routes = { ADMIN: '/admin.html', CAMARERO: '/mesero.html', CAJERO: '/cajero.html', MONITOR: '/monitor-ordenes.html' };
    window.location.href = routes[resolvedRole] || '/panel.html';
  }

  /* ---------- Envío del formulario ---------- */
  // Evita duplicar listeners tras bfcache/recarga
  if (form && !form.dataset.loginBound) {
    form.dataset.loginBound = 'true';
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      hideAlert();

      const results = fields.map(validateField);
      const isValid = results.every(Boolean);

      if (!isValid) {
        showAlert('Completa correctamente los campos marcados para continuar.');
        const firstInvalid = fields.find((f) => f.wrapper.classList.contains('is-invalid'));
        if (firstInvalid) firstInvalid.input.focus({ preventScroll: true });
        return;
      }

      const username = fields[0].input.value.trim();
      const credentials = {
        username,
        password: passInput.value
      };

      submitBtn.classList.add('is-loading');
      submitBtn.setAttribute('aria-busy', 'true');

      try {
        const response = await fetch('/api/v1/users/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(credentials)
        });

        const payload = await response.json();
        if (!response.ok || !payload.success) {
          throw new Error(payload.message || 'No se pudo iniciar sesión.');
        }

        const resolvedRole = (payload.data.role || 'CAMARERO').toUpperCase();
        localStorage.setItem('afenix_access_token', payload.data.access_token);
        localStorage.setItem('afenix_refresh_token', payload.data.refresh_token);
        localStorage.setItem('afenix_display_name', payload.data.display_name || username);
        localStorage.setItem('afenix_role', resolvedRole);

        redirectByRole(resolvedRole);
      } catch (error) {
        showAlert(error.message || 'No se pudo conectar con el backend.');
      } finally {
        submitBtn.classList.remove('is-loading');
        submitBtn.removeAttribute('aria-busy');
      }
    });
  }
  } // end initLogin

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLogin);
  } else {
    initLogin();
  }
  window.addEventListener('pageshow', initLogin);
})();
