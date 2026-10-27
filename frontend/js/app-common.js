(function(){
  'use strict';
  const getRole=()=> (localStorage.getItem('afenix_role')||'').toUpperCase();
  const getToken=()=> localStorage.getItem('afenix_access_token');
  const getDisplay=()=> localStorage.getItem('afenix_display_name')||'Usuario';
  const allowed=['ADMIN','CAMARERO','CAJERO','MONITOR'];
  const roleNames={ADMIN:'Administrador',CAMARERO:'Mesero',CAJERO:'Cajero',MONITOR:'Monitor'};
  const routes={ADMIN:'/admin.html',CAMARERO:'/mesero.html',CAJERO:'/cajero.html',MONITOR:'/monitor-ordenes.html'};
  const apiBaseUrl=['localhost','127.0.0.1'].includes(window.location.hostname)
    ? 'http://localhost:8000'
    : 'https://pollo-api.hostless.app';
  // Solo exige token existente; la verificación de rol la hace guardPage por página.
  // Esto permite que cualquier usuario autenticado (incluido Auxiliares con roles futuros) pueda iniciar sesión y recargar sin ser expulsado.
  const _initRole=getRole();
  const _initToken=getToken();
  if(!_initToken){window.location.href='/secion.html';return;}
  // Si el rol no está en la lista conocida pero el token existe, no redirigimos aquí; guardPage decidirá.
  // Mantenemos compatibilidad: si el rol es conocido y no coincide con la página, guardPage redirigirá.
  const $=(s,c=document)=>c.querySelector(s);
  const esc=v=>String(v??'').replace(/[&<>'"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[ch]));
  const money=v=>`$${Math.max(0,Math.round((Number(v)||0)/100)).toLocaleString('es-CO')}`;
  const date=d=>d?new Date(d.endsWith('Z')?d:d+'Z').toLocaleString('es-CO'):'—';
  const headers=()=>{const t=getToken();return {'Content-Type':'application/json', ...(t?{Authorization:`Bearer ${t}`}:{})};};
  async function api(url,opt={}){const requestUrl=/^https?:\/\//i.test(url)?url:new URL(url,apiBaseUrl).toString();const r=await fetch(requestUrl,{...opt,headers:{...headers(),...(opt.headers||{})}});let p=null;try{p=await r.json()}catch{}if(r.status===401){logout();throw Error('Sesión expirada.')}if(!r.ok||p?.success===false)throw Error(p?.message||p?.detail||'No se pudo completar la operación.');return p?.data}
  function logout(){['afenix_access_token','afenix_refresh_token','afenix_display_name','afenix_role'].forEach(k=>localStorage.removeItem(k));window.location.href='/secion.html'}
  function toast(msg,type='ok'){const e=$('#toast');if(!e)return;e.textContent=msg;e.className='toast is-visible';if(type==='error')e.style.background='#7a0c12';setTimeout(()=>e.classList.remove('is-visible'),2600)}
  function guardPage(pageRole){const r=getRole();if(r!==pageRole){window.location.href=routes[r]||'/secion.html';return false}return true}
  function bindShell(){const r=getRole();const d=getDisplay();const rl=$('#roleLabel'),uc=$('#userChip'),yr=$('#year');if(rl)rl.textContent=`Panel · ${roleNames[r]||r}`;if(uc)uc.textContent=d;if(yr)yr.textContent=new Date().getFullYear();const b=$('#logoutBtn');if(b)b.addEventListener('click',logout);document.querySelectorAll('[data-home]').forEach(a=>a.setAttribute('href',routes[r]||'/secion.html'))}
  window.Afenix={get role(){return getRole();},get roleName(){return roleNames[getRole()]||getRole();},get display(){return getDisplay();},get token(){return getToken();},api,toast,logout,guardPage,bindShell,esc,money,date,routes};
  document.addEventListener('DOMContentLoaded',bindShell);
})();
