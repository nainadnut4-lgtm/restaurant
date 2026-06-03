---
name: deploy
description: Deploy WalletRecord to Google Apps Script and push backup to GitHub. Always run in this exact order — clasp push → clasp deploy → git commit → git push. GitHub index.html must stay as a simple redirect page (never the GAS template). Trigger on /deploy or whenever user says "deploy", "push ขึ้น", "อัปเดต".
---

# Deploy — WalletRecord

ทำตามลำดับนี้เสมอ ห้ามข้ามขั้นตอน

## 1. Push ขึ้น Google Apps Script

```bash
export PATH="$HOME/.npm-global/bin:$PATH"
clasp push
```

## 2. Deploy (อัปเดต deployment เดิม — URL ไม่เปลี่ยน)

```bash
clasp deploy \
  --deploymentId "AKfycbzoq2MF_L95c-rBv4NLjJRgcCavclL1BradjNwwB45YtudC4XRDuCQ49XFOJwecEtE" \
  --description "Fix/Feature: ..."
```

## 3. Backup ขึ้น GitHub

```bash
git add -A
git commit -m "Deploy @XX: ..."
git push origin main
```

---

## กฎสำคัญ — GitHub index.html

> ⚠️ `index.html` ใน local project คือ GAS app template (1400+ บรรทัด)
> ถูก `.gitignore` อยู่แล้ว — **ห้าม push ขึ้น GitHub**

GitHub ต้องการแค่ redirect page เรียบง่าย:

```html
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="refresh" content="0; url=https://script.google.com/macros/s/AKfycbzoq2MF_L95c-rBv4NLjJRgcCavclL1BradjNwwB45YtudC4XRDuCQ49XFOJwecEtE/exec" />
  <script>window.location.replace("https://script.google.com/macros/s/AKfycbzoq2MF_L95c-rBv4NLjJRgcCavclL1BradjNwwB45YtudC4XRDuCQ49XFOJwecEtE/exec");</script>
</head>
<body><a href="...">เปิดหน้าเว็บ</a></body>
</html>
```

ถ้า GitHub index.html หายหรือผิด ให้:
1. เขียน redirect page ลงไฟล์ชั่วคราว
2. `git add -f index.html`
3. `git commit && git push`
4. คืน GAS template กลับมา

---

## Deployment Info

| Key | Value |
|-----|-------|
| Deployment ID | `AKfycbzoq2MF_L95c-rBv4NLjJRgcCavclL1BradjNwwB45YtudC4XRDuCQ49XFOJwecEtE` |
| Web App URL | `https://script.google.com/macros/s/AKfycbzoq2MF_L95c-rBv4NLjJRgcCavclL1BradjNwwB45YtudC4XRDuCQ49XFOJwecEtE/exec` |
| GitHub repo | `https://github.com/nainadnut4-lgtm/restaurant` |
| clasp path | `~/.npm-global/bin/clasp` (ต้อง export PATH ทุกครั้ง) |
