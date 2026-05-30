# Soil Sense — How to Run

Follow these steps from the project folder (`Soil_Sense`).

## Step 1: Install Python

You need **Python 3.11 or newer** and `pip`.

Check your version:

```bash
python3 --version
```

## Step 2: Open the project folder

```bash
cd /path/to/Soil_Sense
```

Replace `/path/to/Soil_Sense` with the folder where you cloned or downloaded this project.

## Step 3: Create a virtual environment

```bash
python3 -m venv .venv
```

## Step 4: Activate the virtual environment

**Linux / macOS:**

```bash
source .venv/bin/activate
```

**Windows (Command Prompt):**

```cmd
.venv\Scripts\activate
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

Your shell prompt should show `(.venv)` when the environment is active.

## Step 5: Install dependencies

```bash
pip install -r requirements.txt
```

## Step 6: (Optional) Configure MongoDB

The app runs without MongoDB and uses in-memory storage.

For **persistent** history, either:

- Start MongoDB locally and set:

```bash
export MONGO_URI="mongodb://localhost:27017/"
```

- Or copy `.env.example` to `.env`, add your Atlas connection string, and set `MONGO_URI` there.

```bash
cp .env.example .env
```

Edit `.env` with your values, then run the app from the same terminal (Step 7).

## Step 7: Start the server

**Option A — start script (Linux / macOS):**

```bash
chmod +x start.sh
./start.sh
```

**Option B — manual start:**

```bash
source .venv/bin/activate
python app.py
```

Leave this terminal open while you use the site. Press **Ctrl+C** to stop the server.

## Step 8: Open the website

In your browser, go to:

```
http://127.0.0.1:5000
```

If you see **Connection refused**, the server is not running — repeat Step 7 and keep that terminal open.

## Step 9: Log in

Use one of the default accounts (created automatically on first run):

| Username | Password   | Role   |
|----------|------------|--------|
| `farmer` | `farmer123` | Farmer |
| `admin`  | `admin123`  | Admin  |

Or register a new account at **Sign up**, then log in.

## Step 10: Use the app

1. On the home page, enter soil values and click **Predict Suitable Crop**.
2. View results, dashboard history, and the chat advisor.
3. Open **Profile** to see past predictions and download CSV/Excel exports.

## Step 11: Deploy on Vercel with MongoDB Atlas

1. Push your project to GitHub.
2. Create a Vercel account and connect your GitHub repository.
3. In Vercel, create a new project from your repository.
4. Set the environment variables in the Vercel dashboard:
   - `SECRET_KEY` = a random long secret
   - `MONGO_URI` = your Atlas connection string
   - `MONGODB_DB_NAME` = `agrosmart_ai`
   - `FLASK_ENV` = `production`
5. Make sure Vercel deploys using the `Dockerfile` in your repo.
6. Wait for the deployment to finish, then open the Vercel URL.

### Notes for Vercel deployment
- This project uses a Flask backend and is deployed via Docker.
- `app.py` reads `PORT` from the environment, so Vercel can bind correctly.
- MongoDB Atlas must allow access from your deployed app (use `0.0.0.0/0` or proper IP access rules).
- Keep `crop_recommender.pkl` and `label_classes.pkl` in the repo so the model loads successfully.

### Quick Vercel checklist
- `Dockerfile` exists in project root
- `vercel.json` exists in project root
- `requirements.txt` is up to date
- Vercel env vars are set correctly
- `FLASK_ENV` is `production`
4. As **admin**, open **Admin** to reload or upload model files.

---

**Quick reference (after setup):**

```bash
cd /path/to/Soil_Sense
source .venv/bin/activate
python app.py
```

Then open http://127.0.0.1:5000
