document.addEventListener('DOMContentLoaded', async ()=>{
  if(!Afenix.guardPage('ADMIN')) return;
  const $=s=>document.querySelector(s), {api,toast,esc}=Afenix;
  let categories=[];
  let editing=null;
  let toDelete=null;

  function setMsg(t,ok=false){ const e=$('#msg'); if(!e)return; e.hidden=!t; e.textContent=t; e.className=`form-message${ok?' ok':''}`; }
  function reset(){ editing=null; $('#categoryForm').reset(); $('#categoryId').value=''; $('#formTitle').textContent='Crear categoria'; $('#save').textContent='Crear categoria'; $('#cancel').hidden=true; $('#editor').classList.remove('editing'); $('#editNote').hidden=true; setMsg(''); }
  function startEdit(cat){ editing=cat; $('#categoryId').value=cat.id; $('#name').value=cat.name; $('#description').value=cat.description||''; $('#formTitle').textContent='Editar categoria'; $('#save').textContent='Guardar cambios'; $('#cancel').hidden=false; $('#editor').classList.add('editing'); $('#editNote').hidden=false; $('#name').focus(); window.scrollTo({top:0,behavior:'smooth'}); }

  async function load(){
    try{
      categories = await api('/api/v1/categories?limit=100') || [];
      $('#count').textContent = `${categories.length} categoria${categories.length===1?'':'s'}`;
      $('#categories').innerHTML = categories.map(c=>`
        <tr>
          <td><span class="cat-badge">${esc(c.name)}</span></td>
          <td class="muted">${esc(c.description||'—')}</td>
          <td class="muted">${c.created_at ? new Date(c.created_at).toLocaleDateString('es-CO') : '—'}</td>
          <td style="text-align:right;">
            <div class="row-actions">
              <button class="btn btn--primary btn--small" data-edit="${c.id}">Editar</button>
              <button class="btn btn--danger btn--small" data-delete="${c.id}">Eliminar</button>
            </div>
          </td>
        </tr>
      `).join('') || `<tr><td colspan="4" class="muted" style="text-align:center; padding:24px;">No hay categorias. Crea la primera.</td></tr>`;
    }catch(e){ toast(e.message,'error'); }
  }

  $('#categories').addEventListener('click', e=>{
    const btnEdit=e.target.closest('[data-edit]');
    if(btnEdit){ const cat=categories.find(x=>String(x.id)===btnEdit.dataset.edit); if(cat) startEdit(cat); return; }
    const btnDel=e.target.closest('[data-delete]');
    if(btnDel){ const cat=categories.find(x=>String(x.id)===btnDel.dataset.delete); if(!cat) return; toDelete=cat; $('#deleteMessage').textContent=`¿Eliminar la categoria "${cat.name}"?`; $('#deleteModal').hidden=false; document.body.classList.add('modal-open'); }
  });
  $('#cancel').addEventListener('click', reset);
  $('#refresh').addEventListener('click', ()=>{ setMsg(''); load(); });
  $('#closeDeleteModal').addEventListener('click', ()=>{ toDelete=null; $('#deleteModal').hidden=true; document.body.classList.remove('modal-open'); });
  $('#cancelDelete').addEventListener('click', ()=>{ toDelete=null; $('#deleteModal').hidden=true; document.body.classList.remove('modal-open'); });
  $('#deleteModal').addEventListener('click', e=>{ if(e.target.id==='deleteModal'){ toDelete=null; $('#deleteModal').hidden=true; document.body.classList.remove('modal-open'); } });
  $('#confirmDelete').addEventListener('click', async ()=>{
    if(!toDelete) return;
    try{ await api(`/api/v1/categories/${toDelete.id}`,{method:'DELETE'}); toast('Categoria eliminada'); setMsg(`Categoria "${toDelete.name}" eliminada.`, true); toDelete=null; $('#deleteModal').hidden=true; document.body.classList.remove('modal-open'); await load(); }
    catch(err){ toast(err.message,'error'); setMsg(err.message); $('#deleteModal').hidden=true; document.body.classList.remove('modal-open'); }
  });

  $('#categoryForm').addEventListener('submit', async e=>{
    e.preventDefault(); setMsg('');
    const name=$('#name').value.trim();
    const description=$('#description').value.trim()||null;
    if(name.length<2){ setMsg('El nombre debe tener al menos 2 caracteres.'); return; }
    try{
      if(editing){
        await api(`/api/v1/categories/${editing.id}`,{method:'PUT', body:JSON.stringify({name, description})});
        setMsg('Categoria actualizada.', true); toast('Categoria actualizada');
      } else {
        await api('/api/v1/categories',{method:'POST', body:JSON.stringify({name, description})});
        setMsg('Categoria creada.', true); toast('Categoria creada');
      }
      reset(); await load();
    }catch(err){ setMsg(err.message); toast(err.message,'error'); }
  });

  document.addEventListener('keydown', e=>{ if(e.key==='Escape' && !$('#deleteModal').hidden){ toDelete=null; $('#deleteModal').hidden=true; document.body.classList.remove('modal-open'); }});
  await load();
});
