document.addEventListener('DOMContentLoaded',async()=>{
  if(!Afenix.guardPage('ADMIN'))return;
  const $=s=>document.querySelector(s),{api,toast,money,esc}=Afenix;
  const box=$('#inventory'), count=$('#count'), modal=$('#editModal'), editMsg=$('#editMsg'); let dishes=[];
  const setMsg=(t,ok=false)=>{editMsg.hidden=!t;editMsg.textContent=t;editMsg.className=`form-message${ok?' ok':''}`};
  function render(){
    count.textContent=`${dishes.length} plato${dishes.length===1?'':'s'}`;
    box.innerHTML=dishes.map(d=>{
      const disponible = !!d.is_available;
      const badgeClass = disponible ? '' : 'empty';
      const badgeText = disponible ? '🟢 Disponible' : '🔴 Agotado';
      const img=d.image_url||d.image_path||'';
      const imgHtml=img?`<img src="${esc(img)}" alt="${esc(d.name)}" style="width:100%; height:140px; object-fit:cover; border-radius:12px; border:1px solid var(--line);">`:`<div style="width:100%; height:140px; display:flex; align-items:center; justify-content:center; background:#f6f1e7; border:1px solid var(--line); border-radius:12px; color:var(--muted); font-size:.9rem;">Sin imagen</div>`;
      const toggleLabel = disponible ? 'Marcar Agotado' : 'Marcar Disponible';
      const toggleClass = disponible ? 'btn--ghost' : 'btn--primary';
      return `<article class="inventory-card"><div class="inventory-card__media" style="margin-bottom:12px;">${imgHtml}</div><div class="inventory-card__head"><div><h3>${esc(d.name)}</h3><p class="muted">${esc(d.category||'Sin categoría')} · ${money(d.price)}</p></div><span class="stock-badge ${badgeClass}">${badgeText}</span></div><div class="inventory-card__meta"><strong>${disponible ? 'Disponible' : 'Agotado'}</strong><span class="muted">${Math.round((Number(d.estimated_time)||0)/60)} min</span></div><div class="inventory-card__actions"><button class="btn ${toggleClass} btn--small" data-toggle="${d.id}" data-available="${disponible}">${toggleLabel}</button><button class="btn btn--ghost btn--small" data-edit="${d.id}">Editar</button><button class="btn btn--danger btn--small" data-delete="${d.id}">Eliminar</button></div></article>`;
    }).join('')||'<p class="muted">No hay platos registrados.</p>';
  }
  async function load(){try{dishes=await api('/api/v1/dishes?limit=100')||[];render()}catch(e){toast(e.message,'error')}}
  let editPendingFile=null;
  const editImageInput=$('#editImage'), editPreview=$('#editImagePreview'), editPreviewWrap=$('#editImagePreviewWrap'), editCurrentInfo=$('#editCurrentImageInfo'), removeEditBtn=$('#removeEditImageBtn');
  if(editImageInput){
    editImageInput.addEventListener('change',()=>{
      const f=editImageInput.files&&editImageInput.files[0];
      if(!f){ editPendingFile=null; if(editPreviewWrap) editPreviewWrap.style.display='none'; return; }
      if(!f.type.startsWith('image/')){ toast('Seleccione una imagen válida','error'); editImageInput.value=''; return; }
      if(f.size>3*1024*1024){ toast('Imagen demasiado grande. Máx 3MB.','error'); editImageInput.value=''; return; }
      editPendingFile=f;
      const url=URL.createObjectURL(f);
      if(editPreview){ editPreview.src=url; }
      if(editPreviewWrap) editPreviewWrap.style.display='block';
      if(removeEditBtn) removeEditBtn.style.display='inline-flex';
      if(editCurrentInfo) editCurrentInfo.textContent=`Nueva imagen seleccionada: ${f.name}`;
    });
  }
  if(removeEditBtn){
    removeEditBtn.addEventListener('click',()=>{
      editPendingFile=null;
      if(editImageInput) editImageInput.value='';
      if(editPreviewWrap) editPreviewWrap.style.display='none';
      if(editCurrentInfo){
        const d=dishes.find(x=>String(x.id)===String($('#editId').value));
        const cur=d?.image_url||d?.image_path||'';
        editCurrentInfo.textContent=cur?`Imagen actual: ${cur.split('/').pop()}`:'Sin imagen actual';
      }
    });
  }
  function openEdit(id){const d=dishes.find(x=>String(x.id)===String(id));if(!d)return;$('#editId').value=d.id;$('#editName').value=d.name||'';$('#editCategory').value=d.category||'';$('#editPrice').value=Math.round((Number(d.price)||0)/100);$('#editEstimated').value=Math.round((Number(d.estimated_time)||0)/60);$('#editAvailable').value=String(!!d.is_available);$('#editDescription').value=d.description||'';$('#editNotes').value=d.preparation_notes||'';setMsg('');editPendingFile=null; if(editImageInput) editImageInput.value=''; if(editPreviewWrap) editPreviewWrap.style.display='none'; if(editCurrentInfo){ const cur=d.image_url||d.image_path||''; editCurrentInfo.textContent=cur?`Imagen actual: ${cur.split('/').pop()}`:'Sin imagen actual'; editCurrentInfo.style.display='block'; if(cur && editPreview){ editPreview.src=cur; editPreviewWrap.style.display='block'; removeEditBtn.style.display='none'; } } modal.hidden=false;document.body.classList.add('modal-open');setTimeout(()=>$('#editName').focus(),30)}
  function closeEdit(){modal.hidden=true;document.body.classList.remove('modal-open'); editPendingFile=null; if(editImageInput) editImageInput.value=''; if(editPreviewWrap) editPreviewWrap.style.display='none';}
  box.addEventListener('click',async e=>{
    const edit=e.target.closest('[data-edit]'); if(edit){openEdit(edit.dataset.edit);return}
    const del=e.target.closest('[data-delete]'); if(del){const d=dishes.find(x=>String(x.id)===String(del.dataset.delete));if(!d)return;if(!confirm(`¿Eliminar el plato "${d.name}" del catálogo?\nSus pedidos históricos se conservarán.`))return;try{await api(`/api/v1/dishes/${d.id}`,{method:'DELETE'});toast('Plato eliminado del catálogo');await load()}catch(err){toast(err.message,'error')}return}
    const tog=e.target.closest('[data-toggle]'); if(tog){
      const id=tog.dataset.toggle;
      const current = tog.dataset.available === 'true';
      const next = !current;
      try{
        await api(`/api/v1/dishes/${id}`,{method:'PUT',body:JSON.stringify({is_available: next})});
        toast(next ? 'Plato marcado como Disponible' : 'Plato marcado como Agotado');
        await load();
      }catch(err){toast(err.message,'error')}
      return;
    }
  });
  $('#editForm').addEventListener('submit',async e=>{e.preventDefault();setMsg('');const id=$('#editId').value,price=Math.round(Number($('#editPrice').value)*100),minutes=Math.round(Number($('#editEstimated').value)*60);try{await api(`/api/v1/dishes/${id}`,{method:'PUT',body:JSON.stringify({name:$('#editName').value.trim(),category:$('#editCategory').value.trim(),price,estimated_time:minutes,is_available:$('#editAvailable').value==='true',description:$('#editDescription').value.trim()||null,preparation_notes:$('#editNotes').value.trim()||null})}); if(editPendingFile){ const fd=new FormData(); fd.append('file', editPendingFile); const token=localStorage.getItem('afenix_access_token'); const res=await fetch(`/api/v1/dishes/${id}/image`,{method:'POST',headers: token?{Authorization:`Bearer ${token}`}:{}, body:fd}); let payload=null; try{payload=await res.json()}catch{} if(!res.ok || payload?.success===false) throw new Error(payload?.message || 'Plato actualizado pero falló la imagen'); } setMsg('Cambios guardados correctamente.',true);toast('Plato actualizado');setTimeout(async()=>{closeEdit();await load()},350)}catch(err){setMsg(err.message);toast(err.message,'error')}});
  $('#closeModal').addEventListener('click',closeEdit);$('#cancelEdit').addEventListener('click',closeEdit);modal.addEventListener('click',e=>{if(e.target===modal)closeEdit()});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!modal.hidden)closeEdit()});$('#refresh').addEventListener('click',load);await load();
});
