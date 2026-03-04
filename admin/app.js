/* ── Config ── */
const API = 'http://127.0.0.1:8000';

/* ── State ── */
let products = [];
let deleteTarget = null;
let editTarget = null;

/* ── Init ── */
document.addEventListener('DOMContentLoaded', () => {
  checkStatus();
  loadProducts();
  loadPrompt();
  setupNav();
  setupPromptCounter();
});

/* ── Navigation ── */
function setupNav() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', e => {
      e.preventDefault();
      navigate(item.dataset.section);
    });
  });
}

function navigate(section) {
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));

  const navEl = document.querySelector(`.nav-item[data-section="${section}"]`);
  if (navEl) navEl.classList.add('active');
  document.getElementById(`section-${section}`)?.classList.add('active');

  if (section === 'products') loadProducts();
}

/* ── API Status ── */
async function checkStatus() {
  const dot  = document.getElementById('statusDot');
  const text = document.getElementById('statusText');
  try {
    const r = await fetch(`${API}/`, { signal: AbortSignal.timeout(3000) });
    if (r.ok) {
      dot.className  = 'status-dot online';
      text.textContent = 'API online';
    } else throw new Error();
  } catch {
    dot.className  = 'status-dot offline';
    text.textContent = 'API offline';
  }
}

/* ── Products ── */
async function loadProducts() {
  const tbody = document.getElementById('productsBody');
  tbody.innerHTML = '<tr><td colspan="6" class="loading-row">Loading…</td></tr>';
  try {
    const r = await fetch(`${API}/admin/products`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    products = await r.json();
    renderProducts();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="loading-row" style="color:var(--red)">
      Failed to load products. Is the API running at <code>${API}</code>?
    </td></tr>`;
  }
}

function renderProducts() {
  const tbody = document.getElementById('productsBody');
  if (!products.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="loading-row">No products yet. Add one!</td></tr>';
    return;
  }
  tbody.innerHTML = products.map(p => `
    <tr>
      <td><span class="id-chip">#${p.id}</span></td>
      <td>${p.image_url
        ? `<img class="product-img" src="${esc(p.image_url)}" alt="" onerror="this.outerHTML='<div class=img-placeholder>📦</div>'">`
        : '<div class="img-placeholder">📦</div>'
      }</td>
      <td>
        <div class="product-name">${esc(p.name)}</div>
      </td>
      <td><span class="price-tag">$${parseFloat(p.price).toFixed(2)}</span></td>
      <td><div class="product-desc">${esc(p.description || '—')}</div></td>
      <td>
        <div class="actions">
          <button class="btn btn-ghost btn-icon" title="Edit" onclick="openEdit(${p.id})">✎</button>
          <button class="btn btn-ghost btn-icon" title="Delete" style="color:var(--red)" onclick="openDelete(${p.id})">✕</button>
        </div>
      </td>
    </tr>
  `).join('');
}

/* ── Add Product ── */
function resetForm() {
  document.getElementById('editId').value    = '';
  document.getElementById('fieldName').value = '';
  document.getElementById('fieldPrice').value = '';
  document.getElementById('fieldDesc').value  = '';
  document.getElementById('fieldImg').value   = '';
  document.getElementById('imgPreview').innerHTML = '<span>Preview</span>';
  document.getElementById('formTitle').textContent = 'Add Product';
  document.getElementById('saveBtn').textContent   = 'Save Product';
}

async function saveProduct() {
  const name  = document.getElementById('fieldName').value.trim();
  const price = parseFloat(document.getElementById('fieldPrice').value);
  const desc  = document.getElementById('fieldDesc').value.trim();
  const img   = document.getElementById('fieldImg').value.trim();

  if (!name || isNaN(price) || price < 0) {
    toast('Name and a valid price are required.', 'error');
    return;
  }

  const payload = { name, price, description: desc, image_url: img || null };
  const editId  = document.getElementById('editId').value;
  const isEdit  = !!editId;

  try {
    const r = await fetch(
      isEdit ? `${API}/admin/products/${editId}` : `${API}/admin/products`,
      {
        method: isEdit ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }
    );
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    toast(isEdit ? 'Product updated!' : 'Product added!', 'success');
    resetForm();
    navigate('products');
  } catch (err) {
    toast('Save failed: ' + err.message, 'error');
  }
}

function previewImg() {
  const url = document.getElementById('fieldImg').value.trim();
  const el  = document.getElementById('imgPreview');
  if (url) {
    el.innerHTML = `<img src="${esc(url)}" alt="" onerror="this.parentElement.innerHTML='<span>Bad URL</span>'">`;
  } else {
    el.innerHTML = '<span>Preview</span>';
  }
}

/* ── Edit Modal ── */
function openEdit(id) {
  const p = products.find(x => x.id === id);
  if (!p) return;
  editTarget = id;
  document.getElementById('mName').value  = p.name;
  document.getElementById('mPrice').value = p.price;
  document.getElementById('mDesc').value  = p.description || '';
  document.getElementById('mImg').value   = p.image_url   || '';
  const prev = document.getElementById('mImgPreview');
  prev.innerHTML = p.image_url
    ? `<img src="${esc(p.image_url)}" alt="" onerror="this.parentElement.innerHTML='<span>Bad URL</span>'">`
    : '<span>Preview</span>';
  document.getElementById('modalOverlay').classList.add('open');
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
  editTarget = null;
}

function previewModalImg() {
  const url = document.getElementById('mImg').value.trim();
  const el  = document.getElementById('mImgPreview');
  el.innerHTML = url
    ? `<img src="${esc(url)}" alt="" onerror="this.parentElement.innerHTML='<span>Bad URL</span>'">`
    : '<span>Preview</span>';
}

async function updateProduct() {
  if (!editTarget) return;
  const name  = document.getElementById('mName').value.trim();
  const price = parseFloat(document.getElementById('mPrice').value);
  const desc  = document.getElementById('mDesc').value.trim();
  const img   = document.getElementById('mImg').value.trim();

  if (!name || isNaN(price)) { toast('Name and price required.', 'error'); return; }

  try {
    const r = await fetch(`${API}/admin/products/${editTarget}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, price, description: desc, image_url: img || null }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    toast('Product updated!', 'success');
    closeModal();
    loadProducts();
  } catch (err) {
    toast('Update failed: ' + err.message, 'error');
  }
}

/* ── Delete Modal ── */
function openDelete(id) {
  const p = products.find(x => x.id === id);
  if (!p) return;
  deleteTarget = id;
  document.getElementById('deleteName').textContent = p.name;
  document.getElementById('deleteOverlay').classList.add('open');
}

function closeDelete() {
  document.getElementById('deleteOverlay').classList.remove('open');
  deleteTarget = null;
}

async function confirmDelete() {
  if (!deleteTarget) return;
  try {
    const r = await fetch(`${API}/admin/products/${deleteTarget}`, { method: 'DELETE' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    toast('Product deleted.', 'success');
    closeDelete();
    loadProducts();
  } catch (err) {
    toast('Delete failed: ' + err.message, 'error');
  }
}

/* ── System Prompt ── */
const DEFAULT_PROMPT = `You are a friendly WhatsApp sales assistant.
Use only the provided products to answer clearly and in a friendly way.
Respond using bullet points and emojis where appropriate.
Keep it concise and helpful.
Keep in mind WhatsApp formatting and character limits.

Ensure WhatsApp text formatting rules while responding:
- Use single asterisks * for bold like *bold*.
- Use underscores _ for italics like _italics_.
- Use tildes ~ for strikethrough like ~strikethrough~.
- Use triple backticks \`\`\` for monospace.

Be concise, persuasive, and helpful.`;

async function loadPrompt() {
  const ta = document.getElementById('systemPrompt');
  try {
    const r = await fetch(`${API}/admin/prompt`);
    if (r.ok) {
      const data = await r.json();
      ta.value = data.prompt || DEFAULT_PROMPT;
    } else {
      ta.value = DEFAULT_PROMPT;
    }
  } catch {
    ta.value = DEFAULT_PROMPT;
  }
  updateCharCount();
}

async function savePrompt() {
  const prompt = document.getElementById('systemPrompt').value.trim();
  if (!prompt) { toast('Prompt cannot be empty.', 'error'); return; }
  try {
    const r = await fetch(`${API}/admin/prompt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    toast('Prompt saved!', 'success');
  } catch (err) {
    // If the endpoint doesn't exist yet, save locally and show hint
    localStorage.setItem('adminPrompt', prompt);
    toast('Saved locally (add /admin/prompt endpoint to persist)', 'success');
  }
}

function setupPromptCounter() {
  document.getElementById('systemPrompt').addEventListener('input', updateCharCount);
}
function updateCharCount() {
  const len = document.getElementById('systemPrompt').value.length;
  document.getElementById('charCount').textContent = `${len.toLocaleString()} character${len !== 1 ? 's' : ''}`;
}

/* ── Toast ── */
let toastTimer;
function toast(msg, type = 'success') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className   = `toast ${type} show`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 3000);
}

/* ── Utils ── */
function esc(str) {
  if (!str) return '';
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}