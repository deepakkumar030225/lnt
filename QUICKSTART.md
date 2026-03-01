# QUICK START GUIDE

## 🚀 Get Started in 3 Steps

### Step 1️⃣: Start the Backend API (Terminal 1)

```powershell
cd backend
python main.py
```

Wait for this message:
```
✓ Loaded 3 models successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2️⃣: Start the Streamlit Frontend (Terminal 2)

Open a **NEW terminal** and run:

```powershell
streamlit run app.py
```

The app will open automatically in your browser at http://localhost:8501

### Step 3️⃣: Start Optimizing!

1. 🏗️ Configure parameters in the sidebar
2. ⚡ Click "✨ Run Optimiser"
3. 📊 View results and recommendations

---

## 🎯 Quick Test

### Test Backend API

Open browser to: http://localhost:8000/docs

Try the `/health` endpoint to verify models are loaded.

### Test Full Stack

1. In the Streamlit app, check if you see:
   - ✅ Green "Connected" status
   - 📊 Baseline performance metrics
   
2. Click "✨ Run Optimiser" with default values

3. You should see optimization results in ~10 seconds

---

## 🐛 Common Issues

### "Cannot connect to API backend"

**Fix:** Make sure Step 1 is complete and backend shows "Loaded 3 models"

### "Models not loaded"

**Fix:** Run the training notebook first:
```
jupyter notebook precast_phase_01.ipynb
```
Then restart the backend.

### Port Already in Use

**Fix:** Kill existing processes or use different ports:
```powershell
# Use different backend port
cd backend
uvicorn main:app --port 8001

# Update frontend to use new port
$env:API_BASE_URL = "http://localhost:8001"
streamlit run app.py
```

---

## 🎨 One-Command Start (PowerShell)

Use the helper script:

```powershell
.\start.ps1
```

This automatically starts both backend and frontend.

---

**Happy Optimizing! 🏭✨**
