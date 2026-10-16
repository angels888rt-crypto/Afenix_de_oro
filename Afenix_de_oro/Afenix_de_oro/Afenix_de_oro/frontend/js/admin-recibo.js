document.addEventListener('DOMContentLoaded', async () => {
  if (!Afenix.guardPage('ADMIN')) return;
  const $ = s => document.querySelector(s);
  const { api, toast } = Afenix;

  const logoInput = $('#logoInput');
  const logoPreview = $('#logoPreview');
  const logoEmpty = $('#logoEmpty');
  const removeBtn = $('#removeLogoBtn');
  const nameInput = $('#nameInput');
  const formMsg = $('#formMsg');
  const saveStatus = $('#saveStatus');
  const previewLogo = $('#previewLogo');
  const previewLogoWrap = $('#previewLogoWrap');
  const previewName = $('#previewName');

  let currentConfig = null;
  let pendingLogoFile = null;
  let previewLogoUrl = null;

  function setMsg(text, ok=false){
    if (!formMsg) return;
    formMsg.hidden = !text;
    formMsg.textContent = text || '';
    formMsg.className = `form-message${ok?' ok':''}`;
  }
  function showSaveStatus(){
    if (!saveStatus) return;
    saveStatus.hidden = false;
    saveStatus.textContent = 'Guardado';
    setTimeout(()=> saveStatus.hidden=true, 2000);
  }

  function updatePreview(){
    const name = (nameInput?.value || '').trim() || 'RESTAURANTE';
    if (previewName) previewName.textContent = name.toUpperCase();

    let logoUrl = null;
    if (previewLogoUrl) {
      logoUrl = previewLogoUrl;
    } else if (currentConfig?.logo_url) {
      logoUrl = currentConfig.logo_url;
    }

    const showLogo = !!logoUrl;
    if (logoPreview) {
      if (showLogo) {
        logoPreview.src = logoUrl;
        logoPreview.style.display = 'block';
      } else {
        logoPreview.style.display = 'none';
        logoPreview.removeAttribute('src');
      }
    }
    if (logoEmpty) logoEmpty.style.display = showLogo ? 'none' : 'flex';
    if (removeBtn) removeBtn.style.display = showLogo ? 'inline-flex' : 'none';

    if (previewLogoWrap) previewLogoWrap.style.display = showLogo ? 'block' : 'none';
    if (previewLogo && showLogo) previewLogo.src = logoUrl;
  }

  async function loadConfig(){
    try {
      const cfg = await api('/api/v1/receipt-config');
      currentConfig = cfg;
      if (nameInput) nameInput.value = cfg.restaurant_name || '';
      pendingLogoFile = null;
      if (previewLogoUrl) {
        URL.revokeObjectURL(previewLogoUrl);
        previewLogoUrl = null;
      }
      updatePreview();
      if (cfg.logo_url && logoPreview) {
        logoPreview.src = cfg.logo_url;
        logoPreview.style.display = 'block';
        if (logoEmpty) logoEmpty.style.display = 'none';
        if (removeBtn) removeBtn.style.display = 'inline-flex';
      }
    } catch (e) {
      setMsg(e.message, false);
      toast(e.message, 'error');
    }
  }

  if (nameInput) nameInput.addEventListener('input', updatePreview);

  if (logoInput) {
    logoInput.addEventListener('change', () => {
      const file = logoInput.files && logoInput.files[0];
      if (!file) {
        pendingLogoFile = null;
        if (previewLogoUrl) { URL.revokeObjectURL(previewLogoUrl); previewLogoUrl=null; }
        updatePreview();
        return;
      }
      if (!file.type.startsWith('image/')) {
        setMsg('Seleccione una imagen válida (PNG/JPG/WEBP).');
        logoInput.value = '';
        return;
      }
      if (file.size > 2*1024*1024) {
        setMsg('Imagen demasiado grande. Máximo 2MB.');
        logoInput.value = '';
        return;
      }
      pendingLogoFile = file;
      if (previewLogoUrl) URL.revokeObjectURL(previewLogoUrl);
      previewLogoUrl = URL.createObjectURL(file);
      updatePreview();
      setMsg('');
    });
  }

  if (removeBtn) {
    removeBtn.addEventListener('click', async () => {
      if (pendingLogoFile) {
        pendingLogoFile = null;
        if (previewLogoUrl) { URL.revokeObjectURL(previewLogoUrl); previewLogoUrl=null; }
        if (logoInput) logoInput.value = '';
        updatePreview();
        return;
      }
      if (!currentConfig?.logo_url) return;
      try {
        const res = await api('/api/v1/receipt-config/logo', { method: 'DELETE' });
        currentConfig = res;
        toast('Logo eliminado');
        if (previewLogoUrl) { URL.revokeObjectURL(previewLogoUrl); previewLogoUrl=null; }
        pendingLogoFile = null;
        if (logoInput) logoInput.value = '';
        updatePreview();
        setMsg('Logo eliminado. Recuerde Guardar si cambió el nombre.', true);
      } catch (e) {
        setMsg(e.message);
        toast(e.message, 'error');
      }
    });
  }

  async function saveConfig(){
    setMsg('');
    const restaurant_name = (nameInput?.value || '').trim();
    if (!restaurant_name) {
      setMsg('El nombre del restaurante es obligatorio.');
      return;
    }
    try {
      if (pendingLogoFile) {
        const fd = new FormData();
        fd.append('file', pendingLogoFile);
        const token = localStorage.getItem('afenix_access_token');
        const resp = await fetch('/api/v1/receipt-config/logo', {
          method: 'POST',
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: fd
        });
        let payload = null;
        try { payload = await resp.json(); } catch {}
        if (!resp.ok || payload?.success === false) throw new Error(payload?.message || 'Error al subir logo');
        currentConfig = payload.data;
        if (previewLogoUrl) { URL.revokeObjectURL(previewLogoUrl); previewLogoUrl=null; }
        pendingLogoFile = null;
        if (logoInput) logoInput.value = '';
        toast('Logo guardado');
      }

      const updated = await api('/api/v1/receipt-config', {
        method: 'PUT',
        body: JSON.stringify({ restaurant_name })
      });
      currentConfig = updated;
      updatePreview();
      setMsg('Configuración guardada correctamente.', true);
      showSaveStatus();
      toast('Configuración guardada');
    } catch (e) {
      setMsg(e.message);
      toast(e.message, 'error');
    }
  }

  const saveBtn = document.getElementById('saveBtn');
  const saveBtn2 = document.getElementById('saveBtn2');
  const resetBtn = document.getElementById('resetBtn');
  if (saveBtn) saveBtn.addEventListener('click', saveConfig);
  if (saveBtn2) saveBtn2.addEventListener('click', saveConfig);
  if (resetBtn) resetBtn.addEventListener('click', loadConfig);

  await loadConfig();
});
