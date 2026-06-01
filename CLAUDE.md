# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**WalletRecord** คือระบบ POS + บัญชีร้านอาหาร สร้างด้วย Google Apps Script (GAS) ใช้ Google Sheets เป็นฐานข้อมูลหลัก

## Deploy Commands

```bash
# Push โค้ดขึ้น Google Apps Script
export PATH="$HOME/.npm-global/bin:$PATH"
clasp push

# Deploy (อัปเดต deployment เดิม — URL ไม่เปลี่ยน)
clasp deploy --deploymentId "AKfycbzoq2MF_L95c-rBv4NLjJRgcCavclL1BradjNwwB45YtudC4XRDuCQ49XFOJwecEtE" --description "Fix: ..."

# เปิด Web App
open "https://script.google.com/macros/s/AKfycbzoq2MF_L95c-rBv4NLjJRgcCavclL1BradjNwwB45YtudC4XRDuCQ49XFOJwecEtE/exec"
```

> clasp ติดตั้งไว้ที่ `~/.npm-global/bin/` ต้อง export PATH ทุกครั้ง

## Architecture

### Data Flow

```
Browser (app.html)
  → google.script.run.<functionName>(data)
    → WebApp.js doPost() — routes by action field
      → Api.js — business logic + Google Sheets CRUD
        → Google Sheets (Spreadsheet ID: 1NHiW47zPBM7CDZTFE6QIfeOT2ahzt2uo3ZmebXHI-6s)
```

Frontend ใช้ `google.script.run` เท่านั้น — ไม่มี REST API, ไม่มี fetch

### Files

| ไฟล์ | หน้าที่ |
|------|---------|
| `WebApp.js` | `doGet` serve หน้า, `doPost` รับ action แล้ว route ไปฟังก์ชันใน Api.js |
| `Api.js` | Business logic ทั้งหมด + CRUD helper (`dbInsert`, `dbUpdate`, `dbDelete`, `sheetData`) |
| `Code.js` | Legacy utilities: Supabase REST caller + `syncExpenses` / `syncIncome` จาก Sheets → Supabase |
| `app.html` | Frontend POS ทั้งหมดในไฟล์เดียว (menu, order, expense, history) |
| `style.html` | Shared CSS — include ใน app.html |
| `index.html` | Redirect page ไปยัง Web App URL |
| `appsscript.json` | GAS manifest — timezone: Asia/Bangkok, access: ANYONE_ANONYMOUS |

### Database (Google Sheets)

Sheets หลักที่ใช้:

- **order_sessions** — โต๊ะที่เปิด (status: `open` / `paid`)
- **order_items** — รายการอาหารในแต่ละ session
- **menu_items** — เมนูทั้งหมด (155+ รายการ)
- **menu_categories** — หมวดหมู่เมนู
- **expense_transactions** + **expense_items** — รายจ่าย
- **income_transactions** + **income_invoice_items** — รายรับ (สร้างอัตโนมัติเมื่อ closeSession)
- **master_admin** — ผู้ใช้งาน (login ด้วย PIN)
- **Config** — เก็บ SUPABASE_URL, SUPABASE_ANON_KEY (ใช้สำหรับ syncMenuImages)

### Core DB Helpers (Api.js)

```js
sheetData(sheetName)          // อ่านทั้ง sheet → { headers, rows[] }
dbInsert(sheetName, obj)      // เพิ่มแถว, auto-assign id, flush
dbUpdate(sheetName, id, obj)  // แก้ไขแถว by id, flush
dbDelete(sheetName, filterFn) // ลบแถวตาม filter, flush (ลบจากล่างขึ้นบน)
```

> ทุก write ต้องมี `SpreadsheetApp.flush()` — ถ้าไม่มีจะเกิด read-after-write miss

### POS Flow

1. Login ด้วย PIN → `getAdminByPin()`
2. เปิดโต๊ะ → `createSession()` (ตรวจ duplicate table_name+open)
3. เพิ่มออเดอร์ → `addOrderItem()`
4. ปิดบิล → `closeSession()` → auto สร้าง `income_transaction` + เปลี่ยน status เป็น `paid`
5. ยกเลิกโต๊ะ → `deleteSession()` (ลบ session + items, ห้ามลบถ้า paid)

## Known Constraints

- **table_name** ใน order_sessions อาจเป็น number ได้ (legacy data) — ต้องใช้ `String(s.table_name ?? '')` ก่อน `.replace()`
- **ชื่อโต๊ะตัวเลขล้วน** ถูกป้องกันใน `posConfirmOpenTable()` ด้วย `/^\d+$/`
- Supabase ใน Code.js เป็น legacy — ปัจจุบัน **ข้อมูลทั้งหมดอยู่ใน Google Sheets** ไม่ใช่ Supabase
- GAS execution timeout 6 นาที — หลีกเลี่ยง loop ขนาดใหญ่
