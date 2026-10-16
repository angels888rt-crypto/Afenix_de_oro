document.addEventListener('DOMContentLoaded', async ()=>{
  if(!Afenix.guardPage('ADMIN')) return;
  const $=s=>document.querySelector(s), {api, toast, esc}=Afenix;
  const dishChecks=$('#dishChecks'), editDishChecks=$('#editDishChecks');
  const optionInputs=$('#optionInputs'), addOptionBtn=$('#addOptionBtn');
  const createMsg=$('#createMsg'), editMsg=$('#editMsg');
  const subsList=$('#subsList'), countLabel=$('#countLabel');
  const editModal=$('#editModal');
  let dishes=[], subcategories=[];

  const setCreateMsg=(t,ok=false)=>{ createMsg.hidden=!t; createMsg.textContent=t||''; createMsg.className='form-message'+(ok?' ok':''); };
  const setEditMsg=(t,ok=false)=>{ editMsg.hidden=!t; editMsg.textContent=t||''; editMsg.className='form-message'+(ok?' ok':''); };

  async function loadDishes(){
    try{
      dishes = await api('/api/v1/dishes?limit=100')||[];
    }catch{ dishes=[]; }
    const renderChecks=(container, selected=[])=>{
      if(!container) return;
      if(!dishes.length){ container.innerHTML='<p class="muted">No hay platos</p>'; return; }
      container.innerHTML = dishes.map(d=>{
        const checked = selected.includes(d.id) ? 'checked' : '';
        return `<label><input type="checkbox" value="${d.id}" ${checked}> <span>${esc(d.name)}</span> <small class="muted">(${esc(d.category||'')})</small></label>`;
      }).join('');
    };
    renderChecks(dishChecks);
    // keep edit checks if modal open
    if(!editModal.hidden){
      const sel = Array.from(editDishChecks.querySelectorAll('input:checked')).map(i=>Number(i.value));
      // re-render will be done in openEdit
    }
  }

  function getSelectedDishIds(container){
    return Array.from(container.querySelectorAll('input[type=checkbox]:checked')).map(i=>Number(i.value));
  }

  function addOptionInput(value=''){
    const row=document.createElement('div');
    row.className='option-row';
    row.innerHTML=`<input placeholder="Ej. Amarillo" maxlength="80" value="${esc(value)}"><button type="button" class="btn btn--ghost btn--small">×</button>`;
    row.querySelector('button').addEventListener('click',()=>row.remove());
    optionInputs.appendChild(row);
  }
  addOptionBtn.addEventListener('click',()=>addOptionInput(''));

  async function loadSubs(){
    try{
      const data = await api('/api/v1/subcategories?limit=100')||[];
      subcategories = Array.isArray(data)?data:[];
      renderSubs();
    }catch(e){ toast(e.message,'error'); subsList.innerHTML=`<p class="muted">Error: ${esc(e.message)}</p>`; }
  }

  function renderSubs(){
    countLabel.textContent = `${subcategories.length} subcategoría${subcategories.length===1?'':'s'}`;
    if(!subcategories.length){ subsList.innerHTML='<p class="muted">No hay subcategorías aún.</p>'; return; }
    subsList.innerHTML = subcategories.map(sub=>{
      const dishesHtml = (sub.dishes && sub.dishes.length ? sub.dishes : []).map(d=>`<span class="dish-badge">${esc(d.name||('Plato #'+d.id))}</span>`).join('') || '<span class="muted" style="font-size:.78rem">Sin platos</span>';
      // fallback if dishes empty but dish_ids present: try to resolve via dishes array
      let fallbackDishesHtml = dishesHtml;
      if((!sub.dishes || !sub.dishes.length) && sub.dish_ids && sub.dish_ids.length){
        fallbackDishesHtml = sub.dish_ids.map(id=>{
          const found = dishes.find(x=>x.id===id);
          return `<span class="dish-badge">${esc(found?found.name:'Plato #'+id)}</span>`;
        }).join('');
      } else if(fallbackDishesHtml.includes('Sin platos') && sub.dish_ids && sub.dish_ids.length){
        fallbackDishesHtml = sub.dish_ids.map(id=>{
          const found = dishes.find(x=>x.id===id);
          return `<span class="dish-badge">${esc(found?found.name:'Plato #'+id)}</span>`;
        }).join('');
      }
      const opts = sub.options||[];
      const optsHtml = opts.map(o=>`<span class="opt-item">${esc(o.name)} <button data-edit-opt="${o.id}" data-sub="${sub.id}" title="Editar">✎</button><button data-del-opt="${o.id}" data-sub="${sub.id}" title="Eliminar">×</button></span>`).join('') || '<span class="muted" style="font-size:.78rem">Sin opciones</span>';
      return `<div class="sub-card" data-id="${sub.id}">
        <div class="sub-card__head"><div><h3 class="sub-card__title">${esc(sub.name)}</h3>${sub.description?`<p class="sub-card__desc">${esc(sub.description)}</p>`:''}</div><div style="display:flex;gap:6px;flex-shrink:0"><button class="btn btn--ghost btn--small" data-edit="${sub.id}">Editar</button><button class="btn btn--danger btn--small" data-delete="${sub.id}">Eliminar</button></div></div>
        <div style="margin-top:10px"><strong style="font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)">Platos (${(sub.dish_ids||[]).length})</strong><div class="sub-card__meta">${fallbackDishesHtml}</div></div>
        <div style="margin-top:10px"><strong style="font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)">Opciones (${opts.length})</strong><div class="opt-list">${optsHtml}</div></div>
        <div style="margin-top:10px;display:flex;gap:6px;align-items:center"><input placeholder="Nueva opción" maxlength="80" data-new-opt="${sub.id}" style="flex:1;padding:8px 10px;border-radius:10px;border:1px solid var(--line)"><button class="btn btn--primary btn--small" data-add-opt="${sub.id}">Agregar</button></div>
      </div>`;
    }).join('');

    // bind edit/delete subcategory
    subsList.querySelectorAll('[data-edit]').forEach(btn=> btn.addEventListener('click', ()=> openEdit(Number(btn.dataset.edit))));
    subsList.querySelectorAll('[data-delete]').forEach(btn=> btn.addEventListener('click', async ()=>{
      const id=Number(btn.dataset.delete);
      const sub=subcategories.find(s=>s.id===id);
      if(!sub) return;
      if(!confirm(`¿Eliminar subcategoría "${sub.name}"?`)) return;
      try{ await api(`/api/v1/subcategories/${id}`,{method:'DELETE'}); toast('Subcategoría eliminada'); await loadSubs(); }catch(e){ toast(e.message,'error'); }
    }));
    // add option
    subsList.querySelectorAll('[data-add-opt]').forEach(btn=>{
      btn.addEventListener('click', async ()=>{
        const subId=Number(btn.dataset.addOpt);
        const input = subsList.querySelector(`input[data-new-opt="${subId}"]`);
        const name = input.value.trim();
        if(!name){ toast('Escribe el nombre de la opción','error'); return; }
        try{ await api(`/api/v1/subcategories/${subId}/options`,{method:'POST', body:JSON.stringify({name})}); toast('Opción agregada'); input.value=''; await loadSubs(); }catch(e){ toast(e.message,'error'); }
      });
    });
    subsList.querySelectorAll('[data-del-opt]').forEach(btn=>{
      btn.addEventListener('click', async ()=>{
        const subId=Number(btn.dataset.sub), optId=Number(btn.dataset.delOpt);
        if(!confirm('¿Eliminar opción?')) return;
        try{ await api(`/api/v1/subcategories/${subId}/options/${optId}`,{method:'DELETE'}); toast('Opción eliminada'); await loadSubs(); }catch(e){ toast(e.message,'error'); }
      });
    });
    subsList.querySelectorAll('[data-edit-opt]').forEach(btn=>{
      btn.addEventListener('click', async ()=>{
        const subId=Number(btn.dataset.sub), optId=Number(btn.dataset.editOpt);
        const sub=subcategories.find(s=>s.id===subId);
        const opt=(sub?.options||[]).find(o=>o.id===optId);
        const nueva = prompt('Editar opción:', opt?opt.name:'');
        if(nueva===null) return;
        const name=nueva.trim();
        if(!name){ toast('Nombre no puede estar vacío','error'); return; }
        try{ await api(`/api/v1/subcategories/${subId}/options/${optId}`,{method:'PUT', body:JSON.stringify({name})}); toast('Opción actualizada'); await loadSubs(); }catch(e){ toast(e.message,'error'); }
      });
    });
  }

  // create
  $('#createForm').addEventListener('submit', async e=>{
    e.preventDefault(); setCreateMsg('');
    const name=$('#subName').value.trim();
    const description=$('#subDesc').value.trim()||null;
    const dish_ids=getSelectedDishIds(dishChecks);
    const options = Array.from(optionInputs.querySelectorAll('input')).map(i=>i.value.trim()).filter(Boolean);
    if(name.length<2){ setCreateMsg('Nombre debe tener al menos 2 caracteres'); return; }
    if(!dish_ids.length){ setCreateMsg('Seleccione al menos un plato'); return; }
    try{
      await api('/api/v1/subcategories',{method:'POST', body:JSON.stringify({name, description, dish_ids, options})});
      setCreateMsg('Subcategoría creada correctamente',true); toast('Subcategoría creada');
      $('#subName').value=''; $('#subDesc').value='';
      dishChecks.querySelectorAll('input').forEach(i=>i.checked=false);
      optionInputs.innerHTML='<div class="option-row"><input placeholder="Ej. Amarillo" maxlength="80"><button type="button" class="btn btn--ghost btn--small">×</button></div>';
      optionInputs.querySelector('button').addEventListener('click',()=>optionInputs.querySelector('.option-row').remove());
      await loadSubs();
    }catch(err){ setCreateMsg(err.message); toast(err.message,'error'); }
  });

  $('#refreshBtn').addEventListener('click', async ()=>{ await loadDishes(); await loadSubs(); });

  // edit modal
  function openEdit(id){
    const sub=subcategories.find(s=>s.id===id); if(!sub) return;
    $('#editId').value=sub.id;
    $('#editName').value=sub.name;
    $('#editDesc').value=sub.description||'';
    setEditMsg('');
    // render dish checks with selected
    if(dishes.length){
      editDishChecks.innerHTML = dishes.map(d=>{
        const checked = (sub.dish_ids||[]).includes(d.id) ? 'checked' : '';
        return `<label><input type="checkbox" value="${d.id}" ${checked}> <span>${esc(d.name)}</span> <small class="muted">(${esc(d.category||'')})</small></label>`;
      }).join('');
    } else {
      editDishChecks.innerHTML = '<p class="muted">No hay platos</p>';
    }
    editModal.hidden=false; document.body.classList.add('modal-open');
  }
  function closeEdit(){ editModal.hidden=true; document.body.classList.remove('modal-open'); }
  $('#closeModal').addEventListener('click', closeEdit);
  $('#cancelEdit').addEventListener('click', closeEdit);
  editModal.addEventListener('click', e=>{ if(e.target===editModal) closeEdit(); });
  document.addEventListener('keydown', e=>{ if(e.key==='Escape' && !editModal.hidden) closeEdit(); });

  $('#editForm').addEventListener('submit', async e=>{
    e.preventDefault(); setEditMsg('');
    const id=Number($('#editId').value);
    const name=$('#editName').value.trim();
    const description=$('#editDesc').value.trim()||null;
    const dish_ids=getSelectedDishIds(editDishChecks);
    if(name.length<2){ setEditMsg('Nombre debe tener al menos 2 caracteres'); return; }
    // dish_ids can be empty? allow but warn
    try{
      await api(`/api/v1/subcategories/${id}`,{method:'PUT', body:JSON.stringify({name, description, dish_ids})});
      setEditMsg('Guardado',true); toast('Subcategoría actualizada');
      setTimeout(async()=>{ closeEdit(); await loadSubs(); },400);
    }catch(err){ setEditMsg(err.message); toast(err.message,'error'); }
  });

  await loadDishes();
  await loadSubs();
});
