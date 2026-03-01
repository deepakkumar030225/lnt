# 🐳 Docker Deployment Guide

This guide explains how to build and run the Precast AI Optimizer backend using Docker.

---

## 📋 Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)
- Model files in `models/` directory

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

The API will be available at **http://localhost:8000**

### Option 2: Docker CLI

```bash
# Build the image
docker build -t precast-backend .

# Run the container
docker run -d \
  --name precast-backend \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models:ro \
  precast-backend

# View logs
docker logs -f precast-backend

# Stop the container
docker stop precast-backend
docker rm precast-backend
```

---

## 🔧 Configuration

### Environment Variables

You can pass environment variables to customize the behavior:

```bash
docker run -d \
  --name precast-backend \
  -p 8000:8000 \
  -e LOG_LEVEL=debug \
  -e WORKERS=4 \
  precast-backend
```

Or with docker-compose, add to `docker-compose.yml`:

```yaml
environment:
  - LOG_LEVEL=debug
  - WORKERS=4
```

### Port Configuration

To use a different port, modify the port mapping:

```bash
# Use port 8080 instead
docker run -d -p 8080:8000 precast-backend
```

Or in docker-compose.yml:
```yaml
ports:
  - "8080:8000"
```

---

## 📊 Health Check

The Docker container includes a health check that verifies the API is responding:

```bash
# Check container health
docker ps
# Look for "healthy" in the STATUS column

# Manual health check
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "models_loaded": true,
  "available_targets": ["Time_to_demould", "Cycle_time", "Total_cost"]
}
```

---

## 🔍 Troubleshooting

### Models Not Loading

**Error:** `Models not loaded` in health check

**Solution:** Ensure all model files are in the `models/` directory:
```bash
ls -la models/
# Should show:
# - precast_pipeline.pkl
# - precast_meta.json
# - model_Time_to_demould.pkl
# - model_Cycle_time.pkl
# - model_Total_cost.pkl
```

### Port Already in Use

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:** Stop the conflicting process or use a different port:
```bash
# Use port 8001
docker run -d -p 8001:8000 precast-backend
```

### Container Exits Immediately

**Solution:** Check logs for errors:
```bash
docker logs precast-backend
```

Common issues:
- Missing dependencies → rebuild image
- Missing model files → check models/ directory
- Syntax errors → check main.py

### Permission Denied

**Error:** Permission errors when accessing models

**Solution:** The container runs as user ID 1000. Ensure files are readable:
```bash
# On Linux/Mac
chmod -R 755 models/
```

---

## 🚀 Production Deployment

### Multi-Worker Setup

For better performance in production, use multiple workers:

**Dockerfile:**
```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Or dynamically:
```bash
docker run -d \
  -p 8000:8000 \
  precast-backend \
  uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Resource Limits

Limit CPU and memory usage:

```bash
docker run -d \
  --name precast-backend \
  -p 8000:8000 \
  --memory="2g" \
  --cpus="2.0" \
  precast-backend
```

Or in docker-compose.yml:
```yaml
services:
  backend:
    # ... other settings ...
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### Restart Policy

Ensure the container restarts on failure:

```bash
docker run -d \
  --name precast-backend \
  -p 8000:8000 \
  --restart unless-stopped \
  precast-backend
```

---

## 🌐 Cloud Deployment

### AWS Elastic Container Service (ECS)

1. Push image to ECR:
```bash
# Tag and push
docker tag precast-backend:latest <account>.dkr.ecr.<region>.amazonaws.com/precast-backend:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/precast-backend:latest
```

2. Create ECS task definition using the image
3. Create ECS service with Application Load Balancer

### Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/<project>/precast-backend

# Deploy to Cloud Run
gcloud run deploy precast-backend \
  --image gcr.io/<project>/precast-backend \
  --platform managed \
  --port 8000 \
  --allow-unauthenticated
```

### Azure Container Instances

```bash
# Login to Azure
az login

# Create resource group
az group create --name precast-rg --location eastus

# Deploy container
az container create \
  --resource-group precast-rg \
  --name precast-backend \
  --image precast-backend:latest \
  --dns-name-label precast-api \
  --ports 8000
```

### Heroku

Using `heroku.yml`:

```yaml
build:
  docker:
    web: Dockerfile
run:
  web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Deploy:
```bash
heroku create precast-backend
heroku stack:set container
git push heroku main
```

---

## 🧪 Testing the Docker Container

### Basic Test

```bash
# Start container
docker-compose up -d

# Wait for startup
sleep 5

# Test health endpoint
curl http://localhost:8000/health

# Test prediction
curl -X POST http://localhost:8000/predict/single \
  -H "Content-Type: application/json" \
  -d '{
    "Ambient_temp_C": 30,
    "Cement_type": "OPC",
    "Cement_content_kgm3": 380,
    "Water_cement_ratio": 0.40,
    "Curing_method": "steam",
    "Steam_temp_C": 60,
    "Steam_duration_hr": 6
  }'
```

### Load Test

```bash
# Install Apache Bench
# Ubuntu: sudo apt-get install apache2-utils
# Mac: brew install ab

# Send 1000 requests with 10 concurrent connections
ab -n 1000 -c 10 -p test_payload.json -T application/json \
  http://localhost:8000/predict/single
```

---

## 📦 Image Optimization

### Multi-Stage Build

For smaller images, use multi-stage builds:

```dockerfile
# Builder stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
WORKDIR /app
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Check Image Size

```bash
docker images precast-backend
# Look for the SIZE column
```

---

## 🛡️ Security Best Practices

1. **Non-root user**: ✅ Already configured (user ID 1000)
2. **Read-only models**: ✅ Mounted as read-only in docker-compose
3. **Minimal base image**: ✅ Using python:3.11-slim
4. **No secrets in image**: ⚠️ Don't include API keys in the image
5. **Security scanning**: Run `docker scan precast-backend`

---

## 📝 Useful Commands

```bash
# Build without cache
docker build --no-cache -t precast-backend .

# Enter running container
docker exec -it precast-backend bash

# View resource usage
docker stats precast-backend

# Inspect container
docker inspect precast-backend

# Export image
docker save precast-backend:latest | gzip > precast-backend.tar.gz

# Import image
docker load < precast-backend.tar.gz
```

---

## 🔄 Update Workflow

### Update Model Files

```bash
# Models are mounted as volume, so just replace files
cp new_models/* models/

# Restart container to reload
docker-compose restart
```

### Update Code

```bash
# Rebuild image
docker-compose build

# Restart with new image
docker-compose up -d
```

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [FastAPI with Docker](https://fastapi.tiangolo.com/deployment/docker/)
- [Best Practices for Python Docker Images](https://docs.docker.com/language/python/build-images/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Container is running: `docker ps`
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] API docs accessible: `http://localhost:8000/docs`
- [ ] Single prediction works
- [ ] Batch prediction works
- [ ] Logs show no errors: `docker logs precast-backend`
- [ ] Models loaded successfully

---

**Ready for Docker deployment! 🐳🚀**
