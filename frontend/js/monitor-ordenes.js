document.addEventListener('DOMContentLoaded', async () => {
  if (!Afenix.guardPage('MONITOR')) return;

  const $ = selector => document.querySelector(selector);
  const { api, toast, esc, date } = Afenix;
  const apiOrigin = 'https://pollo-api.hostless.app';
  const apiUrl = path => new URL(path, apiOrigin).toString();
  const mesaGrid = $('#mesaGrid');
  const detailPanel = $('#detailPanel');
  const ordersDetail = $('#ordersDetail');
  const detailTitle = $('#detailTitle');
  const detailSub = $('#detailSub');
  const lastUpdate = $('#lastUpdate');

  let pendingOrders = [];
  let receiptConfig = { restaurant_name: 'RESTAURANTE', logo_url: null };
  let selectedMesa = null;

  function getTableNumber(order) {
    const table = order.table_number ?? order.table_id;
    const number = Number(table);
    return Number.isFinite(number) ? number : null;
  }

  function groupByMesa(orders) {
    const grouped = Object.fromEntries(
      Array.from({ length: 12 }, (_, index) => [String(index + 1), []])
    );
    grouped['>12'] = [];
    orders.forEach(order => {
      const number = getTableNumber(order);
      if (number >= 1 && number <= 12) grouped[String(number)].push(order);
      else if (number > 12) grouped['>12'].push(order);
    });
    return grouped;
  }

  function renderMesaGrid() {
    const grouped = groupByMesa(pendingOrders);
    const cards = [];
    for (let number = 1; number <= 12; number += 1) {
      const key = String(number);
      const count = grouped[key].length;
      cards.push(`
        <button class="mesa-card ${count ? 'has-pending' : 'no-pending'} ${selectedMesa === key ? 'is-selected' : ''}"
          type="button" data-mesa="${key}" aria-pressed="${selectedMesa === key}">
          <h3>Mesa ${String(number).padStart(2, '0')}</h3>
          <span class="mesa-count">${count ? `${count} ${count === 1 ? 'orden pendiente' : 'órdenes pendientes'}` : 'Sin órdenes pendientes'}</span>
          <span class="mesa-sub">${count ? 'Toca para ver' : '—'}</span>
        </button>
      `);
    }

    const otherTables = grouped['>12'].length;
    cards.push(`
      <button class="mesa-card ${otherTables ? 'has-pending' : 'no-pending'} ${selectedMesa === '>12' ? 'is-selected' : ''}"
        type="button" data-mesa="&gt;12" aria-pressed="${selectedMesa === '>12'}">
        <h3>Mesas &gt; 12</h3>
        <span class="mesa-count">${otherTables ? `${otherTables} ${otherTables === 1 ? 'orden pendiente' : 'órdenes pendientes'}` : 'Sin órdenes pendientes'}</span>
        <span class="mesa-sub">${otherTables ? 'Agrupa las mesas 13 en adelante' : '—'}</span>
      </button>
    `);

    mesaGrid.innerHTML = cards.join('');
    mesaGrid.querySelectorAll('[data-mesa]').forEach(card => {
      card.addEventListener('click', () => openMesa(card.dataset.mesa));
    });
  }

  function orderCard(order) {
    const displayNumber = order.daily_number || order.id;
    const tableNumber = String(getTableNumber(order) ?? '').padStart(2, '0');
    const waiter = esc(`Mesero #${order.camarero_id || '?'}`);
    const createdAt = date(order.created_at);
    const status = esc(order.status);
    const items = (order.items || []).map(item => {
      const quantity = Number(item.quantity) || 0;
      const name = esc(item.dish_name || `Plato #${item.dish_id}`);
      const selections = (item.subcategory_selections || [])
        .map(selection => `${esc(selection.subcategory_name)}: ${esc(selection.option_name)}`)
        .join(' · ');
      const selectionMarkup = selections
        ? `<div style="font-size:.82rem;color:#6b5e56;margin-top:4px;">${selections}</div>`
        : '';
      return `<li><div><span>${name}</span>${selectionMarkup}</div><span><strong>x${quantity}</strong></span></li>`;
    }).join('') || '<li style="justify-content:center;color:var(--muted)">Sin platos</li>';
    const notes = order.notes
      ? `<div class="muted" style="margin-top:8px;font-size:.84rem;border-top:1px dashed #eadfcf;padding-top:8px;"><strong>Notas:</strong> ${esc(order.notes)}</div>`
      : '';
    const tableBadge = getTableNumber(order) > 12
      ? `<span class="mesa-badge">Mesa ${tableNumber}</span>`
      : '';

    return `<article class="order-card-monitor">
      <div class="order-card-monitor__head">
        <div>
          <h3 class="order-card-monitor__title">Orden #${esc(String(displayNumber))} · Mesa ${tableNumber} ${tableBadge}</h3>
          <div class="monitor-card__meta">Mesero: <strong>${waiter}</strong> · ${esc(createdAt)} · <span class="status status--${status}">${status}</span></div>
        </div>
        <span class="status status--${status}">${status}</span>
      </div>
      <ul class="items-list">${items}</ul>
      ${notes}
      <div style="display:flex;justify-content:flex-end;margin-top:12px;">
        <button class="btn btn--primary btn--small" type="button" data-print="${esc(String(order.id))}">Imprimir</button>
      </div>
    </article>`;
  }

  function openMesa(key, shouldScroll = true) {
    selectedMesa = key;
    renderMesaGrid();
    const grouped = groupByMesa(pendingOrders);
    const orders = grouped[key] || [];
    detailPanel.hidden = false;
    detailTitle.textContent = key === '>12' ? 'Mesas > 12' : `Mesa ${String(Number(key)).padStart(2, '0')}`;
    detailSub.textContent = orders.length
      ? `${orders.length} ${orders.length === 1 ? 'orden pendiente' : 'órdenes pendientes'}`
      : 'Sin órdenes pendientes';

    if (!orders.length) {
      ordersDetail.innerHTML = '<div class="empty-detail"><p style="font-size:1.05rem;margin:0 0 6px;">No hay órdenes pendientes</p><p class="muted">Las órdenes pendientes del ciclo actual aparecerán aquí.</p></div>';
    } else if (key === '>12') {
      const byTable = orders.reduce((groups, order) => {
        const table = String(getTableNumber(order));
        (groups[table] ||= []).push(order);
        return groups;
      }, {});
      ordersDetail.innerHTML = Object.keys(byTable).sort((a, b) => Number(a) - Number(b)).map(table => `
        <section style="margin-bottom:18px;">
          <h4 style="font-family:Cinzel,serif;font-size:.95rem;margin:0 0 10px;color:var(--ink);border-bottom:1px solid var(--line);padding-bottom:6px;">
            Mesa ${String(Number(table)).padStart(2, '0')} · ${byTable[table].length} ${byTable[table].length === 1 ? 'orden' : 'órdenes'}
          </h4>
          ${byTable[table].map(orderCard).join('')}
        </section>
      `).join('');
    } else {
      ordersDetail.innerHTML = orders.map(orderCard).join('');
    }

    ordersDetail.querySelectorAll('[data-print]').forEach(button => {
      button.addEventListener('click', async () => {
        button.disabled = true;
        button.textContent = 'Imprimiendo…';
        await handlePrint(button.dataset.print);
        button.textContent = 'Imprimir';
        button.disabled = false;
      });
    });
    if (shouldScroll) detailPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function printKitchenTicket(order) {
    const displayNumber = order.daily_number || order.id;
    const tableNumber = String(getTableNumber(order) ?? '').padStart(2, '0');
    const waiter = `Mesero #${order.camarero_id || '?'}`;
    const createdAt = new Date(order.created_at).toLocaleString('es-CO');
    const logo = receiptConfig.logo_url
      ? `<div style="text-align:center;margin:6px 0 8px;"><img src="${esc(receiptConfig.logo_url)}" alt="Logo" style="max-width:38mm;max-height:16mm;object-fit:contain;display:inline-block;"></div>`
      : '';
    const restaurantName = esc((receiptConfig.restaurant_name || 'RESTAURANTE').toUpperCase());
    const items = (order.items || []).map(item => {
      const name = esc(item.dish_name || `Plato #${item.dish_id}`);
      const selections = (item.subcategory_selections || [])
        .map(selection => `${esc(selection.subcategory_name)}: ${esc(selection.option_name)}`)
        .join(' / ');
      const selectionMarkup = selections
        ? `<div style="font-size:7pt;text-align:left;padding-left:18px;color:#333;">${selections}</div>`
        : '';
      return `<div style="padding:4px 0;border-bottom:1px dashed #ddd;">
        <div style="display:flex;justify-content:center;align-items:center;gap:6px;font-size:10pt;">
          <span style="font-weight:700;">${Number(item.quantity) || 0}x</span>
          <span style="flex:1;text-align:left;word-break:break-word;">${name}</span>
        </div>${selectionMarkup}
      </div>`;
    }).join('') || '<div style="text-align:center;padding:8px;color:#555;">Sin platos</div>';

    const printWindow = window.open('', '_blank');
    if (!printWindow) return false;
    printWindow.document.write(`<!doctype html><html lang="es"><head><meta charset="utf-8">
      <title>Comprobante Cocina - Pedido #${esc(String(displayNumber))}</title>
      <style>
        @page{size:57.5mm auto;margin:2mm}
        *{box-sizing:border-box}
        body{margin:0;padding:0;display:flex;justify-content:center;background:#fff;color:#000;font-family:'Courier New',Courier,monospace}
        .ticket{width:57.5mm;max-width:57.5mm;background:#fff;padding:4mm 3mm;font-size:9pt;line-height:1.35}
        .sep{border:none;border-top:1px solid #000;margin:8px 0}
        .sep-dashed{border:none;border-top:1px dashed #000;margin:8px 0}
        .items{margin:6px 0}
      </style></head><body><main class="ticket">${logo}
        <div style="text-align:center;font-weight:700;font-size:13pt;text-transform:uppercase;margin:4px 0 6px;">${restaurantName}</div>
        <hr class="sep">
        <div style="font-size:7.5pt;text-align:center;margin:4px 0 6px;">
          Pedido #${esc(String(displayNumber))} · Mesa ${tableNumber} · ${esc(waiter)}<br>${esc(createdAt)}
        </div>
        <hr class="sep-dashed"><div class="items">${items}</div><hr class="sep-dashed">
        <div style="text-align:center;font-size:7pt;margin-top:8px;">— COMPROBANTE COCINA —</div>
      </main><script>window.onload=function(){setTimeout(function(){window.print();window.close()},300)}<\/script></body></html>`);
    printWindow.document.close();
    printWindow.focus();
    return true;
  }

  async function handlePrint(orderId) {
    const order = pendingOrders.find(candidate => String(candidate.id) === String(orderId));
    if (!order) {
      toast('Orden no encontrada. Actualiza la lista e inténtalo de nuevo.', 'error');
      return;
    }
    if (!['PENDIENTE', 'NUEVO'].includes(order.status)) {
      toast('Solo se pueden imprimir órdenes pendientes.', 'error');
      return;
    }
    if (!printKitchenTicket(order)) {
      toast('No se pudo abrir la ventana de impresión. La orden sigue pendiente.', 'error');
      return;
    }

    try {
      await new Promise(resolve => window.setTimeout(resolve, 700));
      await api(apiUrl(`/api/v1/orders/${encodeURIComponent(order.id)}`), {
        method: 'PUT',
        body: JSON.stringify({ status: 'EN_COCINA' })
      });
      toast(`Orden #${order.daily_number || order.id} enviada a cocina. El estado quedó guardado.`);
      await loadPending();
      if (selectedMesa) openMesa(selectedMesa);
    } catch (error) {
      toast(`Se abrió la impresión, pero no se pudo guardar el cambio: ${error.message}`, 'error');
    }
  }

  async function loadPending() {
    const orders = await api(apiUrl('/api/v1/orders/monitor/pending?limit=100')) || [];
    pendingOrders = orders
      .filter(order => ['PENDIENTE', 'NUEVO'].includes(order.status))
      .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    renderMesaGrid();
    lastUpdate.textContent = `Actualizado: ${new Date().toLocaleTimeString('es-CO')}`;
    if (selectedMesa && !detailPanel.hidden) openMesa(selectedMesa, false);
  }

  async function loadReceiptConfig() {
    const config = await api(apiUrl('/api/v1/receipt-config'));
    if (!config) return;
    receiptConfig.restaurant_name = config.restaurant_name || 'RESTAURANTE';
    const logoUrl = config.logo_url || config.logo_path;
    receiptConfig.logo_url = logoUrl
      ? new URL(logoUrl, apiOrigin).toString()
      : null;
  }

  $('#closeDetail').addEventListener('click', () => {
    detailPanel.hidden = true;
    selectedMesa = null;
    renderMesaGrid();
  });
  $('#refreshBtn').addEventListener('click', async event => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      await loadPending();
    } catch (error) {
      toast(`No se pudieron cargar las órdenes: ${error.message}`, 'error');
    } finally {
      button.disabled = false;
    }
  });

  try {
    await loadPending();
  } catch (error) {
    toast(`No se pudieron cargar las órdenes: ${error.message}`, 'error');
  }
  try {
    await loadReceiptConfig();
  } catch (error) {
    toast(`No se pudo cargar la configuración del recibo: ${error.message}`, 'error');
  }

  window.setInterval(async () => {
    try {
      await loadPending();
    } catch (error) {
      toast(`No se pudieron actualizar las órdenes: ${error.message}`, 'error');
    }
  }, 12000);
});
