# 🚀 Vercel Deployment Guide

This full-stack application (FastAPI backend + Modern Interactive UI) is pre-configured and ready for 1-click deployment on [Vercel](https://vercel.com).

---

## 🛠️ Option 1: Deploy using Vercel CLI (Fastest - 1 minute)

### 1. Install Vercel CLI
If you don't already have the Vercel CLI installed, install it globally using npm:
```bash
npm install -g vercel
```

### 2. Login to Vercel
```bash
vercel login
```

### 3. Deploy
Navigate to the project root and run:
```bash
vercel
```
Follow the interactive prompts:
* **Set up and deploy?** $ightarrow$ `y`
* **Which scope do you want to deploy to?** $ightarrow$ (Select your Vercel account)
* **Link to existing project?** $ightarrow$ `n`
* **What's your project's name?** $ightarrow$ `health-ai-assistant`
* **In which directory is your code located?** $ightarrow$ `./`
* **Want to modify build settings?** $ightarrow$ `n`

### 4. Deploy to Production
```bash
vercel --prod
```
Your application will be live at: `https://health-ai-assistant-[your-username].vercel.app`! 🎉

---

## 🌐 Option 2: Deploy via GitHub (Recommended for CI/CD)

### 1. Push project to a GitHub repository
```bash
git init
git add .
git commit -m "feat: complete report-driven health AI assistant with Vercel deployment support"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/health-ai-assistant.git
git push -u origin main
```

### 2. Import into Vercel
1. Go to your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** $ightarrow$ **Project**.
3. Select and import your **`health-ai-assistant`** GitHub repository.
4. **Framework Preset**: Leave as **Other** (Vercel automatically detects `vercel.json` and `@vercel/python`).
5. **Root Directory**: Leave as `./`.
6. Click **Deploy**!

---

## 🔑 Environment Variables (Optional)

In your **Vercel Project Settings $ightarrow$ Environment Variables**, you can optionally set:
* `SECRET_KEY`: (A secure random string for JWT session signing)
* `FILE_ENCRYPTION_KEY`: (A 32-character string for document AES encryption)
* `DATABASE_URL`: *(Optional)* If you wish to use a persistent cloud PostgreSQL database (like [Neon.tech](https://neon.tech), [Supabase](https://supabase.com), or Railway), set the PostgreSQL connection string here (e.g. `postgresql+asyncpg://user:pass@host/dbname`). If omitted, it automatically uses the serverless SQLite configuration.
* `GEMINI_API_KEY`: *(Optional)* If you wish to enable Google Gemini clinical synthesis.

---

## ✅ Deployment Verification
Once deployed:
* **Homepage UI**: `https://your-domain.vercel.app/`
* **Interactive API Documentation**: `https://your-domain.vercel.app/docs`
* **Health Check**: `https://your-domain.vercel.app/api/v1/audit/logs`
