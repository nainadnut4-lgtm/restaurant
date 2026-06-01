// ============================================
// FILE: WebApp.gs — Router
// ============================================

// FILE: WebApp.gs
function doGet(e) {
  const template = HtmlService.createTemplateFromFile('index');
  return template.evaluate()
    .setTitle('WalletRecord')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0');
}
function doPost(e) {
  const params = JSON.parse(e.postData.contents);
  const action = params.action;
  let result = {};

  try {
    if (action === 'saveExpense')    result = saveExpense(params.data);
    else if (action === 'saveIncome') result = saveIncome(params.data);
    else if (action === 'getHistory') result = { success: true, data: getHistory() };
    else if (action === 'getSummary') result = { success: true, data: getSummary() };
    else if (action === 'getExpenseDescriptions') result = { success: true, data: getExpenseDescriptions() };
    else if (action === 'getTransactionItems')
    result = { success: true, data: getTransactionItems(params.data) };
    else if (action === 'searchItems')
    result = { success: true, data: searchItems(params.data) };
    else if (action === 'getMenuItems')
      result = { success: true, data: getMenuItems() };
    else if (action === 'saveMenuItem')
      result = saveMenuItem(params.data);
    else if (action === 'getMenuCategories')
      result = { success: true, data: getMenuCategories() };
    else if (action === 'saveMenuCategory')
      result = saveMenuCategory(params.data.name);
    else if (action === 'deleteTransaction')
      result = deleteTransaction(params.data);
    else if (action === 'updateExpense')
      result = updateExpense(params.data);
    else if (action === 'getSalesReport')
      result = getSalesReport(params.data);
    else if (action === 'getIngredientStock')
      result = getIngredientStock(params.data);
    else if (action === 'deleteMenuItem')
      result = deleteMenuItem(params.data);
    else if (action === 'updateMenuItem')
      result = updateMenuItem(params.data);
    else if (action === 'getAdminByPin')
      result = getAdminByPin(params.data);
    else if (action === 'getMenuImage')
      result = getMenuImage(params.data);
    else if (action === 'getMenuImages')
      result = getMenuImages(params.data);
    else if (action === 'getOpenSessions')
      result = getOpenSessions();
    else if (action === 'createSession')
      result = createSession(params.data);
    else if (action === 'addOrderItem')
      result = addOrderItem(params.data);
    else if (action === 'updateItemStatus')
      result = updateItemStatus(params.data);
    else if (action === 'removeOrderItem')
      result = removeOrderItem(params.data);
    else if (action === 'closeSession')
      result = closeSession(params.data);
    else if (action === 'deleteSession')
      result = deleteSession(params.data);
    else if (action === 'syncMenuImages')
      result = syncMenuImages();
    else result = { success: false, message: 'unknown action' };
  } catch(err) {
    result = { success: false, message: err.toString() };
  }

  return ContentService.createTextOutput(JSON.stringify(result))
                       .setMimeType(ContentService.MimeType.JSON);

}
