// ============================================
// FILE: Api.gs — Google Sheets Database Handler
// ============================================

// ─── CORE HELPERS ───────────────────────────

var _db = null;
function getDb() {
  if (!_db) _db = SpreadsheetApp.openById('1NHiW47zPBM7CDZTFE6QIfeOT2ahzt2uo3ZmebXHI-6s');
  return _db;
}

function getSheet(name) {
  return getDb().getSheetByName(name);
}

function sheetData(name) {
  const sheet = getSheet(name);
  if (!sheet) return { headers: [], rows: [] };
  const lastRow = sheet.getLastRow();
  if (lastRow < 1) return { headers: [], rows: [] };
  const all = sheet.getDataRange().getValues();
  if (all.length === 0) return { headers: [], rows: [] };
  const headers = all[0].map(String);
  const rows = all.slice(1).map(function(row) {
    const obj = {};
    headers.forEach(function(h, i) {
      var v = row[i];
      if (v instanceof Date) {
        obj[h] = (v.getHours() === 0 && v.getMinutes() === 0 && v.getSeconds() === 0)
          ? Utilities.formatDate(v, 'Asia/Bangkok', 'yyyy-MM-dd')
          : Utilities.formatDate(v, 'Asia/Bangkok', "yyyy-MM-dd'T'HH:mm:ss");
      } else {
        obj[h] = v;
      }
    });
    return obj;
  });
  return { headers: headers, rows: rows };
}

function nextId(name) {
  const data = sheetData(name);
  if (data.rows.length === 0) return 1;
  const ids = data.rows.map(function(r) { return parseInt(r.id) || 0; });
  return Math.max.apply(null, ids) + 1;
}

function dbInsert(name, obj) {
  const sheet = getSheet(name);
  if (!sheet) throw new Error('Sheet not found: ' + name);
  const lastCol = sheet.getLastColumn();
  const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0].map(String);
  obj.id = nextId(name);
  if (headers.indexOf('created_at') >= 0 && !obj.created_at) {
    obj.created_at = Utilities.formatDate(new Date(), 'Asia/Bangkok', "yyyy-MM-dd'T'HH:mm:ss");
  }
  const row = headers.map(function(h) {
    return (obj[h] !== undefined && obj[h] !== null) ? obj[h] : '';
  });
  sheet.appendRow(row);
  SpreadsheetApp.flush();
  return obj;
}

function dbUpdate(name, id, updates) {
  const sheet = getSheet(name);
  if (!sheet) return false;
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return false;
  const lastCol = sheet.getLastColumn();
  const all = sheet.getRange(1, 1, lastRow, lastCol).getValues();
  const headers = all[0].map(String);
  const idIdx = headers.indexOf('id');
  for (var i = 1; i < all.length; i++) {
    if (String(all[i][idIdx]) === String(id)) {
      Object.keys(updates).forEach(function(k) {
        var col = headers.indexOf(k);
        if (col >= 0) {
          var val = (updates[k] !== null && updates[k] !== undefined) ? updates[k] : '';
          sheet.getRange(i + 1, col + 1).setValue(val);
        }
      });
      SpreadsheetApp.flush();
      return true;
    }
  }
  return false;
}

function dbDelete(name, filterFn) {
  const sheet = getSheet(name);
  if (!sheet) return;
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;
  const lastCol = sheet.getLastColumn();
  const all = sheet.getRange(1, 1, lastRow, lastCol).getValues();
  const headers = all[0].map(String);
  for (var i = all.length - 1; i >= 1; i--) {
    const obj = {};
    headers.forEach(function(h, j) { obj[h] = all[i][j]; });
    if (filterFn(obj)) sheet.deleteRow(i + 1);
  }
  SpreadsheetApp.flush();
}

// ─── EXPENSE ────────────────────────────────

function saveExpense(data) {
  const sources = sheetData('expense_sources').rows;
  const sourceMap = {};
  sources.forEach(function(s) { sourceMap[s.name] = parseInt(s.id); });
  const sourceId = sourceMap[data.source] || 1;

  const txn = dbInsert('expense_transactions', {
    source_id:    sourceId,
    expense_date: data.date,
    total:        parseFloat(data.total) || 0,
    note:         data.note || ''
  });

  (data.items || []).forEach(function(item) {
    dbInsert('expense_items', {
      transaction_id: txn.id,
      description:    item.description,
      quantity:       parseFloat(item.quantity)   || 1,
      unit_price:     parseFloat(item.unit_price) || 0,
      unit:           item.unit || 'Pcs'
    });
  });

  return { success: true, id: txn.id };
}

// ─── INCOME ─────────────────────────────────

function saveIncome(data) {
  const customers = sheetData('customers').rows;
  var customer = customers.find(function(c) { return c.name === data.customer; });
  var customerId;
  if (customer) {
    customerId = parseInt(customer.id);
  } else {
    var newC = dbInsert('customers', { name: data.customer });
    customerId = newC.id;
  }

  const txn = dbInsert('income_transactions', {
    invoice_no:  data.invoice_no,
    customer_id: customerId,
    issue_date:  data.date,
    total:       parseFloat(data.total) || 0,
    status:      'paid'
  });

  (data.items || []).forEach(function(item) {
    dbInsert('income_invoice_items', {
      transaction_id: txn.id,
      description:    item.description,
      quantity:       parseFloat(item.quantity)   || 1,
      unit_price:     parseFloat(item.unit_price) || 0
    });
  });

  return { success: true, id: txn.id };
}

// ─── HISTORY ────────────────────────────────

function getHistory() {
  const expenses  = sheetData('expense_transactions').rows;
  const sources   = sheetData('expense_sources').rows;
  const incomes   = sheetData('income_transactions').rows;
  const customers = sheetData('customers').rows;

  const sourceMap = {};
  sources.forEach(function(s) { sourceMap[String(s.id)] = s.name; });

  const custMap = {};
  customers.forEach(function(c) { custMap[String(c.id)] = c.name; });

  const result = [];

  expenses.slice()
    .forEach(function(e) {
      result.push({
        id:         parseInt(e.id),
        type:       'expense',
        date:       e.expense_date,
        created_at: e.created_at || e.expense_date,
        source:     sourceMap[String(e.source_id)] || '-',
        total:      parseFloat(e.total) || 0,
        note:       e.note || ''
      });
    });

  incomes.slice()
    .forEach(function(i) {
      result.push({
        id:         parseInt(i.id),
        type:       'income',
        date:       i.issue_date,
        created_at: i.created_at || i.issue_date,
        source:     'รายรับ',
        invoice_no: i.invoice_no,
        customer:   custMap[String(i.customer_id)] || '-',
        total:      parseFloat(i.total) || 0
      });
    });

  result.sort(function(a, b) {
    var dateCmp = String(b.date).localeCompare(String(a.date));
    if (dateCmp !== 0) return dateCmp;
    return String(b.created_at).localeCompare(String(a.created_at));
  });
  return result.slice(0, 500);
}

// ─── SUMMARY (แทน monthly_summary VIEW) ──────

function getSummary() {
  const incomes  = sheetData('income_transactions').rows;
  const expenses = sheetData('expense_transactions').rows;
  const monthMap = {};

  incomes.forEach(function(i) {
    const d = String(i.issue_date || '');
    if (d.length < 7) return;
    const m = d.slice(0, 7);
    if (!monthMap[m]) monthMap[m] = { month: m, total_income: 0, total_expense: 0 };
    monthMap[m].total_income += parseFloat(i.total) || 0;
  });

  expenses.forEach(function(e) {
    const d = String(e.expense_date || '');
    if (d.length < 7) return;
    const m = d.slice(0, 7);
    if (!monthMap[m]) monthMap[m] = { month: m, total_income: 0, total_expense: 0 };
    monthMap[m].total_expense += parseFloat(e.total) || 0;
  });

  return Object.values(monthMap)
    .sort(function(a, b) { return b.month.localeCompare(a.month); })
    .slice(0, 12);
}

// ─── EXPENSE DESCRIPTIONS ───────────────────

function getExpenseDescriptions() {
  const rows = sheetData('expense_items').rows;
  const unique = [];
  const seen = {};
  rows.forEach(function(r) {
    if (r.description && !seen[r.description]) {
      seen[r.description] = true;
      unique.push(r.description);
    }
  });
  return unique.sort(function(a, b) { return a.localeCompare(b, 'th'); });
}

// ─── TRANSACTION ITEMS ──────────────────────

function getTransactionItems(params) {
  const type = params.type;
  const id   = parseInt(params.id);

  if (type === 'expense') {
    const rows = sheetData('expense_items').rows;
    return rows.filter(function(r) { return parseInt(r.transaction_id) === id; })
               .sort(function(a,b) { return parseInt(a.id) - parseInt(b.id); });
  } else {
    const rows = sheetData('income_invoice_items').rows;
    return rows.filter(function(r) { return parseInt(r.transaction_id) === id; })
               .sort(function(a,b) { return parseInt(a.id) - parseInt(b.id); });
  }
}

// ─── SEARCH ITEMS ───────────────────────────

function searchItems(params) {
  const keyword  = (params.keyword  || '').toLowerCase();
  const source   = params.source   || null;
  const dateFrom = params.dateFrom || null;
  const dateTo   = params.dateTo   || null;

  if (!keyword || keyword.trim().length < 1) return [];

  const items   = sheetData('expense_items').rows;
  const txns    = sheetData('expense_transactions').rows;
  const sources = sheetData('expense_sources').rows;

  const sourceMap = {};
  sources.forEach(function(s) { sourceMap[String(s.id)] = s.name; });

  const txnMap = {};
  txns.forEach(function(t) { txnMap[String(t.id)] = t; });

  return items.filter(function(item) {
    if (!String(item.description || '').toLowerCase().includes(keyword)) return false;
    const txn = txnMap[String(item.transaction_id)];
    if (!txn) return false;
    if (source   && sourceMap[String(txn.source_id)] !== source)       return false;
    if (dateFrom && String(txn.expense_date) < dateFrom)               return false;
    if (dateTo   && String(txn.expense_date) > dateTo)                 return false;
    return true;
  }).map(function(item) {
    const txn = txnMap[String(item.transaction_id)];
    return Object.assign({}, item, {
      expense_date: txn ? txn.expense_date : '',
      source_name:  txn ? (sourceMap[String(txn.source_id)] || '-') : '-'
    });
  });
}

// ─── MENU IMAGE (lazy) ───────────────────────

function getMenuImage(params) {
  const rows = sheetData('menu_items').rows;
  const item = rows.find(function(r) { return String(r.id) === String(params.id); });
  if (!item) return { success: false };
  return { success: true, image_url: item.image_url || '' };
}

function getMenuImages(params) {
  const ids = (params.ids || []).map(String);
  if (ids.length === 0) return { success: true, data: {} };
  const rows = sheetData('menu_items').rows;
  const map = {};
  rows.filter(function(r) { return ids.indexOf(String(r.id)) >= 0 && r.image_url; })
      .forEach(function(r) { map[r.id] = r.image_url; });
  return { success: true, data: map };
}

// ─── MENU ITEMS ──────────────────────────────

function getMenuItems() {
  const cache  = CacheService.getScriptCache();
  const cached = cache.get('menu_items_v3');
  if (cached) return JSON.parse(cached);

  const menus    = sheetData('menu_items').rows;
  const cats     = sheetData('menu_categories').rows;
  const menuIngs = sheetData('menu_ingredients').rows;
  const ingrs    = sheetData('ingredients').rows;

  const catMap = {};
  cats.forEach(function(c) { catMap[String(c.id)] = c.name; });

  const ingrMap = {};
  ingrs.forEach(function(i) { ingrMap[String(i.id)] = i; });

  const ingrByMenu = {};
  menuIngs.forEach(function(mi) {
    const menuId = String(mi.menu_id);
    if (!ingrByMenu[menuId]) ingrByMenu[menuId] = [];
    const ingr = ingrMap[String(mi.ingredient_id)];
    ingrByMenu[menuId].push(Object.assign({}, mi, {
      ingredients: ingr ? { name: ingr.name } : { name: '' }
    }));
  });

  const result = menus
    .filter(function(m) {
      const v = m.is_active;
      return v !== false && v !== 'FALSE' && v !== 0 && v !== 'false';
    })
    .map(function(m) {
      return Object.assign({}, m, {
        id:               parseInt(m.id),
        price:            parseFloat(m.price) || 0,
        category_id:      parseInt(m.category_id) || null,
        menu_categories:  catMap[String(m.category_id)] ? { name: catMap[String(m.category_id)] } : null,
        menu_ingredients: ingrByMenu[String(m.id)] || [],
        image_url:        m.image_url || ''
      });
    });

  try {
    const json = JSON.stringify(result);
    if (json.length < 100000) {
      cache.put('menu_items_v3', json, 300);
      cache.put('menu_items_stale', json, 21600);
    }
  } catch(e) {}

  return result;
}

// ─── MENU CATEGORIES ─────────────────────────

function getMenuCategories() {
  const rows = sheetData('menu_categories').rows;
  return rows.sort(function(a,b) { return String(a.name).localeCompare(String(b.name), 'th'); });
}

function saveMenuCategory(name) {
  const rows = sheetData('menu_categories').rows;
  const existing = rows.find(function(r) { return r.name === name; });
  if (existing) return { success: true, id: parseInt(existing.id) };
  const result = dbInsert('menu_categories', { name: name });
  return { success: true, id: result.id };
}

// ─── SAVE MENU ITEM ──────────────────────────

function saveMenuItem(data) {
  const cats = sheetData('menu_categories').rows;
  var categoryId = null;
  if (data.category) {
    var cat = cats.find(function(c) { return c.name === data.category; });
    if (cat) categoryId = parseInt(cat.id);
  }

  CacheService.getScriptCache().remove('menu_items_v3');

  const menu = dbInsert('menu_items', {
    name:        data.name,
    price:       parseFloat(data.price) || 0,
    category_id: categoryId,
    image_url:   '',
    is_active:   true
  });

  const menuId = menu.id;

  // ถ้ามีรูปเป็น base64 → upload GitHub → อัพเดท image_url ด้วย CDN URL
  if (data.image_url && String(data.image_url).indexOf('data:image/') === 0) {
    var ghCfg = _getGithubConfig();
    if (ghCfg) {
      var cdnUrl = _uploadImageToGithub(ghCfg, String(menuId), data.image_url);
      if (cdnUrl) {
        dbUpdate('menu_items', menuId, { image_url: cdnUrl });
        CacheService.getScriptCache().remove('menu_items_v3');
      }
    }
  } else if (data.image_url) {
    dbUpdate('menu_items', menuId, { image_url: data.image_url });
  }

  (data.ingredients || []).forEach(function(ing) {
    if (!ing.name) return;
    const ingrs = sheetData('ingredients').rows;
    var ingr = ingrs.find(function(r) { return r.name === ing.name; });
    var ingrId;
    if (ingr) {
      ingrId = parseInt(ingr.id);
    } else {
      var newIngr = dbInsert('ingredients', { name: ing.name, unit: ing.unit || 'G' });
      ingrId = newIngr.id;
    }
    dbInsert('menu_ingredients', {
      menu_id:       menuId,
      ingredient_id: ingrId,
      quantity:      parseFloat(ing.quantity) || 0,
      unit:          ing.unit || 'G'
    });
  });

  return { success: true, id: menuId };
}

// ─── UPDATE MENU ITEM ────────────────────────

function updateMenuItem(params) {
  const id   = parseInt(params.id);
  const data = params.data;

  const cats = sheetData('menu_categories').rows;
  var catId = null;
  if (data.category) {
    var cat = cats.find(function(c) { return c.name === data.category; });
    if (cat) catId = parseInt(cat.id);
  }

  CacheService.getScriptCache().remove('menu_items_v3');

  // ถ้าเป็น base64 → upload GitHub ก่อนแล้วได้ CDN URL
  var resolvedImageUrl = data.image_url || '';
  if (resolvedImageUrl && String(resolvedImageUrl).indexOf('data:image/') === 0) {
    var ghCfg2 = _getGithubConfig();
    if (ghCfg2) {
      var cdn2 = _uploadImageToGithub(ghCfg2, String(id), resolvedImageUrl);
      resolvedImageUrl = cdn2 || '';
    } else {
      resolvedImageUrl = '';
    }
  }

  dbUpdate('menu_items', id, {
    name:        data.name,
    price:       parseFloat(data.price) || 0,
    category_id: catId,
    image_url:   resolvedImageUrl
  });

  dbDelete('menu_ingredients', function(r) { return parseInt(r.menu_id) === id; });

  (data.ingredients || []).forEach(function(ing) {
    if (!ing.name) return;
    const ingrs = sheetData('ingredients').rows;
    var ingr = ingrs.find(function(r) { return r.name === ing.name; });
    var ingrId;
    if (ingr) {
      ingrId = parseInt(ingr.id);
    } else {
      var newIngr = dbInsert('ingredients', { name: ing.name, unit: ing.unit || 'G' });
      ingrId = newIngr.id;
    }
    dbInsert('menu_ingredients', {
      menu_id:       id,
      ingredient_id: ingrId,
      quantity:      parseFloat(ing.quantity) || 0,
      unit:          ing.unit || 'G'
    });
  });

  return { success: true };
}

// ─── DELETE MENU ITEM ────────────────────────

function deleteMenuItem(params) {
  const id = parseInt(params.id);
  CacheService.getScriptCache().remove('menu_items_v3');
  dbDelete('menu_ingredients', function(r) { return parseInt(r.menu_id) === id; });
  dbDelete('menu_items',       function(r) { return parseInt(r.id)      === id; });
  return { success: true };
}

// ─── DELETE TRANSACTION ──────────────────────

function deleteTransaction(params) {
  const id   = parseInt(params.id);
  const type = params.type;

  if (type === 'expense') {
    dbDelete('expense_items',        function(r) { return parseInt(r.transaction_id) === id; });
    dbDelete('expense_transactions', function(r) { return parseInt(r.id)             === id; });
  } else {
    dbDelete('income_invoice_items', function(r) { return parseInt(r.transaction_id) === id; });
    dbDelete('income_transactions',  function(r) { return parseInt(r.id)             === id; });
  }
  return { success: true };
}

// ─── UPDATE INCOME ───────────────────────────

function updateIncome(params) {
  const id   = parseInt(params.id);
  const data = params.data;

  dbUpdate('income_transactions', id, {
    issue_date: data.date,
    total:      parseFloat(data.total) || 0
  });

  dbDelete('income_invoice_items', function(r) { return parseInt(r.transaction_id) === id; });
  (data.items || []).forEach(function(item) {
    dbInsert('income_invoice_items', {
      transaction_id: id,
      description:    item.description,
      quantity:       parseFloat(item.quantity)   || 1,
      unit_price:     parseFloat(item.unit_price) || 0
    });
  });

  return { success: true };
}

// ─── UPDATE EXPENSE ──────────────────────────

function updateExpense(params) {
  const id   = parseInt(params.id);
  const data = params.data;

  dbUpdate('expense_transactions', id, {
    expense_date: data.date,
    total:        parseFloat(data.total) || 0,
    note:         data.note || ''
  });

  dbDelete('expense_items', function(r) { return parseInt(r.transaction_id) === id; });
  (data.items || []).forEach(function(item) {
    dbInsert('expense_items', {
      transaction_id: id,
      description:    item.description,
      quantity:       parseFloat(item.quantity)   || 1,
      unit_price:     parseFloat(item.unit_price) || 0,
      unit:           item.unit || 'Pcs'
    });
  });

  return { success: true };
}

// ─── SALES REPORT ────────────────────────────

function getSalesReport(params) {
  const dateFrom = params.dateFrom;
  const dateTo   = params.dateTo;

  const txns  = sheetData('income_transactions').rows;
  const items = sheetData('income_invoice_items').rows;

  const filtered = txns.filter(function(t) {
    return String(t.issue_date) >= dateFrom && String(t.issue_date) <= dateTo;
  });

  if (filtered.length === 0) return { success: true, data: [] };

  const ids = {};
  filtered.forEach(function(t) { ids[String(t.id)] = true; });

  const result = items.filter(function(i) { return ids[String(i.transaction_id)]; });
  return { success: true, data: result };
}

// ─── INGREDIENT STOCK ────────────────────────

function getIngredientStock(params) {
  const dateFrom = params.dateFrom;
  const dateTo   = params.dateTo;

  const items = sheetData('expense_items').rows;
  const txns  = sheetData('expense_transactions').rows;

  const txnMap = {};
  txns.forEach(function(t) { txnMap[String(t.id)] = t; });

  const stockMap = {};
  items.forEach(function(r) {
    const txn  = txnMap[String(r.transaction_id)];
    const date = txn ? String(txn.expense_date) : null;
    if (!date || date < dateFrom || date > dateTo) return;
    const name = r.description;
    if (!stockMap[name]) stockMap[name] = { name: name, totalQty: 0, unit: r.unit || '', lastDate: date, purchases: [] };
    stockMap[name].totalQty += parseFloat(r.quantity) || 0;
    if (date > stockMap[name].lastDate) stockMap[name].lastDate = date;
    stockMap[name].purchases.push({ date: date, qty: parseFloat(r.quantity) || 0, unit: r.unit || '' });
  });

  return { success: true, data: Object.values(stockMap) };
}

// ─── ADMIN / PIN ─────────────────────────────

function getAdminByPin(params) {
  const pin  = String(params.pin);
  const rows = sheetData('master_admin').rows;
  const admin = rows.find(function(r) { return String(r.pin) === pin; });
  if (!admin) return { success: false, message: 'รหัสไม่ถูกต้อง' };
  return { success: true, data: { name: admin.name, role: admin.role } };
}

// ─── ORDER SESSIONS ──────────────────────────

function getOpenSessions() {
  const sessions = sheetData('order_sessions').rows;
  const items    = sheetData('order_items').rows;

  const open = sessions
    .filter(function(s) { return s.status === 'open'; })
    .sort(function(a,b) { return String(a.created_at).localeCompare(String(b.created_at)); });

  if (open.length === 0) return { success: true, data: [] };

  const openIds = {};
  open.forEach(function(s) { openIds[String(s.id)] = true; });

  const sessionItems = items.filter(function(i) { return openIds[String(i.session_id)]; });

  const result = open.map(function(s) {
    return Object.assign({}, s, {
      id: parseInt(s.id),
      items: sessionItems
        .filter(function(i) { return String(i.session_id) === String(s.id); })
        .sort(function(a,b) { return String(a.created_at).localeCompare(String(b.created_at)); })
        .map(function(i) { return Object.assign({}, i, { id: parseInt(i.id), session_id: parseInt(i.session_id) }); })
    });
  });

  return { success: true, data: result };
}

function createSession(data) {
  console.log('[createSession] ▶ เริ่ม | table_name:', data.table_name);
  const sessions = sheetData('order_sessions').rows;
  console.log('[createSession] order_sessions ทั้งหมด:', sessions.length, 'แถว');

  const existing = sessions.find(function(s) {
    return s.table_name === data.table_name && s.status === 'open';
  });
  if (existing) {
    console.log('[createSession] ⚠️ โต๊ะมีอยู่แล้ว | id:', existing.id, '| status:', existing.status, '— คืน existed:true');
    return { success: true, id: parseInt(existing.id), existed: true };
  }

  console.log('[createSession] ไม่มีโต๊ะนี้ — สร้างใหม่');
  const row = dbInsert('order_sessions', {
    table_name: data.table_name,
    status:     'open',
    opened_by:  data.opened_by || '',
    updated_at: new Date().toISOString()
  });
  console.log('[createSession] ✅ สร้างสำเร็จ | id:', row.id, '| table_name:', row.table_name);

  return { success: true, id: row.id };
}

function addOrderItem(data) {
  const row = dbInsert('order_items', {
    session_id:   parseInt(data.session_id),
    menu_item_id: data.menu_item_id || '',
    menu_name:    data.menu_name,
    price:        parseFloat(data.price) || 0,
    qty:          parseInt(data.qty)     || 1,
    note:         data.note || '',
    status:       'pending'
  });
  return { success: true, id: row.id };
}

function updateItemStatus(data) {
  dbUpdate('order_items', parseInt(data.id), { status: data.status });
  if (data.session_id) {
    dbUpdate('order_sessions', parseInt(data.session_id), {
      updated_at: new Date().toISOString()
    });
  }
  return { success: true };
}

function removeOrderItem(data) {
  dbDelete('order_items', function(r) { return parseInt(r.id) === parseInt(data.id); });
  return { success: true };
}

function closeSession(data) {
  const sessionId = parseInt(data.session_id);
  const sessions  = sheetData('order_sessions').rows;
  const session   = sessions.find(function(s) { return parseInt(s.id) === sessionId; });
  if (!session) return { success: false, message: 'ไม่พบโต๊ะ' };
  if (session.status === 'paid') return { success: false, message: 'บิลนี้ชำระแล้ว' };

  const allItems = sheetData('order_items').rows;
  const items    = allItems.filter(function(i) { return parseInt(i.session_id) === sessionId; });
  if (items.length === 0) return { success: false, message: 'ไม่มีรายการ' };

  const total = items.reduce(function(s, i) {
    return s + (parseFloat(i.price) || 0) * (parseInt(i.qty) || 0);
  }, 0);

  const now = new Date();
  const bkkDate = Utilities.formatDate(now, 'Asia/Bangkok', 'yyyy-MM-dd');
  const invoice_no = 'POS-' +
    Utilities.formatDate(now, 'Asia/Bangkok', 'yyyyMMdd-HHmmssSSS');

  const incomeResult = saveIncome({
    date:       bkkDate,
    invoice_no: invoice_no,
    customer:   session.table_name,
    total:      total,
    items:      items.map(function(i) {
      return { description: i.menu_name, quantity: parseInt(i.qty) || 1, unit_price: parseFloat(i.price) || 0 };
    })
  });

  if (!incomeResult || !incomeResult.success)
    return { success: false, message: 'บันทึก income ไม่สำเร็จ' };

  const updated = dbUpdate('order_sessions', sessionId, {
    status:     'paid',
    updated_at: now.toISOString()
  });
  if (!updated) return { success: false, message: 'ปิด session ไม่สำเร็จ (invoice: ' + invoice_no + ')' };

  return { success: true, invoice_no: invoice_no, total: total };
}

function deleteSession(data) {
  const sessionId = parseInt(data.session_id);
  const sessions  = sheetData('order_sessions').rows;
  const session   = sessions.find(function(s) { return parseInt(s.id) === sessionId; });
  if (session && session.status === 'paid') {
    return { success: false, message: 'ไม่สามารถลบบิลที่ชำระแล้วได้' };
  }
  dbDelete('order_items',    function(r) { return parseInt(r.session_id) === sessionId; });
  dbDelete('order_sessions', function(r) { return parseInt(r.id)         === sessionId; });
  return { success: true };
}

// ─── TOP MENU TODAY ──────────────────────────

function getTopMenuToday() {
  const today    = Utilities.formatDate(new Date(), 'Asia/Bangkok', 'yyyy-MM-dd');
  const sessions = sheetData('order_sessions').rows;
  const items    = sheetData('order_items').rows;

  const paidToday = sessions.filter(function(s) {
    return s.status === 'paid' && String(s.created_at).substring(0, 10) === today;
  });

  if (paidToday.length === 0) return { success: true, data: [] };

  const sessionIds = {};
  paidToday.forEach(function(s) { sessionIds[String(s.id)] = true; });

  const todayItems = items.filter(function(i) { return sessionIds[String(i.session_id)]; });

  const menuMap = {};
  todayItems.forEach(function(item) {
    const name = item.menu_name || 'ไม่ระบุ';
    if (!menuMap[name]) menuMap[name] = { name: name, count: 0, revenue: 0 };
    const qty = parseInt(item.qty) || 1;
    menuMap[name].count   += qty;
    menuMap[name].revenue += (parseFloat(item.price) || 0) * qty;
  });

  return {
    success: true,
    data: Object.values(menuMap)
      .sort(function(a,b) { return b.count - a.count; })
      .slice(0, 5)
  };
}

// ─── SETUP SHEETS ────────────────────────────
// เรียกครั้งเดียวเพื่อสร้าง sheets + headers ทั้งหมด

function setupSheets() {
  const db = getDb();
  const schemas = {
    'expense_sources':      ['id','name'],
    'expense_transactions': ['id','source_id','expense_date','total','note','created_at'],
    'expense_items':        ['id','transaction_id','description','quantity','unit_price','unit'],
    'customers':            ['id','name'],
    'income_transactions':  ['id','invoice_no','customer_id','issue_date','total','status','created_at'],
    'income_invoice_items': ['id','transaction_id','description','quantity','unit_price'],
    'menu_categories':      ['id','name'],
    'menu_items':           ['id','name','price','category_id','image_url','is_active'],
    'ingredients':          ['id','name','unit'],
    'menu_ingredients':     ['id','menu_id','ingredient_id','quantity','unit'],
    'master_admin':         ['id','name','role','pin'],
    'order_sessions':       ['id','table_name','status','opened_by','created_at','updated_at'],
    'order_items':          ['id','session_id','menu_item_id','menu_name','price','qty','note','status','created_at']
  };

  Object.keys(schemas).forEach(function(name) {
    const headers = schemas[name];
    var sheet = db.getSheetByName(name);
    if (!sheet) {
      sheet = db.insertSheet(name);
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
      sheet.setFrozenRows(1);
      sheet.getRange(1, 1, 1, headers.length)
           .setBackground('#1D9E75').setFontColor('#ffffff').setFontWeight('bold');
    }
  });

  // Seed expense_sources
  if (sheetData('expense_sources').rows.length === 0) {
    ['ตลาด','ห้าง','Online','Shopee'].forEach(function(name) {
      dbInsert('expense_sources', { name: name });
    });
  }

  Logger.log('setupSheets เสร็จแล้ว ✓');
}

// ─── MIGRATE FROM SUPABASE → SHEETS ──────────
// เรียกครั้งเดียวหลัง setupSheets() เพื่อ migrate ข้อมูลเดิม

function migrateFromSupabase() {
  const config = _getSupabaseConfig();
  if (!config) { Logger.log('ไม่พบ Supabase config'); return; }
  const ghConfig = _getGithubConfig();

  function sbGet(table) {
    var all = [];
    var limit = 100;
    var offset = 0;
    while (true) {
      var url = config.url + '/rest/v1/' + table + '?order=id.asc&limit=' + limit + '&offset=' + offset;
      try {
        var res = UrlFetchApp.fetch(url, {
          method: 'GET',
          headers: {
            'apikey': config.key,
            'Authorization': 'Bearer ' + config.key,
            'Prefer': 'count=none'
          },
          muteHttpExceptions: true
        });
        var code = res.getResponseCode();
        var text = res.getContentText();
        if (code >= 400) {
          Logger.log(table + ' offset=' + offset + ' → HTTP ' + code + ': ' + text.substring(0, 200));
          break;
        }
        var parsed = JSON.parse(text);
        if (!Array.isArray(parsed) || parsed.length === 0) break;
        all = all.concat(parsed);
        if (parsed.length < limit) break;
        offset += limit;
      } catch(e) {
        Logger.log(table + ' → ERROR: ' + e.toString());
        break;
      }
    }
    return all;
  }

  function sbGetRaw(endpoint) {
    var url = config.url + '/rest/v1/' + endpoint;
    try {
      var res = UrlFetchApp.fetch(url, {
        method: 'GET',
        headers: { 'apikey': config.key, 'Authorization': 'Bearer ' + config.key, 'Prefer': 'count=none' },
        muteHttpExceptions: true
      });
      if (res.getResponseCode() >= 400) return [];
      var parsed = JSON.parse(res.getContentText());
      return Array.isArray(parsed) ? parsed : [];
    } catch(e) { return []; }
  }

  const tables = [
    'expense_sources', 'customers', 'expense_transactions', 'expense_items',
    'income_transactions', 'income_invoice_items', 'menu_categories', 'menu_items',
    'ingredients', 'menu_ingredients', 'master_admin', 'order_sessions', 'order_items'
  ];

  tables.forEach(function(t) {
    var rows;

    if (t === 'menu_items') {
      // ดึง metadata ก่อน (ไม่มี image_url เพื่อหลีกเลี่ยง timeout)
      rows = [];
      var metaOffset = 0;
      while (true) {
        var batch = sbGetRaw('menu_items?select=id,name,price,category_id,is_active&order=id.asc&limit=100&offset=' + metaOffset);
        if (!batch || batch.length === 0) break;
        rows = rows.concat(batch);
        if (batch.length < 100) break;
        metaOffset += 100;
      }
      if (rows.length === 0) { Logger.log('menu_items: ไม่มีข้อมูล'); return; }

      // ดึงรูปทีละ 5 rows แล้ว upload GitHub
      var imageMap = {};
      if (ghConfig) {
        var imgOffset = 0;
        while (true) {
          var imgBatch = sbGetRaw('menu_items?select=id,image_url&order=id.asc&limit=5&offset=' + imgOffset);
          if (!imgBatch || imgBatch.length === 0) break;
          imgBatch.forEach(function(r) {
            if (r.image_url && String(r.image_url).indexOf('data:image/') === 0) {
              var cdnUrl = _uploadImageToGithub(ghConfig, String(r.id), r.image_url);
              if (cdnUrl) imageMap[String(r.id)] = cdnUrl;
            }
          });
          Logger.log('menu_items images: offset=' + imgOffset + ' done');
          if (imgBatch.length < 5) break;
          imgOffset += 5;
        }
      }
      rows = rows.map(function(r) {
        return Object.assign({}, r, { image_url: imageMap[String(r.id)] || '' });
      });

    } else {
      rows = sbGet(t);
      if (rows.length === 0) { Logger.log(t + ': ไม่มีข้อมูล'); return; }
    }

    const sheet = getSheet(t);
    if (!sheet) { Logger.log(t + ': ไม่พบ sheet'); return; }
    const headers = sheet.getRange(1,1,1,sheet.getLastColumn()).getValues()[0].map(String);
    const values = rows.map(function(row) {
      return headers.map(function(h) {
        var v = (row[h] !== undefined && row[h] !== null) ? row[h] : '';
        if (typeof v === 'string' && v.length > 49000) v = '';
        return v;
      });
    });
    var lastRow = sheet.getLastRow();
    if (lastRow > 1) {
      sheet.getRange(2, 1, lastRow - 1, headers.length).clearContent();
    }
    sheet.getRange(2, 1, values.length, headers.length).setValues(values);
    Logger.log(t + ': migrate ' + rows.length + ' rows ✓');
  });

  Logger.log('migrateFromSupabase เสร็จแล้ว ✓');
}

function _getSupabaseConfig() {
  const sheet = getDb().getSheetByName('Config');
  if (!sheet) return null;
  const data = sheet.getDataRange().getValues();
  const config = {};
  data.forEach(function(row) { if (row[0] && row[0] !== 'KEY') config[row[0]] = row[1]; });
  if (!config['SUPABASE_URL'] || !config['SUPABASE_ANON_KEY']) return null;
  return { url: config['SUPABASE_URL'], key: config['SUPABASE_ANON_KEY'] };
}

function _getGithubConfig() {
  const sheet = getDb().getSheetByName('Config');
  if (!sheet) return null;
  const data = sheet.getDataRange().getValues();
  const config = {};
  data.forEach(function(row) { if (row[0] && row[0] !== 'KEY') config[row[0]] = row[1]; });
  if (!config['GITHUB_TOKEN'] || !config['GITHUB_REPO']) return null;
  return { token: String(config['GITHUB_TOKEN']), repo: String(config['GITHUB_REPO']) };
}

function _uploadImageToGithub(ghConfig, filename, base64Data) {
  var matches = String(base64Data).match(/^data:([^;]+);base64,(.+)$/);
  if (!matches) return null;
  var ext = matches[1].split('/')[1] || 'jpg';
  if (ext === 'jpeg') ext = 'jpg';
  var b64content = matches[2];
  var path = 'menu/' + filename + '.' + ext;
  var url = 'https://api.github.com/repos/' + ghConfig.repo + '/contents/' + path;
  try {
    var res = UrlFetchApp.fetch(url, {
      method: 'PUT',
      headers: {
        'Authorization': 'token ' + ghConfig.token,
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'WalletRecord-GAS'
      },
      payload: JSON.stringify({ message: 'Add menu image ' + filename, content: b64content }),
      muteHttpExceptions: true
    });
    var code = res.getResponseCode();
    if (code === 201 || code === 200) {
      Logger.log('uploaded image: ' + filename);
      return 'https://cdn.jsdelivr.net/gh/' + ghConfig.repo + '@main/' + path;
    }
    if (code === 422) {
      return 'https://cdn.jsdelivr.net/gh/' + ghConfig.repo + '@main/' + path;
    }
    Logger.log('GitHub upload ' + filename + ' → HTTP ' + code + ': ' + res.getContentText().substring(0, 150));
    return null;
  } catch(e) {
    Logger.log('GitHub upload error ' + filename + ': ' + e.toString());
    return null;
  }
}

// ─── SYNC MENU IMAGES FROM SUPABASE → GITHUB ─────────────────────────────────
// เรียกจาก app หรือ Script Editor เพื่อ migrate รูปทั้งหมดจาก Supabase → GitHub CDN
function syncMenuImages() {
  const sbConfig = _getSupabaseConfig();
  const ghConfig = _getGithubConfig();
  if (!sbConfig) return { success: false, message: 'ไม่มี Supabase config ใน Config sheet' };
  if (!ghConfig) return { success: false, message: 'ไม่มี GitHub config ใน Config sheet' };

  // ดึง menu_items ทั้งหมดจาก Supabase (id + image_url)
  var sbItems = [];
  var offset = 0;
  while (true) {
    var url = sbConfig.url + '/rest/v1/menu_items?select=id,image_url&order=id.asc&limit=50&offset=' + offset;
    try {
      var res = UrlFetchApp.fetch(url, {
        method: 'GET',
        headers: { 'apikey': sbConfig.key, 'Authorization': 'Bearer ' + sbConfig.key, 'Prefer': 'count=none' },
        muteHttpExceptions: true
      });
      if (res.getResponseCode() >= 400) break;
      var batch = JSON.parse(res.getContentText());
      if (!Array.isArray(batch) || batch.length === 0) break;
      sbItems = sbItems.concat(batch);
      if (batch.length < 50) break;
      offset += 50;
    } catch(e) { break; }
  }

  // สร้าง map ของ image_url ที่มีอยู่ใน Google Sheets (id → image_url)
  var sheetsItems = sheetData('menu_items').rows;
  var sheetsImageMap = {};
  sheetsItems.forEach(function(r) { sheetsImageMap[String(r.id)] = String(r.image_url || ''); });

  var updated = 0, skipped = 0, failed = 0;
  var log = [];

  sbItems.forEach(function(item) {
    var imgUrl = String(item.image_url || '');
    if (!imgUrl) { skipped++; return; }
    // ถ้า Google Sheets มี CDN URL แล้ว → ข้ามทันที ไม่ต้อง upload ซ้ำ
    var existingUrl = sheetsImageMap[String(item.id)] || '';
    if (existingUrl.indexOf('cdn.jsdelivr.net') >= 0) { skipped++; return; }
    // ถ้า Supabase เองเป็น CDN URL แล้ว → ข้าม
    if (imgUrl.indexOf('cdn.jsdelivr.net') >= 0) { skipped++; return; }

    var cdnUrl = null;

    if (imgUrl.indexOf('data:image/') === 0) {
      // base64 — upload ตรง
      cdnUrl = _uploadImageToGithub(ghConfig, String(item.id), imgUrl);
    } else if (imgUrl.indexOf('http') === 0) {
      // URL — ดาวน์โหลดก่อนแล้ว upload
      try {
        var imgRes = UrlFetchApp.fetch(imgUrl, { muteHttpExceptions: true });
        if (imgRes.getResponseCode() === 200) {
          var ct = (imgRes.getHeaders()['Content-Type'] || imgRes.getHeaders()['content-type'] || 'image/jpeg').split(';')[0];
          var b64 = Utilities.base64Encode(imgRes.getContent());
          cdnUrl = _uploadImageToGithub(ghConfig, String(item.id), 'data:' + ct + ';base64,' + b64);
        }
      } catch(e) {
        Logger.log('download err id=' + item.id + ': ' + e);
      }
    }

    if (cdnUrl) {
      dbUpdate('menu_items', parseInt(item.id), { image_url: cdnUrl });
      Logger.log('✅ id=' + item.id + ' → ' + cdnUrl);
      log.push('✅ id=' + item.id);
      updated++;
    } else {
      Logger.log('❌ id=' + item.id + ' → failed');
      log.push('❌ id=' + item.id);
      failed++;
    }
  });

  CacheService.getScriptCache().remove('menu_items_v3');
  Logger.log('syncMenuImages done: updated=' + updated + ' skipped=' + skipped + ' failed=' + failed);
  return { success: true, updated: updated, skipped: skipped, failed: failed, log: log };
}
