(function(){
  'use strict';
  const path = window.location.pathname;
  const publicPages = ['/secion.html','/','/index.html','/panel.html'];
  if (publicPages.includes(path)) return;

  const role = (localStorage.getItem('afenix_role')||'').toUpperCase();
  const display = localStorage.getItem('afenix_display_name')||'Usuario';
  if (!role || !['ADMIN','CAMARERO','CAJERO','MONITOR'].includes(role)) return;

  const isAdmin = role === 'ADMIN';
  const isCajero = role === 'CAJERO';
  const isMonitor = role === 'MONITOR';

  const ADMIN_MENU = [
    { href: '/admin.html', label: 'Panel', icon: 'panel' },
    { href: '/admin-inventario.html', label: 'Inventario', icon: 'inventory' },
    { href: '/admin-crear-plato.html', label: 'Crear plato', icon: 'create' },
    { href: '/admin-usuarios.html', label: 'Usuarios', icon: 'users' },
    { href: '/admin-historial.html', label: 'Historial', icon: 'history' },
    { href: '/admin-recibo.html', label: 'Recibo', icon: 'receipt' },
    { href: '/cajero-ventas.html', label: 'Ventas', icon: 'receipt' },
  ];
  const MESERO_MENU = [
    { href: '/mesero.html', label: 'Panel', icon: 'panel' },
    { href: '/mesero-crear-pedido.html', label: 'Crear pedido', icon: 'create' },
    { href: '/mesero-pedidos.html', label: 'Mis pedidos', icon: 'orders' },
  ];
  const CAJERO_MENU = [
    { href: '/cajero.html', label: 'Panel', icon: 'panel' },
    { href: '/cajero-ordenes.html', label: 'Órdenes', icon: 'orders' },
    { href: '/cajero-entregados.html', label: 'Entregados', icon: 'orders' },
    { href: '/cajero-ventas.html', label: 'Ventas', icon: 'receipt' },
  ];
  const MONITOR_MENU = [
    { href: '/monitor.html', label: 'Panel', icon: 'panel' },
    { href: '/monitor-ordenes.html', label: 'Órdenes', icon: 'orders' },
  ];

  let menu, roleLabel, sectionLabel;
  if (isAdmin) { menu = ADMIN_MENU; roleLabel = 'Administrador'; sectionLabel = 'Administración'; }
  else if (isCajero) { menu = CAJERO_MENU; roleLabel = 'Cajero'; sectionLabel = 'Caja'; }
  else if (isMonitor) { menu = MONITOR_MENU; roleLabel = 'Monitor'; sectionLabel = 'Cocina'; }
  else { menu = MESERO_MENU; roleLabel = 'Mesero'; sectionLabel = 'Servicio'; }
  const roleShort = roleLabel;

  const ICONS = {
    panel: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="8" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/><rect x="13" y="13" width="8" height="8" rx="1.5"/></svg>',
    inventory: '<svg viewBox="0 0 24 24"><path d="M3 7.5L12 3l9 4.5-9 4.5L3 7.5Z"/><path d="M3 12l9 4.5L21 12"/><path d="M3 16.5L12 21l9-4.5"/></svg>',
    create: '<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/><circle cx="12" cy="12" r="9" opacity="0.0"/></svg>',
    users: '<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.5"/><path d="M3 18c0-3 2.5-5 6-5s6 2 6 5"/><circle cx="17" cy="9" r="2.5"/><path d="M15.5 18c0-2 1.2-3.5 3-4"/></svg>',
    history: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 8v5l3 2"/><path d="M9 3h6"/></svg>',
    receipt: '<svg viewBox="0 0 24 24"><path d="M7 3h10l2 2v16H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/><path d="M9 9h8M9 13h8M9 17h5"/><path d="M14 3v4h4"/></svg>',
    orders: '<svg viewBox="0 0 24 24"><path d="M8 6h10"/><path d="M8 12h10"/><path d="M8 18h10"/><path d="M4 6h.01"/><path d="M4 12h.01"/><path d="M4 18h.01"/></svg>',
  };

  function initials(name){ return name.split(' ').map(n=>n[0]).slice(0,2).join('').toUpperCase().slice(0,2); }

  const currentPath = window.location.pathname;
  const itemsHtml = menu.map(item=>{
    const active = currentPath === item.href ? ' is-active' : '';
    return '<li class="sidebar__item'+active+'"><a href="'+item.href+'"><span class="sidebar__icon">'+(ICONS[item.icon]||'')+'</span><span>'+item.label+'</span></a></li>';
  }).join('');

  const sidebarHtml = ''
    + '<aside class="sidebar" id="sidebar" aria-label="Navegación principal">'
    + '<button class="sidebar__collapse-toggle" id="sidebarCollapseToggle" aria-label="Ocultar menú" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg></button>'
    + '<div class="sidebar__brand"><span class="logo__symbol">凤</span><span class="sidebar__brand-text"><strong>Afénix de Oro</strong><small>Sistema interno</small><span class="sidebar__role"><span class="sidebar__role-dot"></span>'+roleShort+'</span></span></div>'
    + '<nav class="sidebar__nav"><div class="sidebar__section">'+sectionLabel+'</div><ul class="sidebar__list">'+itemsHtml+'</ul></nav>'
    + '<div class="sidebar__footer"><div class="sidebar__user"><span class="sidebar__avatar">'+initials(display)+'</span><div style="min-width:0; flex:1;"><div class="sidebar__user-name">'+display.replace(/</g,'&lt;')+'</div><div class="sidebar__user-role">'+roleLabel+'</div></div></div><button class="sidebar__logout" id="sidebarLogout"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg> Cerrar sesión</button></div>'
    + '</aside><div class="sidebar-overlay" id="sidebarOverlay"></div>';

  document.addEventListener('DOMContentLoaded', function(){
    document.body.classList.add('has-sidebar');
    document.body.insertAdjacentHTML('afterbegin', sidebarHtml);

    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const toggleBtn = document.getElementById('sidebarToggle');
    const collapseToggle = document.getElementById('sidebarCollapseToggle');
    const collapseKey = 'afenix_sidebar_collapsed_' + role;

    function applyCollapsed(collapsed){
      if(collapsed){
        sidebar.classList.add('is-collapsed');
        document.body.classList.add('sidebar-collapsed');
        if(collapseToggle) collapseToggle.setAttribute('aria-label','Mostrar menú');
      } else {
        sidebar.classList.remove('is-collapsed');
        document.body.classList.remove('sidebar-collapsed');
        if(collapseToggle) collapseToggle.setAttribute('aria-label','Ocultar menú');
      }
    }
    try {
      const saved = localStorage.getItem(collapseKey);
      if(saved === '1' && window.innerWidth > 980){
        applyCollapsed(true);
      }
    } catch(e){}

    function toggleCollapse(){
      const nowCollapsed = !sidebar.classList.contains('is-collapsed');
      applyCollapsed(nowCollapsed);
      try { localStorage.setItem(collapseKey, nowCollapsed ? '1' : '0'); } catch(e){}
    }

    if(collapseToggle) collapseToggle.addEventListener('click', toggleCollapse);

    function openSidebar(){ sidebar.classList.add('is-open'); overlay.classList.add('is-open'); document.body.style.overflow='hidden'; }
    function closeSidebar(){ sidebar.classList.remove('is-open'); overlay.classList.remove('is-open'); document.body.style.overflow=''; }
    function toggleSidebar(){ sidebar.classList.contains('is-open') ? closeSidebar() : openSidebar(); }

    if (toggleBtn) toggleBtn.addEventListener('click', toggleSidebar);
    if (overlay) overlay.addEventListener('click', closeSidebar);
    document.addEventListener('keydown', function(e){ if(e.key==='Escape') closeSidebar(); });

    const sbLogout = document.getElementById('sidebarLogout');
    if (sbLogout) sbLogout.addEventListener('click', function(){
      ['afenix_access_token','afenix_refresh_token','afenix_display_name','afenix_role'].forEach(function(k){ localStorage.removeItem(k); });
      window.location.href='/secion.html';
    });

    sidebar.querySelectorAll('a').forEach(function(a){ a.addEventListener('click', function(){ if(window.innerWidth<=980) closeSidebar(); }); });

    window.AfenixSidebar = { open: openSidebar, close: closeSidebar, toggle: toggleSidebar, toggleCollapse: toggleCollapse };
  });

  function injectToggle(){
    const headerInner = document.querySelector('.app-header__inner');
    const existing = document.getElementById('sidebarToggle');
    if (!headerInner || existing) return;
    const btn = document.createElement('button');
    btn.id='sidebarToggle';
    btn.className='sidebar-toggle';
    btn.setAttribute('aria-label','Abrir menú');
    btn.setAttribute('type','button');
    btn.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
    headerInner.insertBefore(btn, headerInner.firstChild);
    btn.addEventListener('click', function(){
      const sb=document.getElementById('sidebar');
      const ov=document.getElementById('sidebarOverlay');
      if(!sb) return;
      const isOpen=sb.classList.contains('is-open');
      if(isOpen){ sb.classList.remove('is-open'); ov&&ov.classList.remove('is-open'); document.body.style.overflow=''; }
      else { sb.classList.add('is-open'); ov&&ov.classList.add('is-open'); document.body.style.overflow='hidden'; }
    });
  }
  if (document.readyState==='loading') document.addEventListener('DOMContentLoaded', injectToggle);
  else injectToggle();
  setTimeout(injectToggle, 300);
})();
