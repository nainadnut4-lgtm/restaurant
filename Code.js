// ============================================
// FILE: Code.gs
// ============================================

// ดึง config จาก Sheet
function getConfig() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet()
                              .getSheetByName('Config');
  const data = sheet.getDataRange().getValues();
  const config = {};
  data.forEach(row => {
    if (row[0] && row[0] !== 'KEY') config[row[0]] = row[1];
  });
  return config;
}

// Supabase REST API caller
function supabaseRequest(endpoint, method, payload) {
  const config = getConfig();
  const url = config['SUPABASE_URL'] + '/rest/v1/' + endpoint;

  const options = {
    method: method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      'apikey': config['SUPABASE_ANON_KEY'],
      'Authorization': 'Bearer ' + config['SUPABASE_ANON_KEY'],
      'Prefer': 'return=representation'
    },
    muteHttpExceptions: true
  };

  if (payload) options.payload = JSON.stringify(payload);

  const response = UrlFetchApp.fetch(url, options);
  const code = response.getResponseCode();
  const body = response.getContentText();

  if (code >= 400) {
    Logger.log('❌ Error ' + code + ': ' + body);
    return null;
  }

  return JSON.parse(body);
}

// ทดสอบ connection
function testConnection() {
  const result = supabaseRequest('categories?limit=1', 'GET');
  if (result !== null) {
    Logger.log('✅ เชื่อมต่อ Supabase สำเร็จ');
    Logger.log(JSON.stringify(result));
  } else {
    Logger.log('❌ เชื่อมต่อไม่ได้ ตรวจสอบ Config อีกครั้ง');
  }
}

// ============================================
// บันทึกรายจ่ายจาก Sheet → Supabase
// ============================================

function syncExpenses() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('รายจ่าย');
  const lastRow = sheet.getLastRow();
  
  if (lastRow < 2) {
    Logger.log('ไม่มีข้อมูล');
    return;
  }

  const data = sheet.getRange(2, 1, lastRow - 1, 7).getValues();
  let successCount = 0;
  let errorCount = 0;

  // ดึง expense_sources จาก Supabase
  const sources = supabaseRequest('expense_sources', 'GET');
  const sourceMap = {};
  if (sources) {
    sources.forEach(s => sourceMap[s.name] = s.id);
  }

  data.forEach((row, i) => {
    const rowNum = i + 2;

    // ข้ามแถวว่างหรือที่ sync แล้ว
    if (!row[0] || !row[3]) return;
    
    // เช็ค column H (status sync)
    const statusCell = sheet.getRange(rowNum, 8).getValue();
    if (statusCell === '✅') return;

    const expenseDate = row[0] instanceof Date 
      ? Utilities.formatDate(row[0], 'Asia/Bangkok', 'yyyy-MM-dd')
      : row[0];

    const sourceName = row[1] || 'ตลาด';
    const sourceId = sourceMap[sourceName] || 1;

    // 1. บันทึก expense_transactions
    const transaction = supabaseRequest('expense_transactions', 'POST', {
      source_id: sourceId,
      expense_date: expenseDate,
      total: parseFloat(row[5]) || 0,
      note: row[6] || ''
    });

    if (!transaction || transaction.length === 0) {
      sheet.getRange(rowNum, 8).setValue('❌');
      errorCount++;
      return;
    }

    const transactionId = transaction[0].id;

    // 2. บันทึก expense_items
    const item = supabaseRequest('expense_items', 'POST', {
      transaction_id: transactionId,
      description: row[3],
      quantity: parseFloat(row[4]) || 1,
      unit_price: parseFloat(row[5]) || 0
    });

    if (item) {
      sheet.getRange(rowNum, 8).setValue('✅');
      successCount++;
    } else {
      sheet.getRange(rowNum, 8).setValue('❌');
      errorCount++;
    }
  });

  SpreadsheetApp.getActiveSpreadsheet().toast(
    `✅ สำเร็จ ${successCount} รายการ | ❌ ผิดพลาด ${errorCount} รายการ`,
    'Sync รายจ่าย', 5
  );
}


// ============================================
// บันทึกรายรับจาก Sheet → Supabase
// ============================================

function syncIncome() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('รายรับ');
  const lastRow = sheet.getLastRow();

  if (lastRow < 2) {
    Logger.log('ไม่มีข้อมูล');
    return;
  }

  const data = sheet.getRange(2, 1, lastRow - 1, 6).getValues();
  let successCount = 0;
  let errorCount = 0;

  data.forEach((row, i) => {
    const rowNum = i + 2;

    // ข้ามแถวว่างหรือ sync แล้ว
    if (!row[0] || !row[1]) return;
    const statusCell = sheet.getRange(rowNum, 7).getValue();
    if (statusCell === '✅') return;

    const issueDate = row[0] instanceof Date
      ? Utilities.formatDate(row[0], 'Asia/Bangkok', 'yyyy-MM-dd')
      : row[0];

    const invoiceNo = row[1].toString();
    const customerName = row[2] || 'ลูกค้าทั่วไป';
    const description = row[3] || '';
    const quantity = parseFloat(row[4]) || 1;
    const unitPrice = parseFloat(row[5]) || 0;
    const total = quantity * unitPrice;

    // 1. หรือสร้าง customer
    let customerId = null;
    const existingCustomer = supabaseRequest(
      'customers?name=eq.' + encodeURIComponent(customerName) + '&limit=1',
      'GET'
    );

    if (existingCustomer && existingCustomer.length > 0) {
      customerId = existingCustomer[0].id;
    } else {
      const newCustomer = supabaseRequest('customers', 'POST', {
        name: customerName
      });
      if (newCustomer && newCustomer.length > 0) {
        customerId = newCustomer[0].id;
      }
    }

    // 2. บันทึก income_transactions
    const transaction = supabaseRequest('income_transactions', 'POST', {
      invoice_no: invoiceNo,
      customer_id: customerId,
      issue_date: issueDate,
      total: total,
      status: 'paid'
    });

    if (!transaction || transaction.length === 0) {
      sheet.getRange(rowNum, 7).setValue('❌');
      errorCount++;
      return;
    }

    const transactionId = transaction[0].id;

    // 3. บันทึก income_invoice_items
    const item = supabaseRequest('income_invoice_items', 'POST', {
      transaction_id: transactionId,
      description: description,
      quantity: quantity,
      unit_price: unitPrice
    });

    if (item) {
      sheet.getRange(rowNum, 7).setValue('✅');
      successCount++;
    } else {
      sheet.getRange(rowNum, 7).setValue('❌');
      errorCount++;
    }
  });

  SpreadsheetApp.getActiveSpreadsheet().toast(
    `✅ สำเร็จ ${successCount} รายการ | ❌ ผิดพลาด ${errorCount} รายการ`,
    'Sync รายรับ', 5
  );
}