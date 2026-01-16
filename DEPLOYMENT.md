# 🚀 Deploy to Render.com (FREE)

## Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/text-to-sql.git
git push -u origin main
```

## Step 2: Deploy on Render

1. Go to [render.com](https://render.com) and sign up (free)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `text-to-sql`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `Dockerfile.api`
   - **Plan**: `Free`

5. Add Environment Variables:
   - `GROQ_API_KEY`: Your Groq API key
   - `DATABASE_URL`: (Will add PostgreSQL next)

6. Click **"Create Web Service"**

## Step 3: Add PostgreSQL Database

1. In Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `text-to-sql-db`
   - **Plan**: `Free`
3. Click **"Create Database"**
4. Copy the **Internal Database URL**
5. Go back to your Web Service → **Environment** → Update `DATABASE_URL`

## Step 4: Get Your Live URL

Your app will be live at: `https://text-to-sql-XXXX.onrender.com`

## ⚠️ Important Notes

- **First load takes 50 seconds** (free tier spins down after inactivity)
- **Database expires after 90 days** (just re-create it)
- **Perfect for portfolio/CV** - recruiters can access it!

## 🎯 For Your CV

Add this to your CV:
```
🔗 Live Demo: https://your-app.onrender.com
🔗 GitHub: https://github.com/yourusername/text-to-sql
```

---

**Alternative: Use Railway.app or Fly.io if Render doesn't work**
