document.addEventListener('DOMContentLoaded', async () => {
  if(!Afenix.guardPage('ADMIN')) return;
  const $=s=>document.querySelector(s),{api,toast,esc}=Afenix;
  const disponibilidad=$('#disponibilidad'), preview=$('#availabilityPreview'), msg=$('#dishMsg');
  const imageInput=$('#image'), imagePreview=$('#imagePreview'), imageWrap=$('#imagePreviewWrap'), removeBtn=$('#removeImageBtn');
  const categorySelect=$('#category'), categoryHint=$('#categoryHint');
  const formTitle=document.querySelector('.panel__head h2');
  const submitBtn=document.querySelector('#dishForm button[type="submit"]');
  let pendingFile=null;
  let editingId=null;
  let categories=[];

  const updatePreview=()=>{
    const val = disponibilidad ? disponibilidad.value : 'true';
    if(val==='true'){ preview.textContent='\uD83D\uDFE2 Disponible \u2014 visible para meseros'; }
    else { preview.textContent='\uD83D\uDD34 Agotado \u2014 no se podr\u00e1 pedir'; }
  };
  const setMsg=(text,ok=false)=>{msg.hidden=!text;msg.textContent=text;msg.className=`form-message${ok?' ok':''}`};
  if(disponibilidad){ disponibilidad.addEventListener('change',updatePreview); updatePreview(); }

  async function loadCategories(selectedId){
    try{
      categories = await api('/api/v1/categories?limit=100') || [];
    }catch(e){ categories=[]; }
    if(categorySelect){
      const currentVal = selectedId || categorySelect.value;
      categorySelect.innerHTML = '<option value="">\u25bc Seleccionar categor\u00eda</option>' + categories.map(c=>`<option value="${c.id}">${esc(c.name)}</option>`).join('');
      if(currentVal) categorySelect.value = String(currentVal);
      if(categoryHint){
        if(categories.length) categoryHint.innerHTML = `${categories.length} categor\u00eda(s) disponible(s) \u00b7 <a href="/admin-categorias.html" style="color:var(--gold); text-decoration:underline;">Gestionar categor\u00edas</a>`;
        else categoryHint.innerHTML = `No hay categor\u00edas. <a href="/admin-categorias.html" style="color:var(--gold); text-decoration:underline; font-weight:700;">Crear categor\u00eda primero</a>`;
      }
    }
  }

  // detect editing via ?id=
  const params = new URLSearchParams(window.location.search);
  editingId = params.get('id');
  await loadCategories();

  if(editingId){
    try{
      const dish = await api(`/api/v1/dishes/${editingId}`);
      if(dish){
        $('#name').value = dish.name || '';
        $('#price').value = Math.round((Number(dish.price)||0)/100);
        $('#estimated').value = Math.round((Number(dish.estimated_time)||0)/60);
        if(categorySelect && dish.category_id) categorySelect.value = String(dish.category_id);
        else if(categorySelect && dish.category){
          const found = categories.find(c=>c.name===dish.category);
          if(found) categorySelect.value = String(found.id);
        }
        if(disponibilidad) disponibilidad.value = dish.is_available ? 'true' : 'false';
        $('#description').value = dish.description || '';
        updatePreview();
        if(formTitle) formTitle.textContent = 'Editar plato';
        if(submitBtn) submitBtn.textContent = 'Guardar cambios';
        // show existing image if any
        if(dish.image_url && imagePreview && imageWrap){
          imagePreview.src = dish.image_url;
          imageWrap.style.display='block';
        }
      }
    }catch(e){ toast(e.message,'error'); }
  }

  if(imageInput){
    imageInput.addEventListener('change',()=>{
      const file=imageInput.files&&imageInput.files[0];
      if(!file){ pendingFile=null; if(imageWrap) imageWrap.style.display='none'; if(imagePreview) imagePreview.src=''; return; }
      if(!file.type.startsWith('image/')){ setMsg('Seleccione una imagen v\u00e1lida.'); imageInput.value=''; return; }
      if(file.size>3*1024*1024){ setMsg('Imagen demasiado grande. M\u00e1ximo 3MB.'); imageInput.value=''; return; }
      pendingFile=file;
      const url=URL.createObjectURL(file);
      if(imagePreview){ imagePreview.src=url; }
      if(imageWrap) imageWrap.style.display='block';
    });
  }
  if(removeBtn){
    removeBtn.addEventListener('click',()=>{
      pendingFile=null;
      if(imageInput) imageInput.value='';
      if(imageWrap) imageWrap.style.display='none';
      if(imagePreview) imagePreview.src='';
    });
  }

  $('#dishForm').addEventListener('submit',async e=>{
    e.preventDefault(); setMsg('');
    const pricePesos=Number($('#price').value), minutes=Number($('#estimated').value);
    const isAvailable = disponibilidad ? disponibilidad.value==='true' : true;
    const catId = categorySelect ? Number(categorySelect.value) : 0;
    if(!Number.isFinite(pricePesos)||pricePesos<=0){setMsg('Ingresa un precio v\u00e1lido.');return}
    if(!Number.isFinite(minutes)||minutes<=0){setMsg('Ingresa un tiempo v\u00e1lido.');return}
    if(!catId){ setMsg('Selecciona una categor\u00eda.'); return; }
    const payload = {
      name:$('#name').value.trim(),
      category_id:catId,
      price:Math.round(pricePesos*100),
      estimated_time:Math.round(minutes*60),
      is_available:isAvailable,
      description:$('#description').value.trim()||null
    };
    try{
      let result;
      if(editingId){
        result = await api(`/api/v1/dishes/${editingId}`,{method:'PUT',body:JSON.stringify(payload)});
        if(pendingFile && result && result.id){
          const fd=new FormData(); fd.append('file', pendingFile);
          const token=localStorage.getItem('afenix_access_token');
          const res=await fetch(`/api/v1/dishes/${result.id}/image`,{method:'POST',headers: token?{Authorization:`Bearer ${token}`}:{}, body:fd});
          let p=null; try{p=await res.json()}catch{}
          if(!res.ok || p?.success===false) throw new Error(p?.message || 'Plato actualizado pero fall\u00f3 la imagen');
        }
        setMsg('Plato actualizado correctamente.',true); toast('Plato actualizado');
        setTimeout(()=> window.location.href='/admin-inventario.html', 800);
      } else {
        const created=await api('/api/v1/dishes',{method:'POST',body:JSON.stringify(payload)});
        if(pendingFile && created && created.id){
          const fd=new FormData(); fd.append('file', pendingFile);
          const token=localStorage.getItem('afenix_access_token');
          const res=await fetch(`/api/v1/dishes/${created.id}/image`,{method:'POST',headers: token?{Authorization:`Bearer ${token}`}:{}, body:fd});
          let p=null; try{p=await res.json()}catch{}
          if(!res.ok || p?.success===false) throw new Error(p?.message || 'Plato creado pero fall\u00f3 la imagen');
        }
        setMsg('Plato creado correctamente.',true); toast('Plato creado');
        $('#dishForm').reset(); if(disponibilidad) disponibilidad.value='true'; updatePreview();
        if(categorySelect) categorySelect.value='';
        pendingFile=null; if(imageWrap) imageWrap.style.display='none'; if(imagePreview) imagePreview.src=''; if(imageInput) imageInput.value='';
      }
    }catch(err){setMsg(err.message);toast(err.message,'error')}
  });
  // refresh categories when tab visible
  document.addEventListener('visibilitychange',()=>{ if(document.visibilityState==='visible') loadCategories(categorySelect?categorySelect.value:null); });
});
