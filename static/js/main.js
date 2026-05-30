// FairBet Lab — main.js
// Autenticación: sesión Django (cookie). Sin JWT ni localStorage de tokens.

let betslip = JSON.parse(localStorage.getItem('fb_betslip') || '[]');

// ── CSRF ───────────────────────────────────────────────────────────────────────
function getCsrf() {
  return document.cookie.split(';')
    .find(c => c.trim().startsWith('csrftoken='))
    ?.split('=')[1] || '';
}

// ── API fetch con sesión Django ────────────────────────────────────────────────
async function apiFetch(url, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  if (opts.method && opts.method !== 'GET') {
    headers['X-CSRFToken'] = getCsrf();
  }
  const res = await fetch(url, { ...opts, headers });
  if (res.status === 401) {
    window.location.href = '/login/';
    return null;
  }
  if (res.status === 403) {
    // If it's a CSRF error or DRF error, it might be JSON. 
    // Don't redirect immediately so we can show the error toast.
    const ct = res.headers.get('content-type') || '';
    if (!ct.includes('application/json')) {
      window.location.href = '/login/';
      return null;
    }
  }
  return res;
}

// ── Toast ──────────────────────────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const wrap = document.getElementById('toast-wrap');
  if (!wrap) return;
  const icons = { success: 'fa-circle-check', error: 'fa-circle-xmark', info: 'fa-circle-info' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<i class="fa-solid ${icons[type] || icons.info}"></i><span>${msg}</span>`;
  wrap.appendChild(t);
  setTimeout(() => {
    t.style.transition = '.3s';
    t.style.opacity = '0';
    t.style.transform = 'translateX(30px)';
    setTimeout(() => t.remove(), 320);
  }, 3000);
}

// ── Betslip ────────────────────────────────────────────────────────────────────
function saveBetslip() { localStorage.setItem('fb_betslip', JSON.stringify(betslip)); }

function limpiarBetslip() {
  betslip = [];
  document.querySelectorAll('.cuota-btn.selected').forEach(el => el.classList.remove('selected'));
  saveBetslip();
  renderBetslip();
}

function addToBetslip(cuotaId, seleccion, odds, evento, mercado) {
  const idx = betslip.findIndex(b => b.cuotaId === cuotaId);
  if (idx !== -1) {
    betslip.splice(idx, 1);
    document.querySelectorAll(`[data-cuota="${cuotaId}"]`).forEach(el => el.classList.remove('selected'));
  } else {
    betslip.push({ cuotaId, seleccion, odds: parseFloat(String(odds).replace(',', '.')), evento, mercado });
    document.querySelectorAll(`[data-cuota="${cuotaId}"]`).forEach(el => el.classList.add('selected'));
    toast(`${seleccion} agregado al ticket`, 'info');
  }
  saveBetslip();
  renderBetslip();
}

function removeFromBetslip(cuotaId) {
  betslip = betslip.filter(b => b.cuotaId !== cuotaId);
  document.querySelectorAll(`[data-cuota="${cuotaId}"]`).forEach(el => el.classList.remove('selected'));
  saveBetslip();
  renderBetslip();
}

let betslipTab = 'simple';

function setBetslipTab(tab) {
  betslipTab = tab;
  document.getElementById('tab-simple')?.classList.toggle('active', tab === 'simple');
  document.getElementById('tab-combinada')?.classList.toggle('active', tab === 'combinada');
  renderBetslip();
}

function renderBetslip() {
  const body    = document.getElementById('bs-body');
  const foot    = document.getElementById('bs-foot');
  const countEl = document.getElementById('bs-count');
  const tabsEl  = document.getElementById('bs-tabs');

  if (countEl) countEl.textContent = betslip.length || '';
  if (!body) return;

  if (!betslip.length) {
    if (tabsEl) tabsEl.style.display = 'none';
    body.innerHTML = `
      <div class="betslip-empty">
        <i class="fa-solid fa-ticket"></i>
        <p>Selecciona una cuota para<br/>agregar al ticket</p>
      </div>`;
    if (foot) foot.style.display = 'none';
    return;
  }

  if (tabsEl) tabsEl.style.display = 'flex';

  const groups = {};
  betslip.forEach(b => {
    if (!groups[b.evento]) groups[b.evento] = [];
    groups[b.evento].push(b);
  });

  let html = '';
  if (betslipTab === 'simple') {
    for (const [evento, items] of Object.entries(groups)) {
      html += `<div class="bs-grupo"><div class="bs-grupo-header">${evento}</div>`;
      items.forEach(b => {
        html += `
          <div class="bs-item">
            <button class="bs-remove" onclick="removeFromBetslip(${b.cuotaId})">
              <i class="fa-solid fa-xmark"></i>
            </button>
            <div class="bs-seleccion">${b.seleccion}</div>
            <div class="bs-odds">${b.odds.toFixed(2)}</div>
            <input type="number" class="bs-monto-sm" id="monto-${b.cuotaId}" placeholder="Monto" min="1" oninput="calcBetslip()">
            <div style="font-size:11px;color:var(--text-3);margin-top:4px">Ganancia: <span id="ganancia-${b.cuotaId}" class="c-green">0.00</span> Fichas</div>
          </div>`;
      });
      html += `</div>`;
    }
  } else {
    for (const [evento, items] of Object.entries(groups)) {
      html += `<div class="bs-grupo"><div class="bs-grupo-header">${evento}</div>`;
      items.forEach(b => {
        html += `
          <div class="bs-item">
            <button class="bs-remove" onclick="removeFromBetslip(${b.cuotaId})">
              <i class="fa-solid fa-xmark"></i>
            </button>
            <div class="bs-seleccion">${b.seleccion}</div>
            <div class="bs-odds">${b.odds.toFixed(2)}</div>
          </div>`;
      });
      html += `</div>`;
    }
  }

  body.innerHTML = html;
  if (foot) foot.style.display = 'block';

  const footMontoInput = document.getElementById('bs-monto');
  const restrictBanner = document.getElementById('bs-restrict-banner');
  if (betslipTab === 'simple') {
    if (footMontoInput) footMontoInput.style.display = 'none';
    if (restrictBanner) restrictBanner.style.display = 'none';
  } else {
    if (footMontoInput) footMontoInput.style.display = 'block';
  }

  calcBetslip();
}

function calcBetslip() {
  const footTi = document.getElementById('bs-odds-total');
  const footGi = document.getElementById('bs-ganancia');
  const footMonto = document.getElementById('bs-monto');
  const btn = document.getElementById('btn-apostar');

  if (betslipTab === 'simple') {
    if (footTi) footTi.parentElement.style.display = 'none';
    let totalP = 0;
    betslip.forEach(b => {
      const mi = document.getElementById(`monto-${b.cuotaId}`);
      const go = document.getElementById(`ganancia-${b.cuotaId}`);
      const val = parseFloat(mi?.value) || 0;
      if (go) go.textContent = (val * b.odds).toFixed(2);
      totalP += (val * b.odds);
    });
    if (footGi) footGi.textContent = `${totalP.toFixed(2)} Fichas`;
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-check"></i> Confirmar Simples';
    }
  } else {
    if (footTi) footTi.parentElement.style.display = 'flex';
    const monto = parseFloat(footMonto?.value) || 0;
    const totalOdds = betslip.reduce((acc, b) => acc * b.odds, 1);
    if (footTi) footTi.textContent = totalOdds.toFixed(2);
    if (footGi) footGi.textContent = `${(monto * totalOdds).toFixed(2)} Fichas`;

    const restrictBanner = document.getElementById('bs-restrict-banner');
    
    // Validar por mercado en vez de evento para permitir Same Game Parlay (Bet Builder)
    const mercados = new Set(betslip.map(b => b.mercado));
    if (mercados.size < betslip.length && betslip.length > 0) {
      if (btn) {
         btn.disabled = true;
         btn.innerHTML = 'Restringido: Opciones incompatibles';
      }
      if (restrictBanner) restrictBanner.style.display = 'block';
    } else if (betslip.length < 2) {
      if (btn) {
         btn.disabled = true;
         btn.innerHTML = 'Faltan selecciones para Combinada';
      }
      if (restrictBanner) restrictBanner.style.display = 'none';
    } else {
      if (btn) {
         btn.disabled = false;
         btn.innerHTML = '<i class="fa-solid fa-check"></i> Confirmar Combinada';
      }
      if (restrictBanner) restrictBanner.style.display = 'none';
    }
  }
}

// ── Confirmar apuesta ──────────────────────────────────────────────────────────
async function confirmarApuesta() {
  if (!betslip.length) { toast('Agrega al menos una selección al ticket', 'error'); return; }

  const btn = document.getElementById('btn-apostar');
  if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Procesando...'; }

  try {
    if (betslipTab === 'simple') {
      const promises = [];
      for (const b of betslip) {
        const monto = parseFloat(document.getElementById(`monto-${b.cuotaId}`)?.value || 0);
        if (monto > 0) {
          promises.push(apiFetch('/api/apuestas/', {
            method: 'POST',
            body: JSON.stringify({
              cuota_id: b.cuotaId,
              monto: monto.toFixed(4),
              cuota_esperada: b.odds.toFixed(4),
              clave_idempotencia: crypto.randomUUID(),
            })
          }));
        }
      }
      if (promises.length === 0) {
        toast('Ingresa monto en al menos una apuesta', 'error');
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-check"></i> Confirmar Simples'; }
        return;
      }
      const results = await Promise.all(promises);
      const errors = [];
      for (const res of results) {
         if (!res) {
             errors.push('No response');
         } else if (!res.ok) {
             const data = await res.json().catch(() => null);
             errors.push(data?.error || data?.detail || `Error ${res.status}`);
             toast(data?.error || data?.detail || `Error ${res.status}`, 'error');
         }
      }
      if (errors.length > 0) {
        toast(`Se completaron algunas, pero fallaron ${errors.length}`, 'warning');
        actualizarSaldoNavbar();
      } else {
        toast('Apuestas simples completadas con éxito', 'success');
        limpiarBetslip();
        setTimeout(() => window.location.reload(), 1500);
      }
    } else {
      const monto = parseFloat(document.getElementById('bs-monto')?.value || 0);
      if (monto <= 0) { 
        toast('Ingresa un monto válido', 'error'); 
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-check"></i> Confirmar Combinada'; }
        return; 
      }
      const res = await apiFetch('/api/apuestas/combinada/', {
        method: 'POST',
        body: JSON.stringify({
          cuota_ids: betslip.map(b => b.cuotaId),
          monto: monto.toFixed(4),
          clave_idempotencia: crypto.randomUUID(),
        })
      });
      if (!res) return;
      if (res.ok) {
        toast('Apuesta combinada aceptada con éxito', 'success');
        limpiarBetslip();
        setTimeout(() => window.location.reload(), 1500);
      } else {
        const data = await res.json().catch(() => null);
        toast(data?.error || data?.detail || `Error ${res.status} al procesar la apuesta`, 'error');
      }
    }
  } catch (e) {
    toast('Error inesperado: ' + (e?.message || 'desconocido'), 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = betslipTab === 'simple' ? '<i class="fa-solid fa-check"></i> Confirmar Simples' : '<i class="fa-solid fa-check"></i> Confirmar Combinada'; }
  }
}

// ── Actualizar saldo en navbar (sin recargar página) ───────────────────────────
async function actualizarSaldoNavbar() {
  const el = document.getElementById('nav-balance-val');
  if (!el) return;
  const res = await apiFetch('/api/wallet/saldo/');
  if (!res?.ok) return;
  const d = await res.json();
  el.textContent = `${parseFloat(String(d.saldo_disponible).replace(',', '.')).toFixed(2)} Fichas`;
}

// ── Al cargar la página ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  renderBetslip();
  // Marcar cuotas que ya están en el betslip guardado
  betslip.forEach(b => {
    document.querySelectorAll(`[data-cuota="${b.cuotaId}"]`)
      .forEach(el => el.classList.add('selected'));
  });
  const mi = document.getElementById('bs-monto');
  if (mi) mi.addEventListener('input', calcBetslip);
});
