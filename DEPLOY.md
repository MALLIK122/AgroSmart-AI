# Deployment Guide: AgroSmart AI on Vercel + MongoDB Atlas

This guide walks you through deploying the Flask app to Vercel and setting up a free MongoDB Atlas database.

---

## Part 1: Set Up MongoDB Atlas (Database)

### Step 1: Create MongoDB Atlas Account
1. Go to https://www.mongodb.com/cloud/atlas
2. Click **"Sign Up"**
3. Fill in:
   - Email address
   - Password
   - Agree to terms
4. Click **"Create your Atlas account"**
5. Verify your email (check inbox)

### Step 2: Create a Free Cluster
1. After signing in, click **"Create a Deployment"**
2. Choose **"Free"** tier (M0)
3. Select your region (closest to your users):
   - Asia → **Singapore** or **Tokyo**
   - India → Select nearest region
4. Click **"Create Cluster"** (wait 2-3 minutes for creation)

### Step 3: Create Database User
1. Go to **"Database Access"** (left menu)
2. Click **"+ Add New Database User"**
3. Fill in:
   - **Username**: `agrosmart_user` (or any name)
   - **Password**: Create a STRONG password (copy it somewhere safe!)
   - Example: `MySecure123#Pass`
4. Click **"Add User"**
5. **IMPORTANT**: Copy the username & password somewhere safe

### Step 4: Allow Network Access
1. Go to **"Network Access"** (left menu)
2. Click **"+ Add IP Address"**
3. Click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - ⚠️ Only safe for development/demo; restrict for production
4. Click **"Confirm"**

### Step 5: Get Connection String
1. Go back to **"Clusters"** (left menu)
2. Click **"Connect"** button on your cluster
3. Choose **"Drivers"** → **"Python"**
4. Copy the connection string (looks like):
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. Replace `<username>` and `<password>` with your actual credentials

---

## Part 2: Prepare Your App for Deployment

### Step 1: Create `.env` File Locally
```bash
cd /home/mallikarjunks/Documents/Projects/Soil_Sense
cp .env.example .env
```

### Step 2: Edit `.env` with Your Values
```bash
# Open the .env file and fill in:
cat > .env << 'EOF'
# Flask
SECRET_KEY=your_random_secret_key_here_make_it_long
FLASK_DEBUG=0
FLASK_ENV=production

# MongoDB Atlas (from Step 5 above)
MONGO_URI=mongodb+srv://agrosmart_user:MySecure123#Pass@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=agrosmart_ai
EOF
```

**Replace:**
- `your_random_secret_key_here_make_it_long` → a random 32-character string
- `agrosmart_user` → your MongoDB username
- `MySecure123#Pass` → your MongoDB password
- `cluster0.xxxxx.mongodb.net` → your actual cluster URL

### Step 3: Test MongoDB Locally (Optional)
```bash
source .venv/bin/activate
python3 -c "
import os
from pymongo import MongoClient

uri = os.getenv('MONGO_URI')
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.server_info()
    print('✓ MongoDB connection successful!')
except Exception as e:
    print(f'✗ MongoDB connection failed: {e}')
"
```

### Step 4: Test App Locally
```bash
source .venv/bin/activate
python app.py
```
- Visit http://localhost:5000
- Sign up with test account
- Try a crop prediction
- Check that data appears in your profile

---

## Part 3: Deploy to Vercel

### Step 1: Install Vercel CLI
```bash
npm install -g vercel
# OR if npm not available:
# pip install vercel
```

### Step 2: Log In to Vercel
```bash
vercel login
# Follow the browser prompt to authenticate with your GitHub account
```

### Step 3: Deploy the App
```bash
cd /home/mallikarjunks/Documents/Projects/Soil_Sense
vercel --prod
```

When prompted:
- **Link to existing project?** → Say **No** (first deploy)
- **Project name?** → `agro-smart-ai` (or your choice)
- **Which scope?** → Select your account
- **Detected framework?** → Say **No**, enter `Other`
- **Root directory?** → Press Enter (`.`)

### Step 4: Set Environment Variables on Vercel
1. After deployment, go to https://vercel.com/dashboard
2. Click your project **"agro-smart-ai"**
3. Go to **"Settings"** → **"Environment Variables"**
4. Add these variables:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | (same as your `.env`) |
| `FLASK_ENV` | `production` |
| `MONGO_URI` | (your MongoDB connection string) |
| `MONGODB_DB_NAME` | `agrosmart_ai` |
| `FLASK_DEBUG` | `0` |

5. Click **"Save"** after each variable

### Step 5: Redeploy with Environment Variables
```bash
vercel --prod --env MONGO_URI=your_mongo_string --env SECRET_KEY=your_secret_key
```

Or redeploy from the Vercel dashboard:
1. Go to **"Deployments"**
2. Click the **3-dot menu** on the latest deployment
3. Click **"Redeploy"**

---

## Part 4: Disable Vercel Deployment Protection (Optional)

Your site might be behind Vercel's authentication wall. To make it public:

1. Go to Vercel Dashboard
2. Click your project
3. Go to **"Settings"** → **"Deployment Protection"**
4. Toggle **"Vercel Authentication"** to **OFF**
5. Save changes
6. Redeploy

---

## Part 5: Verify Deployment

### Test the Live Site
```bash
# Replace with your actual Vercel URL
curl -i https://agro-smart-ai-yourusername.vercel.app/
```

### Check Health Endpoint
```bash
curl https://agro-smart-ai-yourusername.vercel.app/api/health
```

Expected response:
```json
{"ok": true, "mongo": true, "model_loaded": true}
```

### Manual Testing
1. Open your Vercel URL in a browser
2. Sign up with a test account
3. Enter N=50, P=40, K=60, pH=6.5
4. Submit and see crop recommendation
5. Check your profile for saved predictions

---

## Part 6: Troubleshooting

### Problem: "Connection Refused" Error
**Solution:**
- Check MongoDB IP whitelist allows `0.0.0.0/0`
- Verify `MONGO_URI` spelling (copy-paste from MongoDB Atlas)
- Test locally: `python3 test_auth.py`

### Problem: "503 Bad Gateway"
**Solution:**
- Check Vercel function logs: Dashboard → Deployments → View logs
- Ensure all environment variables are set
- Try redeploying

### Problem: "Model not loaded"
**Solution:**
- App will use fallback recommendation algorithm (built-in)
- This is OK for deployment; model files are local

### Problem: Crop predictions not saving
**Solution:**
- Verify `MONGO_URI` is correct
- Check MongoDB Atlas network access (whitelist 0.0.0.0/0)
- Redeploy with correct env vars

---

## Part 7: Future Updates

### To Update Code
```bash
# Make your code changes locally
git add .
git commit -m "Your changes"
git push origin main

# Redeploy to Vercel
vercel --prod
```

### To Update MongoDB Connection
1. Go to MongoDB Atlas
2. Create a new user with stronger password
3. Update `MONGO_URI` in Vercel environment variables
4. Redeploy

---

## Quick Commands Cheatsheet

```bash
# Local setup
cp .env.example .env
source .venv/bin/activate
pip install -r requirements.txt
python app.py

# Test MongoDB
python3 -c "from pymongo import MongoClient; MongoClient('your_uri').server_info(); print('OK')"

# Deploy to Vercel
vercel login
vercel --prod

# View Vercel logs
vercel logs agro-smart-ai --tail

# Check deployment status
curl https://your-vercel-url.vercel.app/api/health
```

---

## Summary

✓ MongoDB Atlas database ready  
✓ Environment variables configured  
✓ App deployed to Vercel  
✓ Predictions saved to cloud database  
✓ Live at: `https://your-project.vercel.app`

**Your website is now live and can handle real users!**
