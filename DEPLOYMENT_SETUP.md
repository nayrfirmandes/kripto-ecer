# 🚀 Deployment Setup Guide: Railway + Vercel

## 📋 Overview
- **Bot Backend:** Railway (Python + Prisma)
- **Admin Panel:** Vercel (Next.js)
- **Database:** NeonSQL (External PostgreSQL)

---

## 🚂 1. Setup Railway (Bot Backend)

### Step 1: Prepare GitHub
```bash
# Push code ke GitHub (jika belum)
git add .
git commit -m "Setup deployment configs for Railway"
git push
```

### Step 2: Connect Railway
1. Buka https://railway.app
2. Klik **"New Project"**
3. Pilih **"Deploy from GitHub repo"**
4. Select repo Anda
5. Railway akan auto-detect `Dockerfile` dan `railway.json`

### Step 3: Set Environment Variables di Railway
Dashboard Railway → Settings → Environment
```
TELEGRAM_BOT_TOKEN=7981158644:AAG93vQUnkEvaGoEmHVJdGb6qH0gnKDXRcs
BOT_DATABASE=postgresql://neondb_owner:npg_3BtMkjUAuvI7@ep-winter-block-a1m7jlv8-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
OXAPAY_PAYOUT_API_KEY=LIQDCG-FJTOQC-KRMD7L-WSVSY3
OXAPAY_MERCHANT_API_KEY=KBWAPC-I7WLYE-T803K6-IBSLZQ
OXAPAY_WEBHOOK_SECRET=your_webhook_secret
ADMIN_TELEGRAM_IDS=998181835
CRYPTOBOT_API_TOKEN=472202:AAdquyhT25eJRT1mWEowVtsSvxunybA3jVm
DEBUG=true
WEBHOOK_URL=https://your-railway-domain.railway.app
WEBHOOK_PATH=/telegram/webhook
WEBHOOK_PORT=8080
```

### Step 4: Deployment Process
Railway akan:
1. ✅ Build Docker image
2. ✅ Generate Prisma Python client (`prisma generate`)
3. ✅ Install dependencies dari `requirements.txt`
4. ✅ Start bot dengan `python run_bot.py`

**Important:** Railway akan otomatis assign domain. Update `WEBHOOK_URL` di environment vars dengan domain yang diberikan.

---

## ✨ 2. Setup Vercel (Admin Panel)

### Step 1: Connect GitHub to Vercel
1. Buka https://vercel.com
2. Klik **"New Project"**
3. Select GitHub repo Anda
4. Vercel auto-detect Next.js project

### Step 2: Configure Settings
Di Project Settings → General:
- **Framework:** Next.js (auto-detected)
- **Build Command:** `cd admin && npm run build && npx prisma@5.22.0 generate --schema=./prisma/schema.prisma`
- **Output Directory:** `admin/.next`
- **Install Command:** `cd admin && npm install`

### Step 3: Set Environment Variables di Vercel
Environment Variables section:
```
DATABASE_URL=postgresql://neondb_owner:npg_3BtMkjUAuvI7@ep-winter-block-a1m7jlv8-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

### Step 4: Deploy
Vercel akan:
1. ✅ Install dependencies
2. ✅ Generate Prisma JS client
3. ✅ Build Next.js app
4. ✅ Deploy ke global CDN

---

## 🔐 Environment Variables Summary

### DATABASE_URL
Same value untuk Railway dan Vercel (sudah ada di .env):
```
postgresql://neondb_owner:npg_3BtMkjUAuvI7@ep-winter-block-a1m7jlv8-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

### Telegram Bot Token
```
7981158644:AAG93vQUnkEvaGoEmHVJdGb6qH0gnKDXRcs
```

### API Keys
- `OXAPAY_PAYOUT_API_KEY`
- `OXAPAY_MERCHANT_API_KEY`
- `OXAPAY_WEBHOOK_SECRET`
- `CRYPTOBOT_API_TOKEN`

---

## ✅ Prisma Handling (PENTING!)

### Apa Masalahnya?
Prisma needs to generate platform-specific clients:
- **Python Prisma:** For bot (Railway)
- **JS Prisma:** For admin panel (Vercel)

### Solusinya?
```
✅ Dockerfile → `prisma generate --schema=prisma/schema.prisma`
✅ admin/package.json build → `npx prisma generate --schema=./prisma/schema.prisma && next build`
✅ Vercel config → auto-run during build
```

Jadi Prisma clients akan di-generate otomatis saat deployment.

---

## 🧪 Testing Sebelum Deploy

```bash
# Test build admin panel locally
cd admin
npm install
npm run build

# Test build bot locally
python -m pip install -r bot/requirements.txt
npx prisma generate --schema=prisma/schema.prisma
python run_bot.py
```

---

## 📌 Important Notes

1. **Database Connection:**
   - NeonSQL sudah external, no issue dengan Prisma migration
   - Both Railway dan Vercel bisa connect ke same database

2. **Webhook URL:**
   - Railway akan assign URL automatik
   - Update `WEBHOOK_URL` env var dengan Railway domain
   - Bot akan update Telegram webhook otomatis saat start

3. **Cost:**
   - Railway: $5 free credit/month (cukup untuk bot 24/7)
   - Vercel: Gratis untuk admin panel
   - Total: ~$0-5/month

4. **Auto-Deploy:**
   - Setiap push ke GitHub → auto-deploy (Railway + Vercel)
   - No manual deploy needed

---

## 🚨 Troubleshooting

### Bot tidak start di Railway?
- Check logs di Railway dashboard
- Pastikan env vars semua terisi
- Verify `Dockerfile` terbaca

### Admin panel build error di Vercel?
- Check "Build Logs" di Vercel dashboard
- Pastikan `vercel.json` config correct
- Verify Prisma generate berhasil

### Database connection error?
- Verify `BOT_DATABASE` / `DATABASE_URL` value
- Cek NeonSQL masih active
- Test connection locally dulu

---

## 🎯 Deployment Checklist

- [ ] Code pushed ke GitHub
- [ ] Railway connected dan env vars set
- [ ] Vercel connected dan env vars set
- [ ] Railway deployment berhasil (check logs)
- [ ] Vercel deployment berhasil (check logs)
- [ ] Bot Telegram webhook updated (check bot start)
- [ ] Admin panel accessible via Vercel URL
- [ ] Database connectivity verified
