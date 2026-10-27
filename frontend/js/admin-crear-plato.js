document.addEventListener('DOMContentLoaded',()=>{
  if(!Afenix.guardPage('ADMIN'))return;
  const $=s=>document.querySelector(s),{api,toast}=Afenix;
  const disponibilidad=$('#disponibilidad'), preview=$('#availabilityPreview'), msg=$('#dishMsg');
  const imageInput=$('#image'), imagePreview=$('#imagePreview'), imageWrap=$('#imagePreviewWrap'), removeBtn=$('#removeImageBtn');
  let pendingFile=null;
  const updatePreview=()=>{
    const val = disponibilidad ? disponibilidad.value : 'true';
    if(val==='true'){ preview.textContent='🟢 Disponible — visible para meseros'; }
    else { preview.textContent='🔴 Agotado — no se podrá pedir'; }
  };
  const setMsg=(text,ok=false)=>{msg.hidden=!text;msg.textContent=text;msg.className=`form-message${ok?' ok':''}`};
  if(disponibilidad){ disponibilidad.addEventListener('change',updatePreview); updatePreview(); }
  if(imageInput){
    imageInput.addEventListener('change',()=>{
      const file=imageInput.files&&imageInput.files[0];
      if(!file){ pendingFile=null; if(imageWrap) imageWrap.style.display='none'; if(imagePreview) imagePreview.src=''; return; }
      if(!file.type.startsWith('image/')){ setMsg('Seleccione una imagen válida.'); imageInput.value=''; return; }
      if(file.size>3*1024*1024){ setMsg('Imagen demasiado grande. Máximo 3MB.'); imageInput.value=''; return; }
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
    if(!Number.isFinite(pricePesos)||pricePesos<=0){setMsg('Ingresa un precio válido.');return}
    if(!Number.isFinite(minutes)||minutes<=0){setMsg('Ingresa un tiempo válido.');return}
    try{
      const created=await api('/api/v1/dishes',{method:'POST',body:JSON.stringify({
        name:$('#name').value.trim(),category:$('#category').value.trim(),price:Math.round(pricePesos*100),estimated_time:Math.round(minutes*60),is_available:isAvailable,
        description:$('#description').value.trim()||null
      })});
      // Si hay imagen, subirla inmediatamente
      if(pendingFile && created && created.id){
        const fd=new FormData();
        fd.append('file', pendingFile);
        const token=localStorage.getItem('afenix_access_token');
        const res=await fetch(`/api/v1/dishes/${created.id}/image`,{method:'POST',headers: token?{Authorization:`Bearer ${token}`}:{}, body:fd});
        let payload=null; try{payload=await res.json()}catch{}
        if(!res.ok || payload?.success===false) throw new Error(payload?.message || 'Plato creado pero falló la imagen');
      }
      setMsg('Plato creado correctamente.',true); toast('Plato creado');
      $('#dishForm').reset(); if(disponibilidad) disponibilidad.value='true'; updatePreview();
      pendingFile=null; if(imageWrap) imageWrap.style.display='none'; if(imagePreview) imagePreview.src=''; if(imageInput) imageInput.value='';
    }catch(err){setMsg(err.message);toast(err.message,'error')}
  });
});
