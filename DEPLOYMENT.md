# Deploying app.py - Deployment Guide

## ✅ Pre-Deployment Checklist

- [x] No syntax errors in app.py
- [x] requirements.txt present with all dependencies
- [x] API_BASE_URL configured via environment variable
- [x] Secrets handled via st.secrets
- [x] .streamlit/config.toml created
- [x] .streamlit/secrets.toml.example provided

## 🚀 Deployment Options

### Option 1: Streamlit Cloud (Recommended)

**Prerequisites:**
- GitHub account
- Backend API deployed and accessible (https://vivek45537-dpklnt.hf.space)

**Steps:**

1. **Push to GitHub** (Already done ✅)
   ```bash
   git push
   ```

2. **Deploy to Streamlit Cloud**
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select your repository: `Vivekkumar0045/ayaanlnt`
   - Branch: `main`
   - Main file path: `app.py`
   - Click "Deploy"

3. **Configure Secrets**
   - In Streamlit Cloud dashboard, go to App Settings
   - Navigate to "Secrets" section
   - Add:
     ```toml
     GOOGLE_API_KEY = "your-gemini-api-key"
     ```

4. **Configure Environment Variables** (Optional)
   - If your backend URL changes, set:
     ```toml
     API_BASE_URL = "https://your-backend-url.com"
     ```

**Current Backend URL:** `https://vivek45537-dpklnt.hf.space`

---

### Option 2: Hugging Face Spaces

**Steps:**

1. **Create new Space**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Select "Streamlit" as SDK
   - Name your space

2. **Upload files**
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE
   cd YOUR_SPACE
   
   # Copy files
   cp /path/to/app.py .
   cp /path/to/requirements.txt .
   cp -r /path/to/.streamlit .
   
   git add .
   git commit -m "Deploy Precast AI Optimizer"
   git push
   ```

3. **Configure Secrets**
   - In Space settings, add secrets:
     - `GOOGLE_API_KEY`

---

### Option 3: Docker Deployment

**Prerequisites:**
- Docker installed
- Backend API running

**Steps:**

1. **Create Dockerfile** (in project root):
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY app.py .
   COPY .streamlit .streamlit
   
   EXPOSE 8501
   
   CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **Build and run**:
   ```bash
   docker build -t precast-frontend .
   docker run -p 8501:8501 \
     -e API_BASE_URL=https://vivek45537-dpklnt.hf.space \
     -e GOOGLE_API_KEY=your-key \
     precast-frontend
   ```

---

### Option 4: Heroku

**Steps:**

1. **Create files**:

   `Procfile`:
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

   `runtime.txt`:
   ```
   python-3.11.7
   ```

2. **Deploy**:
   ```bash
   heroku create your-app-name
   heroku config:set API_BASE_URL=https://vivek45537-dpklnt.hf.space
   heroku config:set GOOGLE_API_KEY=your-key
   git push heroku main
   ```

---

### Option 5: Railway

**Steps:**

1. **Connect GitHub repo**
   - Go to https://railway.app
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `Vivekkumar0045/ayaanlnt`

2. **Configure**
   - Railway auto-detects Streamlit
   - Add environment variables:
     - `API_BASE_URL`: `https://vivek45537-dpklnt.hf.space`
     - `GOOGLE_API_KEY`: Your Gemini API key

3. **Deploy**
   - Click "Deploy"

---

## 🔧 Environment Variables

### Required:
- **None** (Has sensible defaults)

### Optional:
- `API_BASE_URL`: Backend API URL (default: `https://vivek45537-dpklnt.hf.space`)
- `GOOGLE_API_KEY`: For AI Report feature (can be added via Streamlit secrets)

---

## 🔐 Secrets Configuration

### For Streamlit Cloud / Hugging Face:

Add to Secrets section:
```toml
GOOGLE_API_KEY = "AIzaSy..."
```

### For Docker / Heroku / Railway:

Set as environment variable:
```bash
export GOOGLE_API_KEY="AIzaSy..."
```

Or pass in docker run:
```bash
docker run -e GOOGLE_API_KEY="AIzaSy..." ...
```

---

## 📋 Pre-Flight Check

Before deploying, verify:

1. **Backend is accessible**
   ```bash
   curl https://vivek45537-dpklnt.hf.space/health
   ```
   Should return: `{"status":"healthy","models_loaded":true,...}`

2. **Dependencies install correctly**
   ```bash
   pip install -r requirements.txt
   ```

3. **App runs locally**
   ```bash
   streamlit run app.py
   ```

4. **API connection works**
   - Open app
   - Should see baseline performance metrics
   - Click "Run Optimiser" - should work without errors

---

## 🐛 Troubleshooting

### "Cannot connect to API backend"

**Cause:** Backend not accessible or wrong URL

**Fix:**
1. Verify backend is running: `curl https://vivek45537-dpklnt.hf.space/health`
2. Check `API_BASE_URL` environment variable
3. Ensure no firewall blocking requests

### "API key not configured"

**Cause:** Missing GOOGLE_API_KEY in secrets

**Fix:**
- Streamlit Cloud: Add to Secrets section
- Docker: Pass as environment variable `-e GOOGLE_API_KEY=...`
- Local: Add to `.streamlit/secrets.toml`

### Module import errors

**Cause:** Missing dependencies

**Fix:**
1. Verify `requirements.txt` is complete
2. Clear cache and reinstall: `pip install --force-reinstall -r requirements.txt`

### Slow batch predictions

**Cause:** Backend timeout or too many combinations

**Fix:**
1. Reduce number of combinations in sidebar
2. Increase timeout in API calls (edit app.py line ~100)
3. Scale up backend server

---

## 📊 Performance Tips

1. **Cache API responses** - Already implemented ✅
2. **Limit combinations** - Start with 100-1000 for testing
3. **Use batch endpoint** - Already implemented ✅
4. **Monitor backend health** - Check `/health` endpoint regularly

---

## ✅ Deployment-Ready Status

**app.py is READY for deployment!** ✅

All requirements are met:
- ✅ No errors
- ✅ Dependencies documented
- ✅ Secrets handled securely
- ✅ Environment variables supported
- ✅ Backend connection configured
- ✅ Production config ready

**Recommended Next Step:**
Deploy to Streamlit Cloud for easiest deployment.

---

## 📞 Support

If deployment issues occur:
1. Check backend health: https://vivek45537-dpklnt.hf.space/docs
2. Review Streamlit logs
3. Verify all environment variables are set
4. Test API connection manually

---

**Happy Deploying! 🚀**
