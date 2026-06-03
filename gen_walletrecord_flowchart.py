# -*- coding: utf-8 -*-
"""
สร้าง Flowchart (PDF) อธิบายการทำงานของโปรเจค WalletRecord
- ใช้สัญลักษณ์ผังงาน (flowchart) มาตรฐาน ANSI/ISO ให้ถูกต้อง
- ภาษาไทย อ่านง่ายสำหรับคนนอก
ผลลัพธ์: /Users/admin/Developer/WalletRecord_Flowchart.pdf
"""
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color

# ─── ฟอนต์ไทย ──────────────────────────────────────────────
pdfmetrics.registerFont(TTFont('Thai',  '/System/Library/Fonts/Supplemental/Thonburi.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('ThaiB', '/System/Library/Fonts/Supplemental/Thonburi.ttc', subfontIndex=1))
F  = 'Thai'
FB = 'ThaiB'

# ─── สี ────────────────────────────────────────────────────
COL = {
    'start'    : '#2E7D32',  # เขียว   - เริ่ม/จบ (terminator)
    'process'  : '#1565C0',  # น้ำเงิน - ขั้นตอนทำงาน (process)
    'decision' : '#EF6C00',  # ส้ม     - ตัดสินใจ (decision)
    'db'       : '#6A1B9A',  # ม่วง    - ฐานข้อมูล (database)
    'io'       : '#00838F',  # ฟ้าเขียว- รับ/ส่งข้อมูล (input/output)
    'sub'      : '#283593',  # คราม    - ฟังก์ชันสำเร็จรูป (predefined process)
    'manual'   : '#6D4C41',  # น้ำตาล  - กรอกข้อมูลด้วยมือ (manual input)
    'doc'      : '#AD1457',  # ชมพูเข้ม- เอกสาร/ใบเสร็จ (document)
    'conn'     : '#455A64',  # เทา     - จุดเชื่อมต่อ (connector)
}
OUTLINE = HexColor('#1A2327')
INK     = HexColor('#22303A')
WHITE   = HexColor('#FFFFFF')
LIGHT   = HexColor('#ECEFF1')
PAGEBG  = HexColor('#F7F9FB')
HEADBG  = HexColor('#11212B')

# ─── primitive วาดข้อความหลายบรรทัด ─────────────────────────
def text_block(c, cx, cy, text, size=10.5, color=WHITE, font=FB, leading=None):
    lines = text.split('\n')
    leading = leading or size * 1.28
    c.setFont(font, size)
    c.setFillColor(color)
    start = cy + (len(lines) - 1) * leading / 2 - size * 0.36
    for i, ln in enumerate(lines):
        c.drawCentredString(cx, start - i * leading, ln)

def _begin(c, fill):
    c.setStrokeColor(OUTLINE)
    c.setLineWidth(1.2)
    c.setFillColor(HexColor(fill))

# ─── สัญลักษณ์ผังงาน ───────────────────────────────────────
def sym_terminator(c, cx, cy, w, h, fill):           # เริ่ม/จบ : stadium
    _begin(c, fill)
    c.roundRect(cx - w/2, cy - h/2, w, h, h/2, fill=1, stroke=1)

def sym_process(c, cx, cy, w, h, fill):              # ขั้นตอน : rectangle
    _begin(c, fill)
    c.rect(cx - w/2, cy - h/2, w, h, fill=1, stroke=1)

def sym_decision(c, cx, cy, w, h, fill):             # ตัดสินใจ : diamond
    _begin(c, fill)
    p = c.beginPath()
    p.moveTo(cx, cy + h/2); p.lineTo(cx + w/2, cy)
    p.lineTo(cx, cy - h/2); p.lineTo(cx - w/2, cy); p.close()
    c.drawPath(p, fill=1, stroke=1)

def sym_io(c, cx, cy, w, h, fill):                   # รับ/ส่งข้อมูล : parallelogram
    _begin(c, fill)
    off = h * 0.5
    p = c.beginPath()
    p.moveTo(cx - w/2 + off, cy + h/2); p.lineTo(cx + w/2, cy + h/2)
    p.lineTo(cx + w/2 - off, cy - h/2); p.lineTo(cx - w/2, cy - h/2); p.close()
    c.drawPath(p, fill=1, stroke=1)

def sym_db(c, cx, cy, w, h, fill):                   # ฐานข้อมูล : cylinder
    ry = h * 0.13
    x1, x2 = cx - w/2, cx + w/2
    yb, yt = cy - h/2, cy + h/2
    _begin(c, fill)
    c.ellipse(x1, yb, x2, yb + 2*ry, fill=1, stroke=1)          # ฐานล่าง
    c.setStrokeColor(HexColor(fill))
    c.rect(x1, yb + ry, w, (yt - ry) - (yb + ry), fill=1, stroke=0)
    c.setStrokeColor(OUTLINE)
    c.line(x1, yb + ry, x1, yt - ry)
    c.line(x2, yb + ry, x2, yt - ry)
    c.ellipse(x1, yt - 2*ry, x2, yt, fill=1, stroke=1)          # ฝาบน

def sym_sub(c, cx, cy, w, h, fill):                  # ฟังก์ชันสำเร็จรูป : predefined process
    _begin(c, fill)
    c.rect(cx - w/2, cy - h/2, w, h, fill=1, stroke=1)
    inset = min(11, w * 0.07)
    c.setStrokeColor(WHITE); c.setLineWidth(1.0)
    c.line(cx - w/2 + inset, cy - h/2, cx - w/2 + inset, cy + h/2)
    c.line(cx + w/2 - inset, cy - h/2, cx + w/2 - inset, cy + h/2)

def sym_manual(c, cx, cy, w, h, fill):               # กรอกข้อมูลด้วยมือ : manual input
    _begin(c, fill)
    slope = h * 0.4
    p = c.beginPath()
    p.moveTo(cx - w/2, cy - h/2); p.lineTo(cx + w/2, cy - h/2)
    p.lineTo(cx + w/2, cy + h/2); p.lineTo(cx - w/2, cy + h/2 - slope); p.close()
    c.drawPath(p, fill=1, stroke=1)

def sym_doc(c, cx, cy, w, h, fill):                  # เอกสาร/ใบเสร็จ : document
    _begin(c, fill)
    x1, x2 = cx - w/2, cx + w/2
    yb, yt = cy - h/2, cy + h/2
    wv = h * 0.14
    p = c.beginPath()
    p.moveTo(x1, yb + wv)
    p.lineTo(x1, yt); p.lineTo(x2, yt); p.lineTo(x2, yb + wv)
    p.curveTo(x2 - w*0.25, yb - wv, cx + w*0.05, yb + 2*wv, cx, yb + wv)
    p.curveTo(x1 + w*0.25, yb,       x1 + w*0.20, yb + 2*wv, x1, yb + wv)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

def sym_connector(c, cx, cy, r, fill, label=''):     # จุดเชื่อมต่อ : connector
    _begin(c, fill)
    c.circle(cx, cy, r, fill=1, stroke=1)
    if label:
        text_block(c, cx, cy, label, size=r*0.95, color=WHITE)

# ─── node wrapper ──────────────────────────────────────────
def node(c, shape, cx, cy, w, h, text, key, size=10.5, font=FB, tcolor=WHITE):
    {'terminator':sym_terminator,'process':sym_process,'decision':sym_decision,
     'io':sym_io,'db':sym_db,'sub':sym_sub,'manual':sym_manual,'doc':sym_doc}[shape](
        c, cx, cy, w, h, COL[key])
    text_block(c, cx, cy, text, size=size, color=tcolor, font=font)
    return {'cx':cx,'cy':cy,'w':w,'h':h,
            'top':(cx,cy+h/2),'bot':(cx,cy-h/2),
            'left':(cx-w/2,cy),'right':(cx+w/2,cy)}

# ─── ลูกศร ─────────────────────────────────────────────────
def _arrowhead(c, x, y, ang, color, size=7.5):
    p = c.beginPath(); p.moveTo(x, y)
    p.lineTo(x - size*math.cos(ang - 0.42), y - size*math.sin(ang - 0.42))
    p.lineTo(x - size*math.cos(ang + 0.42), y - size*math.sin(ang + 0.42))
    p.close()
    c.setFillColor(HexColor(color)); c.drawPath(p, fill=1, stroke=0)

def label(c, x, y, text, size=9, fg='#1A2327', bg='#FFFFFF', font=FB):
    c.setFont(font, size)
    w = pdfmetrics.stringWidth(text, font, size)
    if bg:
        c.setFillColor(HexColor(bg))
        c.rect(x - w/2 - 2.5, y - size*0.42, w + 5, size + 2, fill=1, stroke=0)
    c.setFillColor(HexColor(fg))
    c.drawCentredString(x, y, text)

def arrow(c, p1, p2, color='#37474F', lw=1.5, lab=None, lab_off=(0,0)):
    c.setStrokeColor(HexColor(color)); c.setLineWidth(lw)
    c.line(p1[0], p1[1], p2[0], p2[1])
    _arrowhead(c, p2[0], p2[1], math.atan2(p2[1]-p1[1], p2[0]-p1[0]), color)
    if lab:
        mx, my = (p1[0]+p2[0])/2 + lab_off[0], (p1[1]+p2[1])/2 + lab_off[1]
        label(c, mx, my, lab, fg=color)

def elbow(c, pts, color='#37474F', lw=1.5, lab=None, lab_at=None):
    c.setStrokeColor(HexColor(color)); c.setLineWidth(lw)
    for i in range(len(pts)-1):
        c.line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1])
    a, b = pts[-2], pts[-1]
    _arrowhead(c, b[0], b[1], math.atan2(b[1]-a[1], b[0]-a[0]), color)
    if lab and lab_at:
        label(c, lab_at[0], lab_at[1], lab, fg=color)

# ─── โครงหน้า ──────────────────────────────────────────────
def page_bg(c, W, H):
    c.setFillColor(PAGEBG); c.rect(0, 0, W, H, fill=1, stroke=0)

def header(c, W, H, title, subtitle):
    c.setFillColor(HEADBG); c.rect(0, H-62, W, 62, fill=1, stroke=0)
    c.setFillColor(HexColor('#4FC3F7')); c.rect(0, H-62, 7, 62, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont(FB, 17)
    c.drawString(28, H-32, title)
    c.setFillColor(HexColor('#B0BEC5')); c.setFont(F, 10.5)
    c.drawString(28, H-50, subtitle)

def footer(c, W, pg, total):
    c.setFillColor(HexColor('#90A4AE')); c.setFont(F, 8.5)
    c.drawString(28, 20, 'WalletRecord — ระบบ POS + บัญชีร้านอาหาร (Google Apps Script + Google Sheets)')
    c.drawRightString(W-28, 20, 'หน้า %d / %d' % (pg, total))

TOTAL_PAGES = 6

def new_page(c, W, H, title, subtitle, pg):
    page_bg(c, W, H); header(c, W, H, title, subtitle); footer(c, W, pg, TOTAL_PAGES)

# ════════════════════════════════════════════════════════════
OUT = '/Users/admin/Developer/WalletRecord_Flowchart.pdf'
PW, PH = A4              # portrait 595 x 842
LW, LH = landscape(A4)  # 842 x 595
c = canvas.Canvas(OUT, pagesize=A4)

# ════════════════════════════════════════════════════════════
# หน้า 1 : ภาพรวมระบบ (สถาปัตยกรรม)
# ════════════════════════════════════════════════════════════
c.setPageSize(A4)
new_page(c, PW, PH, 'WalletRecord คืออะไร — ภาพรวมระบบ',
         'แอปจดบิล/ขายหน้าร้าน (POS) + บัญชีรายรับ-รายจ่าย ทำงานบนเว็บ เก็บข้อมูลใน Google Sheets', 1)

cx = PW/2
# กล่องอธิบายสั้น ๆ ด้านบน
c.setFillColor(HexColor('#FFFDE7')); c.setStrokeColor(HexColor('#FBC02D')); c.setLineWidth(1)
c.roundRect(34, PH-150, PW-68, 70, 6, fill=1, stroke=1)
c.setFillColor(INK); c.setFont(FB, 11.5)
c.drawString(46, PH-104, 'พูดให้เห็นภาพ:  พนักงานเปิดเว็บบนแท็บเล็ต กดสั่งอาหารเข้าโต๊ะ → ปิดบิล → ระบบบันทึกยอดขายเอง')
c.setFillColor(HexColor('#455A64')); c.setFont(F, 10.5)
c.drawString(46, PH-122, 'ทั้งหมดทำงานบนบริการฟรีของ Google ไม่มีเซิร์ฟเวอร์ของตัวเอง  •  ข้อมูลทุกอย่างเก็บเป็นตารางใน Google Sheets')
c.drawString(46, PH-138, 'ด้านล่างคือ “เส้นทางของข้อมูล” จากนิ้วผู้ใช้ ลงไปจนถึงฐานข้อมูล แล้วส่งผลลัพธ์กลับขึ้นมา')

# 6 ชั้น เรียงจากบนลงล่าง
W_BOX = 430
layers = [
    ('terminator','start',
     'ผู้ใช้งาน  —  พนักงานหน้าร้าน / เจ้าของร้าน\n(เปิดผ่านเบราว์เซอร์บนแท็บเล็ต หรือ มือถือ)', 11),
    ('process','process',
     'หน้าจอเว็บแอป   (ไฟล์ app.html)\nเมนูอาหาร • เปิดโต๊ะ/สั่งอาหาร • รายรับ-รายจ่าย • ประวัติ • รายงาน', 11),
    ('io','io',
     'สะพานเชื่อมของ Google   ( google.script.run )\nส่ง “คำสั่ง + ข้อมูล” จากหน้าจอ ไปยังเซิร์ฟเวอร์ของ Google', 10.5),
    ('sub','decision',
     'ตัวจัดเส้นทาง   (ไฟล์ WebApp.js → doPost)\nดูว่าคำสั่งคืออะไร (action) แล้วส่งต่อให้ฟังก์ชันที่ถูกต้อง', 10.5),
    ('sub','sub',
     'สมองประมวลผล   (ไฟล์ Api.js)\nคิดเลข/ตรวจเงื่อนไข/สั่งอ่าน-เขียนข้อมูล เช่น createSession, closeSession, saveExpense', 10),
    ('db','db',
     'ฐานข้อมูล   Google Sheets\norder_sessions • order_items • menu_items • income/expense • master_admin', 10.5),
]
top = PH - 178
gap = 30
h_box = 52
ys = []
for i,(shape,key,txt,sz) in enumerate(layers):
    cy = top - i*(h_box+gap) - h_box/2
    ys.append(cy)
    node(c, shape, cx, cy, W_BOX, h_box, txt, key, size=sz)

# ลูกศร ลง(คำขอ ซ้าย) + ขึ้น(คำตอบ ขวา) ระหว่างชั้น
for i in range(len(layers)-1):
    y_from = ys[i] - h_box/2
    y_to   = ys[i+1] + h_box/2
    arrow(c, (cx-70, y_from), (cx-70, y_to+1), color='#C62828', lw=1.6)
    arrow(c, (cx+70, y_to),   (cx+70, y_from-1), color='#2E7D32', lw=1.6)
# คำกำกับลูกศร (ครั้งเดียว ช่องบนสุด)
label(c, cx-70, (ys[0]-h_box/2 + ys[1]+h_box/2)/2, 'คำขอ ▼', fg='#C62828', bg='#F7F9FB', size=9)
label(c, cx+70, (ys[0]-h_box/2 + ys[1]+h_box/2)/2, '▲ คำตอบ', fg='#2E7D32', bg='#F7F9FB', size=9)
c.showPage()

# ════════════════════════════════════════════════════════════
# หน้า 2 : วงจรการใช้งานหน้าร้าน (POS) — flow หลัก
# ════════════════════════════════════════════════════════════
c.setPageSize(A4)
new_page(c, PW, PH, 'ขั้นตอนใช้งานจริงหน้าร้าน  (วงจรการขาย)',
         'ตั้งแต่พนักงานล็อกอิน → เปิดโต๊ะ → สั่งอาหาร → ปิดบิล หรือ ยกเลิกโต๊ะ', 2)

cxL = 205          # เส้นหลัก (spine) ค่อนไปทางซ้าย เผื่อ branch ขวา
W1 = 250
top = PH - 96

def n(shape, cy, txt, key, w=W1, h=46, sz=10.5, x=None):
    return node(c, shape, x if x else cxL, cy, w, h, txt, key, size=sz)

y = top
A = n('terminator', y, 'เริ่ม — เปิดแอป', 'start', w=180, h=40);  y -= 64
B = n('manual', y, 'พนักงานกรอกรหัส PIN', 'manual', h=46);       y -= 70
C = n('decision', y, 'PIN ถูกต้อง?', 'decision', w=170, h=74);   y -= 96
D = n('process', y, 'เข้าหน้าหลัก — เห็นโต๊ะที่เปิดอยู่', 'process', w=265, h=44); y -= 64
E = n('manual', y, 'เลือก “เปิดโต๊ะใหม่” + ตั้งชื่อโต๊ะ', 'manual', w=265, h=48); y -= 72
Fd = n('decision', y, 'ชื่อโต๊ะนี้\nเปิดค้างอยู่แล้ว?', 'decision', w=180, h=80); y -= 104
G = n('sub', y, 'createSession()\nสร้างโต๊ะใหม่ (สถานะ open)', 'sub', w=255, h=50); y -= 70
H = n('sub', y, 'addOrderItem()  — กดสั่งอาหารเข้าโต๊ะ\n(ทำซ้ำได้เรื่อย ๆ ทีละจาน)', 'sub', w=300, h=52); y -= 74
I = n('decision', y, 'จะทำอะไรต่อ\nกับโต๊ะนี้?', 'decision', w=185, h=84); y -= 92
J = n('terminator', y, 'จบหนึ่งรอบบริการ', 'start', w=200, h=40)

# --- เส้นหลัก ---
arrow(c, A['bot'], B['top'])
arrow(c, B['bot'], C['top'])
arrow(c, C['bot'], D['top'], lab='ถูก', lab_off=(12,0), color='#2E7D32')
arrow(c, D['bot'], E['top'])
arrow(c, E['bot'], Fd['top'])
arrow(c, Fd['bot'], G['top'], lab='ยังไม่เปิด', lab_off=(26,0), color='#2E7D32')
arrow(c, G['bot'], H['top'])
arrow(c, H['bot'], I['top'])

# --- PIN ผิด : ย้อนกลับ ---
xR = 430
elbow(c, [C['right'], (xR, C['cy']), (xR, B['cy']), B['right']],
      color='#C62828', lab='ผิด → ให้กรอกใหม่', lab_at=(xR-2, (C['cy']+B['cy'])/2))

# --- โต๊ะซ้ำ : ใช้โต๊ะเดิม ---
elbow(c, [Fd['right'], (xR, Fd['cy']), (xR, H['cy']+8), (H['cx']+H['w']/2, H['cy']+8)],
      color='#EF6C00', lab='เปิดแล้ว → ใช้โต๊ะเดิม', lab_at=(xR-2, Fd['cy']-12))

# --- ทางเลือกที่โต๊ะ (decision I) : 3 ทาง ---
# 1) สั่งเพิ่ม → วนกลับขึ้นไป H
elbow(c, [I['left'], (70, I['cy']), (70, H['cy']), H['left']],
      color='#1565C0', lab='สั่งเพิ่ม', lab_at=(70, (I['cy']+H['cy'])/2))
# 2) ปิดบิล (ลงล่างทางขวา)
K = node(c, 'sub', 430, I['cy']-2, 250, 52,
         'closeSession()\nคิดเงิน + ปิดโต๊ะ', 'sub', size=10.5)
arrow(c, I['right'], K['left'], lab='ปิดบิล', color='#2E7D32', lab_off=(0,7))
L = node(c, 'db', 430, K['cy']-86, 270, 58,
         'บันทึกยอดขายอัตโนมัติ\n(income_transactions)\nเปลี่ยนสถานะโต๊ะ → paid', 'db', size=9.5)
arrow(c, K['bot'], L['top'])
M = node(c, 'doc', 430, L['cy']-86, 220, 58,
         'ได้เลขใบเสร็จ\nPOS-วันที่-เวลา\n+ ยอดรวม', 'doc', size=10)
arrow(c, L['bot'], M['top'])
arrow(c, M['bot'], (M['cx'], J['cy']+8))
arrow(c, (M['cx'], J['cy']+8), J['right'])
# 3) ยกเลิกโต๊ะ (ลงตรง ๆ จาก I)
N = n('decision', I['cy']-104, 'โต๊ะนี้จ่ายเงิน\n(paid) แล้ว?', 'decision', w=185, h=82, x=cxL)
arrow(c, I['bot'], N['top'], lab='ยกเลิกโต๊ะ', color='#C62828', lab_off=(0,3))
O = n('sub', N['cy']-86, 'deleteSession()\nลบโต๊ะ + รายการอาหารทิ้ง', 'sub', w=265, h=50, x=cxL)
arrow(c, N['bot'], O['top'], lab='ยังไม่จ่าย', color='#2E7D32', lab_off=(28,0))
arrow(c, O['bot'], (O['cx'], J['cy']))
arrow(c, (O['cx'], J['cy']), J['left'])
# N = paid → ห้ามลบ
P = node(c, 'doc', 70, N['cy'], 120, 56, 'ห้ามลบ!\nบิลจ่ายแล้ว', 'doc', size=9.5)
arrow(c, N['left'], P['right'], lab='จ่ายแล้ว', color='#C62828', lab_off=(0,7))
c.showPage()

# ════════════════════════════════════════════════════════════
# หน้า 3 : เบื้องหลัง 1 คำสั่งเดินทางอย่างไร (request journey) — แนวนอน
# ════════════════════════════════════════════════════════════
c.setPageSize(landscape(A4))
new_page(c, LW, LH, 'เบื้องหลัง: 1 คำสั่งเดินทางอย่างไร',
         'ตัวอย่าง “กดปิดบิล” — ตามรอยข้อมูลจากหน้าจอ ไปเซิร์ฟเวอร์ แล้วกลับมา', 3)

midy = LH/2 + 30
bw, bh = 150, 70
xs = [110, 285, 460, 635]
steps_top = [
    ('process','process','① หน้าจอ (app.html)\nกดปุ่ม “ปิดบิล”\nรวบรวม session_id'),
    ('io','io','② google.script.run\n.doPost(action=\n"closeSession")'),
    ('sub','decision','③ WebApp.js (Router)\nอ่าน action\nเรียก closeSession()'),
    ('sub','sub','④ Api.js : closeSession()\nรวมเงินทุกจาน\nสร้างเลขใบเสร็จ'),
]
tops = []
for (shape,key,txt),x in zip(steps_top, xs):
    tops.append(node(c, shape, x, midy+70, bw, bh, txt, key, size=9))
for i in range(len(tops)-1):
    arrow(c, tops[i]['right'], tops[i+1]['left'], color='#1565C0')

# ลงไปฐานข้อมูล
db = node(c, 'db', xs[3], midy-70, 175, 80,
          '⑤ Google Sheets\nเขียน income_transactions\n+ income_invoice_items\nอัปเดต order_sessions=paid', 'db', size=8.6)
arrow(c, tops[3]['bot'], db['top'], color='#6A1B9A', lab='อ่าน/เขียน', lab_off=(34,0))

# flush note
c.setFillColor(HexColor('#FFF3E0')); c.setStrokeColor(HexColor('#FB8C00')); c.setLineWidth(1)
c.roundRect(xs[3]+105, midy-95, 175, 52, 5, fill=1, stroke=1)
c.setFillColor(INK); c.setFont(FB, 9)
c.drawString(xs[3]+114, midy-58, 'ทุกครั้งที่เขียน ต้อง')
c.setFillColor(HexColor('#E65100')); c.setFont(FB, 9.5)
c.drawString(xs[3]+114, midy-72, 'SpreadsheetApp.flush()')
c.setFillColor(INK); c.setFont(F, 8.6)
c.drawString(xs[3]+114, midy-86, 'กันอ่านค่าเก่าหลังเพิ่งเขียน')

# กลับขึ้นมา : ผลลัพธ์เดินทางย้อน
back = node(c, 'io', xs[1], midy-70, 175, 70,
            '⑥ ส่งผลกลับเป็น JSON\n{success, invoice_no, total}', 'io', size=9)
arrow(c, db['left'], back['right'], color='#2E7D32', lab='ผลลัพธ์', lab_off=(0,9))
shown = node(c, 'doc', xs[0], midy-70, 165, 70,
             '⑦ หน้าจอแสดงผล\n“ปิดบิลสำเร็จ”\nโชว์ใบเสร็จ + ยอดรวม', 'doc', size=9)
arrow(c, back['left'], shown['right'], color='#2E7D32')
arrow(c, shown['top'], tops[0]['bot'], color='#2E7D32', lab='อัปเดตจอ', lab_off=(40,0))

# โน้ตอธิบายซ้ายล่าง
c.setFillColor(HexColor('#ECEFF1')); c.setStrokeColor(HexColor('#B0BEC5')); c.setLineWidth(1)
c.roundRect(40, 46, 470, 56, 5, fill=1, stroke=1)
c.setFillColor(INK); c.setFont(FB, 9.5)
c.drawString(52, 84, 'จุดสำคัญ:  ระบบนี้ไม่มี REST API / ไม่มี fetch — หน้าเว็บคุยกับเซิร์ฟเวอร์ผ่าน google.script.run เท่านั้น')
c.setFillColor(HexColor('#455A64')); c.setFont(F, 9)
c.drawString(52, 68, 'ทุกการกระทำ (เปิดโต๊ะ, สั่งอาหาร, บันทึกรายจ่าย ฯลฯ) เดินตามเส้นทาง ①→⑦ แบบเดียวกันนี้ เปลี่ยนแค่ชื่อ action')
c.drawString(52, 54, 'เซิร์ฟเวอร์มีเวลาทำงานจำกัด 6 นาทีต่อครั้ง — จึงออกแบบให้แต่ละคำสั่งเล็กและจบเร็ว')
c.showPage()

# ════════════════════════════════════════════════════════════
# หน้า 4 : รายรับ-รายจ่าย + การบันทึกเข้า Sheet (2 flow ย่อย)
# ════════════════════════════════════════════════════════════
c.setPageSize(A4)
new_page(c, PW, PH, 'บันทึกรายจ่าย & รายรับ',
         'อีกหน้าที่หนึ่งของแอป: ลงบัญชีเงินเข้า-ออกของร้าน เก็บเป็น 2 ตารางคู่กันเสมอ', 4)

# สองคอลัมน์
LX, RX = 165, 430
ytop = PH - 110
def col(x, title, key_head, steps):
    cy = ytop
    head = node(c, 'terminator', x, cy, 250, 42, title, key_head, size=11)
    prev = head
    cy -= 64
    for (shape,key,txt,h,sz) in steps:
        nd = node(c, shape, x, cy, 250, h, txt, key, size=sz)
        arrow(c, prev['bot'], nd['top'])
        prev = nd
        cy -= h/2 + 26 + 999*0  # placeholder
        cy = nd['bot'][1] - 26 - 0
        cy = nd['cy'] - h/2 - 26
        # next center computed below
    return head

# วาดเองเพื่อคุมระยะ
def column(x, title, headkey, steps):
    cy = ytop
    prev = node(c, 'terminator', x, cy, 250, 42, title, headkey, size=11)
    for (shape,key,txt,h,sz) in steps:
        cy = prev['bot'][1] - 30 - h/2
        nd = node(c, shape, x, cy, 250, h, txt, key, size=sz)
        arrow(c, prev['bot'], nd['top'])
        prev = nd
    return prev

# รายจ่าย (ซ้าย)
column(LX, 'บันทึก “รายจ่าย”', 'start', [
    ('manual','manual', 'กรอก: วันที่ • แหล่งซื้อ\nรายการของ • จำนวน • ราคา', 52, 9.8),
    ('io','io', 'ส่ง action = saveExpense', 44, 10),
    ('sub','sub', 'saveExpense()\nหาเลขแหล่งซื้อ (source)', 50, 10),
    ('db','db', 'เขียนหัวบิล\nexpense_transactions', 48, 9.8),
    ('db','db', 'เขียนรายการย่อยทีละชิ้น\nexpense_items', 48, 9.8),
    ('terminator','start', 'เสร็จ — คืนเลขบิล', 40, 10),
])
# รายรับ (ขวา)
column(RX, 'บันทึก “รายรับ”', 'start', [
    ('manual','manual', 'มาจากปิดบิล POS\nหรือกรอกเอง', 48, 9.8),
    ('io','io', 'ส่ง action = saveIncome', 44, 10),
    ('decision','decision', 'มีชื่อลูกค้านี้\nอยู่แล้ว?', 64, 9.8),
    ('db','db', 'เขียนหัวบิล\nincome_transactions', 48, 9.8),
    ('db','db', 'เขียนรายการย่อยทีละชิ้น\nincome_invoice_items', 48, 9.8),
    ('terminator','start', 'เสร็จ — คืนเลขบิล', 40, 10),
])
# หมายเหตุ customer ใหม่
c.setFillColor(HexColor('#455A64')); c.setFont(F, 8.6)
c.drawCentredString(RX, ytop-64-30-64-2-40,
                    '(ถ้ายังไม่มี → สร้างลูกค้าใหม่ในตาราง customers ก่อน)')

# กล่องสรุปล่าง
c.setFillColor(HexColor('#E8F5E9')); c.setStrokeColor(HexColor('#43A047')); c.setLineWidth(1)
c.roundRect(40, 70, PW-80, 78, 6, fill=1, stroke=1)
c.setFillColor(INK); c.setFont(FB, 11)
c.drawString(54, 124, 'เห็นรูปแบบเดียวกันไหม?  ทั้งรายรับและรายจ่ายเก็บเป็น “ตารางคู่” เสมอ:')
c.setFillColor(HexColor('#1B5E20')); c.setFont(FB, 10.5)
c.drawString(54, 104, '   • ตารางหัวบิล (transactions) = 1 แถวต่อ 1 บิล  → เก็บวันที่ ยอดรวม')
c.drawString(54, 88,  '   • ตารางรายการย่อย (items) = หลายแถวต่อ 1 บิล  → เก็บของแต่ละชิ้น/จาน')
c.showPage()

# ════════════════════════════════════════════════════════════
# หน้า 5 : ตาราง action ทั้งหมด (ภาคผนวก)
# ════════════════════════════════════════════════════════════
c.setPageSize(A4)
new_page(c, PW, PH, 'คำสั่ง (action) ทั้งหมดที่ระบบรองรับ',
         'ทุกปุ่มบนหน้าจอ = ส่ง 1 action เข้า WebApp.js แล้ววิ่งไปฟังก์ชันใน Api.js', 5)

groups = [
    ('โต๊ะ / ออเดอร์ (POS)', '#1565C0', [
        ('getOpenSessions', 'ดึงโต๊ะที่เปิดค้างอยู่ + รายการอาหาร'),
        ('createSession', 'เปิดโต๊ะใหม่ (กันชื่อซ้ำ)'),
        ('addOrderItem', 'สั่งอาหารเข้าโต๊ะ'),
        ('updateItemStatus', 'เปลี่ยนสถานะจาน (เช่น เสิร์ฟแล้ว)'),
        ('removeOrderItem', 'ลบรายการอาหารออก'),
        ('closeSession', 'ปิดบิล → สร้างรายรับอัตโนมัติ'),
        ('deleteSession', 'ยกเลิกโต๊ะ (ห้ามลบถ้าจ่ายแล้ว)'),
    ]),
    ('เมนูอาหาร', '#00838F', [
        ('getMenuItems / getMenuCategories', 'ดึงเมนูและหมวดหมู่'),
        ('saveMenuItem / updateMenuItem', 'เพิ่ม/แก้เมนู'),
        ('deleteMenuItem', 'ลบเมนู'),
        ('saveMenuCategory', 'เพิ่มหมวดหมู่'),
        ('getMenuImage(s) / syncMenuImages', 'จัดการรูปเมนู'),
    ]),
    ('เงิน: รายรับ-รายจ่าย', '#6A1B9A', [
        ('saveExpense / updateExpense', 'บันทึก/แก้รายจ่าย'),
        ('saveIncome', 'บันทึกรายรับ'),
        ('getExpenseDescriptions', 'ดึงรายการของที่เคยซื้อ'),
        ('deleteTransaction', 'ลบบิลรายรับ/รายจ่าย'),
    ]),
    ('ประวัติ / รายงาน / ผู้ใช้', '#EF6C00', [
        ('getHistory / getSummary', 'ดูประวัติ + ยอดสรุป'),
        ('getTransactionItems / searchItems', 'ดูรายการในบิล / ค้นหา'),
        ('getSalesReport / getMenuRankByPeriod', 'รายงานยอดขาย + เมนูขายดี'),
        ('getIngredientStock', 'ประเมินวัตถุดิบคงเหลือ'),
        ('getAdminByPin', 'ตรวจ PIN ตอนล็อกอิน'),
    ]),
]
y = PH - 96
for gname, gcol, rows in groups:
    c.setFillColor(HexColor(gcol)); c.roundRect(34, y-20, PW-68, 24, 4, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont(FB, 11); c.drawString(44, y-15, gname)
    y -= 30
    for fn, desc in rows:
        c.setFillColor(HexColor('#0D1B22')); c.setFont(FB, 9.7)
        c.drawString(52, y-9, fn)
        c.setFillColor(HexColor('#455A64')); c.setFont(F, 9.7)
        c.drawString(290, y-9, '— ' + desc)
        c.setStrokeColor(HexColor('#E0E4E7')); c.setLineWidth(0.5); c.line(48, y-15, PW-40, y-15)
        y -= 19
    y -= 8
c.showPage()

# ════════════════════════════════════════════════════════════
# หน้า 6 : คำอธิบายสัญลักษณ์ (Legend)
# ════════════════════════════════════════════════════════════
c.setPageSize(A4)
new_page(c, PW, PH, 'คำอธิบายสัญลักษณ์ผังงาน (Legend)',
         'สัญลักษณ์มาตรฐาน ANSI/ISO ที่ใช้ในเอกสารนี้ — แต่ละรูปทรงมีความหมายเฉพาะ', 6)

legend = [
    ('terminator','start', 'จุดเริ่มต้น / จุดสิ้นสุด', 'ทรงแคปซูล — บอกว่าเริ่มหรือจบการทำงาน (Terminator)'),
    ('process','process', 'ขั้นตอนการทำงานทั่วไป', 'สี่เหลี่ยมผืนผ้า — การประมวลผล 1 ขั้น (Process)'),
    ('sub','sub', 'เรียกฟังก์ชันสำเร็จรูป', 'สี่เหลี่ยมมีขีดข้างสองข้าง — เรียกฟังก์ชันที่นิยามไว้แล้ว เช่น closeSession() (Predefined process)'),
    ('decision','decision', 'การตัดสินใจ', 'สี่เหลี่ยมข้าวหลามตัด — จุดเลือกทาง ตอบ ใช่/ไม่ (Decision)'),
    ('io','io', 'รับ / ส่งข้อมูล', 'สี่เหลี่ยมด้านขนาน — ข้อมูลเข้า-ออกระหว่างระบบ (Input/Output)'),
    ('manual','manual', 'กรอกข้อมูลด้วยมือ', 'ทรงสี่เหลี่ยมขอบบนเฉียง — คนพิมพ์/กรอกข้อมูลเอง เช่น ใส่ PIN (Manual input)'),
    ('db','db', 'ฐานข้อมูล', 'ทรงกระบอก — อ่าน/เขียนข้อมูลใน Google Sheets (Database)'),
    ('doc','doc', 'เอกสาร / ใบเสร็จ', 'สี่เหลี่ยมก้นหยัก — ผลลัพธ์ที่เป็นเอกสาร เช่น ใบเสร็จ (Document)'),
]
y = PH - 110
for shape, key, name, desc in legend:
    node(c, shape, 95, y, 110, 46, '', key)
    c.setFillColor(INK); c.setFont(FB, 12)
    c.drawString(175, y+6, name)
    c.setFillColor(HexColor('#455A64')); c.setFont(F, 10)
    c.drawString(175, y-12, desc)
    c.setStrokeColor(HexColor('#E0E4E7')); c.setLineWidth(0.6); c.line(40, y-34, PW-40, y-34)
    y -= 64

# ลูกศร
yy = y - 6
c.setFillColor(INK); c.setFont(FB, 12); c.drawString(40, yy, 'ความหมายของลูกศร')
yy -= 26
c.setStrokeColor(HexColor('#37474F')); c.setLineWidth(1.6)
c.line(70, yy, 150, yy); _arrowhead(c, 150, yy, 0, '#37474F')
c.setFillColor(INK); c.setFont(F, 10.5); c.drawString(165, yy-3, 'ทิศทางการไหลของงาน → ไปยังขั้นตอนถัดไป')
yy -= 26
c.setStrokeColor(HexColor('#2E7D32')); c.line(70, yy, 150, yy); _arrowhead(c, 150, yy, 0, '#2E7D32')
c.setFillColor(INK); c.drawString(165, yy-3, 'เส้นทาง “ใช่ / สำเร็จ”')
yy -= 26
c.setStrokeColor(HexColor('#C62828')); c.line(70, yy, 150, yy); _arrowhead(c, 150, yy, 0, '#C62828')
c.setFillColor(INK); c.drawString(165, yy-3, 'เส้นทาง “ไม่ / ผิดพลาด / ย้อนกลับ”')

# กล่องสีอ้างอิง
yy -= 40
c.setFillColor(HexColor('#FFFDE7')); c.setStrokeColor(HexColor('#FBC02D')); c.setLineWidth(1)
c.roundRect(40, yy-30, PW-80, 50, 5, fill=1, stroke=1)
c.setFillColor(INK); c.setFont(FB, 10)
c.drawString(54, yy+2, 'หมายเหตุ: สีของกล่องช่วยให้กวาดตาดูง่ายขึ้น แต่ “รูปทรง” คือสิ่งที่บอกความหมายตามมาตรฐาน')
c.setFillColor(HexColor('#455A64')); c.setFont(F, 9.5)
c.drawString(54, yy-14, 'เขียว=เริ่ม/จบ • น้ำเงิน/คราม=ทำงาน • ส้ม=ตัดสินใจ • ม่วง=ฐานข้อมูล • ฟ้าเขียว=รับส่งข้อมูล • น้ำตาล=กรอกมือ • ชมพู=เอกสาร')
c.showPage()

c.save()
print('saved:', OUT)
