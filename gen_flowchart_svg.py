# -*- coding: utf-8 -*-
"""
สร้าง Flowchart โปรเจค WalletRecord เป็น HTML(SVG) แล้วให้ Chrome พิมพ์เป็น PDF
- ภาษาไทยถูกต้อง (Chrome shaping)
- สัญลักษณ์ผังงานมาตรฐาน ANSI/ISO
ผลลัพธ์ HTML: /Users/admin/Developer/WalletRecord_Main/_flowchart.html
"""
import math, html

PAGES = []          # list ของ svg-string ต่อหน้า
W, H = 794, 1123    # A4 portrait @96dpi

COL = {
    'start':'#2E7D32','process':'#1565C0','decision':'#EF6C00','db':'#6A1B9A',
    'io':'#00838F','sub':'#283593','manual':'#6D4C41','doc':'#AD1457','conn':'#455A64',
}
OUT = '#1A2327'
ARROW_COLORS = ['#37474F','#2E7D32','#C62828','#1565C0','#EF6C00','#6A1B9A','#00838F']

def esc(s): return html.escape(s, quote=True)

# ─── สัญลักษณ์ (คืน svg path/shape) ─────────────────────────
def _shape(kind, cx, cy, w, h, fill):
    x1,y1,x2,y2 = cx-w/2, cy-h/2, cx+w/2, cy+h/2
    st = f'fill="{fill}" stroke="{OUT}" stroke-width="1.4"'
    if kind=='terminator':
        return f'<rect x="{x1:.1f}" y="{y1:.1f}" width="{w}" height="{h}" rx="{h/2:.1f}" ry="{h/2:.1f}" {st}/>'
    if kind=='process':
        return f'<rect x="{x1:.1f}" y="{y1:.1f}" width="{w}" height="{h}" {st}/>'
    if kind=='decision':
        return f'<polygon points="{cx:.1f},{y1:.1f} {x2:.1f},{cy:.1f} {cx:.1f},{y2:.1f} {x1:.1f},{cy:.1f}" {st}/>'
    if kind=='io':
        o=h*0.5
        return f'<polygon points="{x1+o:.1f},{y1:.1f} {x2:.1f},{y1:.1f} {x2-o:.1f},{y2:.1f} {x1:.1f},{y2:.1f}" {st}/>'
    if kind=='manual':
        sl=h*0.4
        return f'<polygon points="{x1:.1f},{y1+sl:.1f} {x2:.1f},{y1:.1f} {x2:.1f},{y2:.1f} {x1:.1f},{y2:.1f}" {st}/>'
    if kind=='sub':
        ins=min(11,w*0.07)
        return (f'<rect x="{x1:.1f}" y="{y1:.1f}" width="{w}" height="{h}" {st}/>'
                f'<line x1="{x1+ins:.1f}" y1="{y1:.1f}" x2="{x1+ins:.1f}" y2="{y2:.1f}" stroke="#fff" stroke-width="1"/>'
                f'<line x1="{x2-ins:.1f}" y1="{y1:.1f}" x2="{x2-ins:.1f}" y2="{y2:.1f}" stroke="#fff" stroke-width="1"/>')
    if kind=='db':
        ry=h*0.13; rx=w/2
        body=(f'M {x1:.1f},{y1+ry:.1f} L {x1:.1f},{y2-ry:.1f} '
              f'A {rx:.1f},{ry:.1f} 0 0 0 {x2:.1f},{y2-ry:.1f} '
              f'L {x2:.1f},{y1+ry:.1f} A {rx:.1f},{ry:.1f} 0 0 1 {x1:.1f},{y1+ry:.1f} Z')
        return (f'<path d="{body}" {st}/>'
                f'<ellipse cx="{cx:.1f}" cy="{y1+ry:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" {st}/>')
    if kind=='doc':
        wv=h*0.16
        d=(f'M {x1:.1f},{y1:.1f} L {x2:.1f},{y1:.1f} L {x2:.1f},{y2-wv:.1f} '
           f'C {x2-w*0.25:.1f},{y2+wv:.1f} {cx+w*0.05:.1f},{y2-2*wv:.1f} {cx:.1f},{y2-wv:.1f} '
           f'C {x1+w*0.25:.1f},{y2:.1f} {x1+w*0.20:.1f},{y2-2*wv:.1f} {x1:.1f},{y2-wv:.1f} Z')
        return f'<path d="{d}" {st}/>'
    raise ValueError(kind)

def text(cx, cy, s, size=14, color='#fff', bold=True, lh=None):
    lines=s.split('\n'); lh=lh or size*1.32
    fw='700' if bold else '400'
    y0=cy-(len(lines)-1)*lh/2
    out=[f'<text x="{cx:.1f}" y="{y0:.1f}" text-anchor="middle" dominant-baseline="central" '
         f'font-family="\'Sukhumvit Set\',\'Thonburi\',sans-serif" font-size="{size}" font-weight="{fw}" fill="{color}">']
    for i,ln in enumerate(lines):
        out.append(f'<tspan x="{cx:.1f}" y="{y0+i*lh:.1f}">{esc(ln)}</tspan>')
    out.append('</text>')
    return ''.join(out)

def node(buf, kind, key, cx, cy, w, h, s, size=14, tcolor='#fff'):
    buf.append(_shape(kind, cx, cy, w, h, COL[key]))
    if s: buf.append(text(cx, cy, s, size=size, color=tcolor))
    return {'cx':cx,'cy':cy,'w':w,'h':h,'t':(cx,cy-h/2),'b':(cx,cy+h/2),
            'l':(cx-w/2,cy),'r':(cx+w/2,cy)}

def _mid(color): return ARROW_COLORS.index(color)
def arrow(buf, p1, p2, color='#37474F', lw=1.8, lab=None, lab_dx=0, lab_dy=0):
    buf.append(f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
               f'stroke="{color}" stroke-width="{lw}" marker-end="url(#a{_mid(color)})"/>')
    if lab:
        mx,my=(p1[0]+p2[0])/2+lab_dx,(p1[1]+p2[1])/2+lab_dy
        textlabel(buf, mx, my, lab, color)

def elbow(buf, pts, color='#37474F', lw=1.8, lab=None, lab_at=None):
    d='M '+' L '.join(f'{x:.1f},{y:.1f}' for x,y in pts)
    buf.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{lw}" marker-end="url(#a{_mid(color)})"/>')
    if lab and lab_at: textlabel(buf, lab_at[0], lab_at[1], lab, color)

def textlabel(buf, x, y, s, color='#1A2327', size=11.5, bg='#F7F9FB'):
    w=len(s)*size*0.55+10
    buf.append(f'<rect x="{x-w/2:.1f}" y="{y-size*0.85:.1f}" width="{w:.1f}" height="{size*1.7:.1f}" rx="3" fill="{bg}" opacity="0.95"/>')
    buf.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" dominant-baseline="central" '
               f'font-family="\'Sukhumvit Set\',\'Thonburi\',sans-serif" font-size="{size}" font-weight="700" fill="{color}">{esc(s)}</text>')

def rrect(buf,x,y,w,h,fill,stroke,sw=1,rx=6):
    buf.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

def plain(buf,x,y,s,size=12,color='#22303A',bold=False,anchor='start'):
    fw='700' if bold else '400'
    buf.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
               f'font-family="\'Sukhumvit Set\',\'Thonburi\',sans-serif" font-size="{size}" font-weight="{fw}" fill="{color}">{esc(s)}</text>')

# ─── โครงหน้า ─────────────────────────────────────────────
def page_start(title, sub, pg):
    b=[]
    b.append(f'<rect width="{W}" height="{H}" fill="#F7F9FB"/>')
    b.append(f'<rect x="0" y="0" width="{W}" height="84" fill="#11212B"/>')
    b.append(f'<rect x="0" y="0" width="9" height="84" fill="#4FC3F7"/>')
    plain(b,34,42,title,size=22,color='#fff',bold=True)
    plain(b,34,66,sub,size=13,color='#B0BEC5')
    plain(b,34,H-20,'WalletRecord — ระบบ POS + บัญชีร้านอาหาร (Google Apps Script + Google Sheets)',size=11,color='#90A4AE')
    plain(b,W-34,H-20,f'หน้า {pg} / 6',size=11,color='#90A4AE',anchor='end')
    return b

def page_end(b): PAGES.append('\n'.join(b))

# ════════════════════════════════════════════════════════════
# หน้า 1 : ภาพรวมระบบ
# ════════════════════════════════════════════════════════════
b=page_start('WalletRecord คืออะไร — ภาพรวมระบบ',
             'แอปจดบิล/ขายหน้าร้าน (POS) + บัญชีรายรับ-รายจ่าย ทำงานบนเว็บ เก็บข้อมูลใน Google Sheets',1)
cx=W/2
rrect(b,40,104,W-80,92,'#FFFDE7','#FBC02D',1.2)
plain(b,56,132,'พูดให้เห็นภาพ:  พนักงานเปิดเว็บบนแท็บเล็ต กดสั่งอาหารเข้าโต๊ะ → ปิดบิล → ระบบบันทึกยอดขายให้เอง',size=13.5,color='#22303A',bold=True)
plain(b,56,158,'• ทำงานบนบริการฟรีของ Google ไม่มีเซิร์ฟเวอร์ของตัวเอง  • ข้อมูลทุกอย่างเก็บเป็นตารางใน Google Sheets',size=12.5,color='#455A64')
plain(b,56,182,'• ด้านล่างคือ “เส้นทางของข้อมูล” จากนิ้วผู้ใช้ ลงไปถึงฐานข้อมูล แล้วส่งผลลัพธ์กลับขึ้นมา',size=12.5,color='#455A64')

WB=560; HB=66; gap=40; top=240
layers=[
 ('terminator','start','ผู้ใช้งาน — พนักงานหน้าร้าน / เจ้าของร้าน\n(เปิดผ่านเบราว์เซอร์บนแท็บเล็ต หรือ มือถือ)',14),
 ('process','process','หน้าจอเว็บแอป  (ไฟล์ app.html)\nเมนูอาหาร • เปิดโต๊ะ/สั่งอาหาร • รายรับ-รายจ่าย • ประวัติ • รายงาน',13),
 ('io','io','สะพานเชื่อมของ Google  ( google.script.run )\nส่ง “คำสั่ง + ข้อมูล” จากหน้าจอ ไปยังเซิร์ฟเวอร์ของ Google',12.5),
 ('sub','decision','ตัวจัดเส้นทาง  (ไฟล์ WebApp.js → doPost)\nดูว่าคำสั่งคืออะไร (action) แล้วส่งต่อให้ฟังก์ชันที่ถูกต้อง',12.5),
 ('sub','sub','สมองประมวลผล  (ไฟล์ Api.js)\nคิดเลข/ตรวจเงื่อนไข/อ่าน-เขียนข้อมูล เช่น createSession, closeSession',12),
 ('db','db','ฐานข้อมูล  Google Sheets\norder_sessions • order_items • menu_items • income/expense • master_admin',12.5),
]
ys=[]
for i,(k,key,t,sz) in enumerate(layers):
    cy=top+i*(HB+gap)+HB/2; ys.append(cy)
    node(b,k,key,cx,cy,WB,HB,t,size=sz)
for i in range(len(layers)-1):
    yb=ys[i]+HB/2; yt=ys[i+1]-HB/2
    arrow(b,(cx-95,yb),(cx-95,yt-1),color='#C62828')
    arrow(b,(cx+95,yt),(cx+95,yb+1),color='#2E7D32')
textlabel(b,cx-95,(ys[0]+HB/2+ys[1]-HB/2)/2,'คำขอ ▼','#C62828')
textlabel(b,cx+95,(ys[0]+HB/2+ys[1]-HB/2)/2,'▲ คำตอบ','#2E7D32')
page_end(b)

# ════════════════════════════════════════════════════════════
# หน้า 2 : วงจรการใช้งานหน้าร้าน (POS)
# ════════════════════════════════════════════════════════════
b=page_start('ขั้นตอนใช้งานจริงหน้าร้าน  (วงจรการขาย)',
             'พนักงานล็อกอิน → เปิดโต๊ะ → สั่งอาหาร → ปิดบิล หรือ ยกเลิกโต๊ะ',2)
SX=250   # spine x
RX=585   # branch x ขวา
def n2(k,key,cy,t,w,h,sz=12.5,x=None):
    return node(b,k,key,x if x else SX,cy,w,h,t,size=sz)

A=n2('terminator','start',120,'เริ่ม — เปิดแอป',230,46,13)
B=n2('manual','manual',196,'พนักงานกรอกรหัส PIN',240,56)
C=n2('decision','decision',300,'PIN ถูกต้อง?',190,84)
D=n2('process','process',410,'เข้าหน้าหลัก — เห็นโต๊ะที่เปิดอยู่',300,52)
E=n2('manual','manual',500,'เลือก “เปิดโต๊ะใหม่”\n+ ตั้งชื่อโต๊ะ',300,58,12)
Fd=n2('decision','decision',610,'ชื่อโต๊ะนี้\nเปิดค้างอยู่แล้ว?',210,92,12)
G=n2('sub','sub',718,'createSession()\nสร้างโต๊ะใหม่ (สถานะ open)',300,56,12.5)
Hn=n2('sub','sub',812,'addOrderItem() — สั่งอาหารเข้าโต๊ะ\n(ทำซ้ำได้เรื่อย ๆ ทีละจาน)',320,58,12)
I=n2('decision','decision',930,'จะทำอะไรต่อ\nกับโต๊ะนี้?',210,96,12.5)

arrow(b,A['b'],B['t'])
arrow(b,B['b'],C['t'])
arrow(b,C['b'],D['t'],color='#2E7D32',lab='ถูก',lab_dx=16)
arrow(b,D['b'],E['t'])
arrow(b,E['b'],Fd['t'])
arrow(b,Fd['b'],G['t'],color='#2E7D32',lab='ยังไม่เปิด',lab_dx=34)
arrow(b,G['b'],Hn['t'])
arrow(b,Hn['b'],I['t'])
# PIN ผิด → ย้อน
xr=560
elbow(b,[C['r'],(xr,C['cy']),(xr,B['cy']),B['r']],color='#C62828',lab='ผิด → กรอกใหม่',lab_at=(xr,(C['cy']+B['cy'])/2))
# โต๊ะซ้ำ → ใช้โต๊ะเดิม (ลงไป addOrderItem)
elbow(b,[Fd['r'],(690,Fd['cy']),(690,Hn['cy']+12),(Hn['r'][0],Hn['cy']+12)],color='#EF6C00',lab='เปิดแล้ว → ใช้เดิม',lab_at=(640,Fd['cy']-16))
# decision I : 3 ทาง
# 1 สั่งเพิ่ม → loop กลับขึ้น Hn
elbow(b,[I['l'],(95,I['cy']),(95,Hn['cy']),Hn['l']],color='#1565C0',lab='สั่งเพิ่ม',lab_at=(95,(I['cy']+Hn['cy'])/2))
# 2 ปิดบิล → ขวา
K=node(b,'sub','sub',RX,I['cy'],300,58,'closeSession()\nคิดเงิน + ปิดโต๊ะ',size=12.5)
arrow(b,I['r'],K['l'],color='#2E7D32',lab='ปิดบิล',lab_dy=-12)
L=node(b,'db','db',RX,I['cy']+118,330,72,'บันทึกยอดขายอัตโนมัติ\n(income_transactions)\nเปลี่ยนสถานะโต๊ะ → paid',size=11.5)
arrow(b,K['b'],L['t'])
M=node(b,'doc','doc',RX,I['cy']+240,250,76,'ได้ใบเสร็จ\nPOS-วันที่-เวลา\n+ ยอดรวม',size=12)
arrow(b,L['b'],M['t'])
# 3 ยกเลิก → ลง
N=n2('decision','decision',I['cy']+130,'โต๊ะนี้จ่ายเงิน\n(paid) แล้ว?',210,92,12)
arrow(b,I['b'],N['t'],color='#C62828',lab='ยกเลิกโต๊ะ',lab_dy=4)
O=n2('sub','sub',N['cy']+105,'deleteSession()\nลบโต๊ะ + รายการอาหารทิ้ง',300,56,12)
arrow(b,N['b'],O['t'],color='#2E7D32',lab='ยังไม่จ่าย',lab_dx=34)
# paid → ห้ามลบ (ซ้าย)
P=node(b,'doc','doc',95,N['cy'],150,68,'ห้ามลบ!\nบิลจ่ายแล้ว',size=12)
arrow(b,N['l'],P['r'],color='#C62828',lab='จ่ายแล้ว',lab_dy=-12)
# จบ
J=node(b,'terminator','start',(SX+RX)/2,1078,260,46,'จบหนึ่งรอบบริการ',size=13)
arrow(b,O['b'],(O['cx'],J['cy']),color='#37474F')
arrow(b,(O['cx'],J['cy']),J['l'])
arrow(b,M['b'],(M['cx'],J['cy']),color='#37474F')
arrow(b,(M['cx'],J['cy']),J['r'])
page_end(b)

# ════════════════════════════════════════════════════════════
# หน้า 3 : เบื้องหลัง 1 คำสั่งเดินทางอย่างไร (vertical)
# ════════════════════════════════════════════════════════════
b=page_start('เบื้องหลัง: 1 คำสั่งเดินทางอย่างไร',
             'ตัวอย่าง “กดปิดบิล” — ตามรอยข้อมูลจากหน้าจอ ไปเซิร์ฟเวอร์ แล้วกลับมา',3)
LCX=255   # คอลัมน์ขาไป (ลง)
RCX=545   # คอลัมน์ขากลับ (ขึ้น)
down=[
 ('process','process','① หน้าจอ (app.html) กดปุ่ม “ปิดบิล”\nรวบรวม session_id ของโต๊ะ',300,60,12.5),
 ('io','io','② google.script.run ส่งคำขอ\n(action = "closeSession")',300,60,12.5),
 ('sub','decision','③ WebApp.js (Router) อ่าน action\nแล้วเรียก closeSession()',300,60,12.5),
 ('sub','sub','④ Api.js : closeSession()\nรวมเงินทุกจาน + สร้างเลขใบเสร็จ',300,60,12.5),
 ('db','db','⑤ Google Sheets — เขียนข้อมูล\nincome_transactions + invoice_items\nอัปเดต order_sessions → paid',300,76,11.5),
]
ys=[]; top=130; gap=34
for i,(k,key,t,w,h,sz) in enumerate(down):
    cy=top+sum(down[j][4] for j in range(i))+i*gap+h/2; ys.append((cy,h))
    node(b,k,key,LCX,cy,w,h,t,size=sz)
for i in range(len(down)-1):
    arrow(b,(LCX,ys[i][0]+ys[i][1]/2),(LCX,ys[i+1][0]-ys[i+1][1]/2),color='#1565C0')
dby,dbh=ys[-1]
# ขากลับ (ขึ้น)
back=node(b,'io','io',RCX,dby-40,300,64,'⑥ ส่งผลกลับเป็น JSON\n{success, invoice_no, total}',size=12.5)
arrow(b,(LCX+150,dby),(RCX-150,back['cy']+10),color='#2E7D32',lab='ผลลัพธ์',lab_dy=-12)
shown=node(b,'doc','doc',RCX,dby-200,290,80,'⑦ หน้าจอแสดง “ปิดบิลสำเร็จ”\nโชว์ใบเสร็จ + ยอดรวม\nรีเฟรชรายการโต๊ะ',size=12)
arrow(b,back['t'],shown['b'],color='#2E7D32')
arrow(b,shown['t'],(RCX,ys[0][0]),color='#2E7D32',lab='อัปเดตจอ',lab_dx=46)
arrow(b,(RCX,ys[0][0]),(LCX+150,ys[0][0]),color='#2E7D32')
# โน้ต flush
rrect(b,40,dby+90,W-80,70,'#FFF3E0','#FB8C00',1.2)
plain(b,56,dby+118,'ทุกครั้งที่เขียนลง Sheets ต้องสั่ง SpreadsheetApp.flush() — กันการอ่านค่าเก่าทันทีหลังเพิ่งเขียน',size=12.5,color='#22303A',bold=True)
plain(b,56,dby+144,'(read-after-write miss) ซึ่งเป็นบั๊กที่เจอบ่อยใน Google Apps Script',size=12,color='#E65100')
# โน้ตสรุป
rrect(b,40,dby+185,W-80,96,'#ECEFF1','#B0BEC5',1)
plain(b,56,dby+214,'จุดสำคัญ:  ระบบนี้ไม่มี REST API / ไม่มี fetch — หน้าเว็บคุยกับเซิร์ฟเวอร์ผ่าน google.script.run เท่านั้น',size=12.5,color='#22303A',bold=True)
plain(b,56,dby+240,'ทุกการกระทำ (เปิดโต๊ะ, สั่งอาหาร, บันทึกรายจ่าย ฯลฯ) เดินตามเส้นทาง ①→⑦ แบบเดียวกัน เปลี่ยนแค่ชื่อ action',size=12,color='#455A64')
plain(b,56,dby+264,'เซิร์ฟเวอร์มีเวลาทำงานจำกัด 6 นาทีต่อครั้ง จึงออกแบบให้แต่ละคำสั่งเล็กและจบเร็ว',size=12,color='#455A64')
page_end(b)

# ════════════════════════════════════════════════════════════
# หน้า 4 : รายรับ-รายจ่าย
# ════════════════════════════════════════════════════════════
b=page_start('บันทึกรายจ่าย & รายรับ',
             'อีกหน้าที่ของแอป: ลงบัญชีเงินเข้า-ออกของร้าน เก็บเป็น “ตารางคู่” เสมอ',4)
def column(x,title,steps):
    cy=140
    prev=node(b,'terminator','start',x,cy,300,46,title,size=13.5)
    for (k,key,t,h,sz) in steps:
        cy=prev['b'][1]+34+h/2
        nd=node(b,k,key,x,cy,300,h,t,size=sz)
        arrow(b,prev['b'],nd['t'])
        prev=nd
    return prev
LX,RXc=215,580
column(LX,'บันทึก “รายจ่าย”',[
 ('manual','manual','กรอก: วันที่ • แหล่งซื้อ\nรายการของ • จำนวน • ราคา',62,12),
 ('io','io','ส่ง action = saveExpense',48,12.5),
 ('sub','sub','saveExpense()\nหาเลขแหล่งซื้อ (source_id)',56,12.5),
 ('db','db','เขียนหัวบิล\nexpense_transactions',56,12),
 ('db','db','เขียนรายการย่อยทีละชิ้น\nexpense_items',56,12),
 ('terminator','start','เสร็จ — คืนเลขบิล',46,12.5),
])
last=column(RXc,'บันทึก “รายรับ”',[
 ('manual','manual','มาจากปิดบิล POS อัตโนมัติ\nหรือกรอกเอง',56,12),
 ('io','io','ส่ง action = saveIncome',48,12.5),
 ('decision','decision','มีชื่อลูกค้านี้\nอยู่แล้ว?',80,12),
 ('db','db','เขียนหัวบิล\nincome_transactions',56,12),
 ('db','db','เขียนรายการย่อยทีละชิ้น\nincome_invoice_items',56,12),
 ('terminator','start','เสร็จ — คืนเลขบิล',46,12.5),
])
# หมายเหตุ customer ใหม่ ข้าง decision
plain(b,RXc-170,140+46+34+56+34+48+34+40,'ถ้ายังไม่มี → สร้างลูกค้าใหม่',size=10.5,color='#C62828',anchor='end')
plain(b,RXc-170,140+46+34+56+34+48+34+56,'ในตาราง customers ก่อน',size=10.5,color='#C62828',anchor='end')
# สรุปล่าง
rrect(b,40,H-150,W-80,92,'#E8F5E9','#43A047',1.2)
plain(b,56,H-118,'เห็นรูปแบบเดียวกันไหม?  ทั้งรายรับและรายจ่ายเก็บเป็น “ตารางคู่” เสมอ:',size=13.5,color='#22303A',bold=True)
plain(b,70,H-92,'• ตารางหัวบิล (transactions) = 1 แถวต่อ 1 บิล → เก็บวันที่ + ยอดรวม',size=12.5,color='#1B5E20',bold=True)
plain(b,70,H-68,'• ตารางรายการย่อย (items) = หลายแถวต่อ 1 บิล → เก็บของแต่ละชิ้น/จาน',size=12.5,color='#1B5E20',bold=True)
page_end(b)

# ════════════════════════════════════════════════════════════
# หน้า 5 : ตาราง action
# ════════════════════════════════════════════════════════════
b=page_start('คำสั่ง (action) ทั้งหมดที่ระบบรองรับ',
             'ทุกปุ่มบนหน้าจอ = ส่ง 1 action เข้า WebApp.js แล้ววิ่งไปฟังก์ชันใน Api.js',5)
groups=[
 ('โต๊ะ / ออเดอร์ (POS)','#1565C0',[
   ('getOpenSessions','ดึงโต๊ะที่เปิดค้างอยู่ + รายการอาหาร'),
   ('createSession','เปิดโต๊ะใหม่ (กันชื่อซ้ำ)'),
   ('addOrderItem','สั่งอาหารเข้าโต๊ะ'),
   ('updateItemStatus','เปลี่ยนสถานะจาน (เช่น เสิร์ฟแล้ว)'),
   ('removeOrderItem','ลบรายการอาหารออก'),
   ('closeSession','ปิดบิล → สร้างรายรับอัตโนมัติ'),
   ('deleteSession','ยกเลิกโต๊ะ (ห้ามลบถ้าจ่ายแล้ว)')]),
 ('เมนูอาหาร','#00838F',[
   ('getMenuItems / getMenuCategories','ดึงเมนูและหมวดหมู่'),
   ('saveMenuItem / updateMenuItem','เพิ่ม / แก้เมนู'),
   ('deleteMenuItem','ลบเมนู'),
   ('saveMenuCategory','เพิ่มหมวดหมู่'),
   ('getMenuImage(s) / syncMenuImages','จัดการรูปเมนู')]),
 ('เงิน: รายรับ-รายจ่าย','#6A1B9A',[
   ('saveExpense / updateExpense','บันทึก / แก้รายจ่าย'),
   ('saveIncome','บันทึกรายรับ'),
   ('getExpenseDescriptions','ดึงรายการของที่เคยซื้อ'),
   ('deleteTransaction','ลบบิลรายรับ/รายจ่าย')]),
 ('ประวัติ / รายงาน / ผู้ใช้','#EF6C00',[
   ('getHistory / getSummary','ดูประวัติ + ยอดสรุป'),
   ('getTransactionItems / searchItems','ดูรายการในบิล / ค้นหา'),
   ('getSalesReport / getMenuRankByPeriod','รายงานยอดขาย + เมนูขายดี'),
   ('getIngredientStock','ประเมินวัตถุดิบคงเหลือ'),
   ('getAdminByPin','ตรวจ PIN ตอนล็อกอิน')]),
]
y=120
for gname,gcol,rows in groups:
    rrect(b,40,y,W-80,28,gcol,gcol,0,rx=5)
    plain(b,52,y+19,gname,size=13,color='#fff',bold=True)
    y+=40
    for fn,desc in rows:
        plain(b,58,y,fn,size=12,color='#0D1B22',bold=True)
        plain(b,360,y,'— '+desc,size=12,color='#455A64')
        b.append(f'<line x1="52" y1="{y+8}" x2="{W-44}" y2="{y+8}" stroke="#E0E4E7" stroke-width="0.7"/>')
        y+=25
    y+=12
page_end(b)

# ════════════════════════════════════════════════════════════
# หน้า 6 : Legend
# ════════════════════════════════════════════════════════════
b=page_start('คำอธิบายสัญลักษณ์ผังงาน (Legend)',
             'สัญลักษณ์มาตรฐาน ANSI/ISO ที่ใช้ในเอกสารนี้ — รูปทรงคือสิ่งที่บอกความหมาย',6)
legend=[
 ('terminator','start','จุดเริ่มต้น / จุดสิ้นสุด','ทรงแคปซูล — บอกว่าเริ่มหรือจบการทำงาน (Terminator)'),
 ('process','process','ขั้นตอนการทำงานทั่วไป','สี่เหลี่ยมผืนผ้า — การประมวลผล 1 ขั้น (Process)'),
 ('sub','sub','เรียกฟังก์ชันสำเร็จรูป','สี่เหลี่ยมมีขีดข้างสองข้าง — เรียกฟังก์ชันที่นิยามไว้ เช่น closeSession() (Predefined process)'),
 ('decision','decision','การตัดสินใจ','ข้าวหลามตัด — จุดเลือกทาง ตอบ ใช่/ไม่ (Decision)'),
 ('io','io','รับ / ส่งข้อมูล','สี่เหลี่ยมด้านขนาน — ข้อมูลเข้า-ออกระหว่างระบบ (Input/Output)'),
 ('manual','manual','กรอกข้อมูลด้วยมือ','ขอบบนเฉียง — คนพิมพ์/กรอกข้อมูลเอง เช่น ใส่ PIN (Manual input)'),
 ('db','db','ฐานข้อมูล','ทรงกระบอก — อ่าน/เขียนข้อมูลใน Google Sheets (Database)'),
 ('doc','doc','เอกสาร / ใบเสร็จ','สี่เหลี่ยมก้นหยัก — ผลลัพธ์ที่เป็นเอกสาร เช่น ใบเสร็จ (Document)'),
]
y=130
for k,key,name,desc in legend:
    node(b,k,key,110,y,120,50,'')
    plain(b,195,y-6,name,size=15,color='#1A2327',bold=True)
    plain(b,195,y+16,desc,size=11.5,color='#455A64')
    b.append(f'<line x1="40" y1="{y+38}" x2="{W-40}" y2="{y+38}" stroke="#E0E4E7" stroke-width="0.7"/>')
    y+=78
# ลูกศร
y+=4
plain(b,40,y,'ความหมายของลูกศร',size=15,color='#1A2327',bold=True); y+=34
for cset,desc in [('#37474F','ทิศทางการไหลของงาน → ไปขั้นตอนถัดไป'),
                  ('#2E7D32','เส้นทาง “ใช่ / สำเร็จ”'),
                  ('#C62828','เส้นทาง “ไม่ / ผิดพลาด / ย้อนกลับ”')]:
    b.append(f'<line x1="70" y1="{y}" x2="170" y2="{y}" stroke="{cset}" stroke-width="2" marker-end="url(#a{_mid(cset)})"/>')
    plain(b,190,y+4,desc,size=12.5,color='#22303A'); y+=32
y+=10
rrect(b,40,y,W-80,64,'#FFFDE7','#FBC02D',1.2)
plain(b,56,y+26,'หมายเหตุ: สีช่วยให้กวาดตาดูง่าย แต่ “รูปทรง” คือสิ่งที่บอกความหมายตามมาตรฐาน',size=12.5,color='#22303A',bold=True)
plain(b,56,y+50,'เขียว=เริ่ม/จบ • น้ำเงิน/คราม=ทำงาน • ส้ม=ตัดสินใจ • ม่วง=ฐานข้อมูล • ฟ้าเขียว=รับส่งข้อมูล • น้ำตาล=กรอกมือ • ชมพู=เอกสาร',size=11,color='#455A64')
page_end(b)

# ─── ประกอบ HTML ──────────────────────────────────────────
markers=''.join(
 f'<marker id="a{i}" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto" markerUnits="userSpaceOnUse">'
 f'<path d="M0,0 L9,4.5 L0,9 Z" fill="{catlr}"/></marker>'
 for i,catlr in enumerate(ARROW_COLORS))

pages_html=[]
for svg in PAGES:
    pages_html.append(
      f'<div class="page"><svg width="210mm" height="297mm" viewBox="0 0 {W} {H}" '
      f'xmlns="http://www.w3.org/2000/svg"><defs>{markers}</defs>{svg}</svg></div>')

doc=('<!doctype html><html><head><meta charset="utf-8"><style>'
     '@page{size:A4 portrait;margin:0}*{margin:0;padding:0}'
     '.page{width:210mm;height:297mm;page-break-after:always;overflow:hidden}'
     '.page:last-child{page-break-after:auto}'
     '</style></head><body>'+''.join(pages_html)+'</body></html>')

path='/Users/admin/Developer/WalletRecord_Main/_flowchart.html'
open(path,'w',encoding='utf-8').write(doc)
print('saved html:',path)
