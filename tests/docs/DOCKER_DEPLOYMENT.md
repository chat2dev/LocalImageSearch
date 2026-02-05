# Docker Deployment Verification Guide

This guide provides a complete Docker-based sandbox environment to verify that the deployment instructions in README.md are accurate and working.

## Overview

The Docker setup includes:
- **Ollama service**: Local LLM inference engine
- **Application container**: Python environment with all dependencies
- **Automated testing**: Complete deployment verification workflow

## Prerequisites

- Docker 20.10+
- Docker Compose 1.29+
- At least 8GB RAM
- ~5GB disk space (for Ollama and model)

## Quick Start

### 1. Run the automated test script

```bash
./docker-test.sh
```

This script will:
1. Check Docker and Docker Compose installation
2. Clean up any existing containers
3. Build Docker images from scratch
4. Start Ollama and application services
5. Download qwen3-vl:4b model
6. Run end-to-end deployment verification
7. Display test results

### 2. Manual deployment (alternative)

If you prefer to run commands manually:

```bash
# Build and start services
docker-compose up --build

# In another terminal, check logs
docker-compose logs -f app

# Stop services
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v
```

## What Gets Tested

The Docker deployment verification tests the following steps from README.md:

### Step 1: Environment Setup
- ✓ Python 3.11 installation
- ✓ uv package manager installation
- ✓ Dependency installation via `uv sync`

### Step 2: Ollama Service
- ✓ Ollama service startup
- ✓ Ollama API connectivity
- ✓ Model download (qwen3-vl:4b)

### Step 3: Application Functionality
- ✓ Test image creation
- ✓ Image tagging with Chinese language
- ✓ Database record creation
- ✓ Tag generation and storage

### Step 4: Verification
- ✓ Database query functionality
- ✓ Tag quality check
- ✓ Language setting verification

## Expected Output

When successful, you should see output similar to:

```
========================================
Image Auto-Tagging System - Docker Test
========================================

Step 1: Verifying uv installation...
uv 0.7.21

Step 2: Verifying Python dependencies...
✓ All dependencies installed

Step 3: Checking Ollama connection...
✓ Ollama service is ready

Step 4: Pulling qwen3-vl:4b model (this may take a while)...
✓ Model downloaded

Step 5: Creating test image...
✓ Test image created: test_images/test_blue.jpg

Step 6: Running image tagging (following README instructions)...
============================================================
图片自动标注系统
============================================================
Config:
  Model: qwen3-vl:4b
  Model Type: ollama
  Image Path: test_images/test_blue.jpg
  Resize: 512x512
  Tag Count: 5
  Language: zh
============================================================
找到 1 个图片文件

处理进度: 100%|██████████| 1/1
Successfully processed: test_images/test_blue.jpg
Tags: 蓝色背景, 纯色图片, 简约风格, 背景图, 渐变色

Step 7: Verifying database...
✓ Database contains 1 record(s)
  Image: test_images/test_blue.jpg
  Tags: 蓝色背景, 纯色图片, 简约风格, 背景图, 渐变色
  Language: zh

========================================
✓ All tests passed!
Deployment verification successful.
========================================
```

## Docker Configuration Files

### Dockerfile

Builds the application container:
- Base: Python 3.11-slim
- Installs uv package manager
- Copies project files
- Runs `uv sync` to install dependencies

### docker-compose.yml

Orchestrates two services:
- **ollama**: Ollama inference service (port 11434)
- **app**: Application container with automated test script

### .dockerignore

Excludes unnecessary files from Docker build:
- Virtual environments (.venv/)
- Data files (data/, models/)
- IDE files (.vscode/, .idea/)
- Build artifacts

## Troubleshooting

### Issue: "Cannot connect to Ollama"

**Solution**: Wait for Ollama service to fully start (30-60 seconds)

```bash
# Check Ollama service status
docker-compose logs ollama

# Manually test Ollama connection
docker-compose exec app curl http://ollama:11434/api/tags
```

### Issue: "Model download timeout"

**Solution**: The qwen3-vl:4b model is ~3.3GB. On slow connections:

```bash
# Increase timeout in docker-compose.yml or download model separately
docker-compose exec ollama ollama pull qwen3-vl:4b
```

### Issue: "Out of memory"

**Solution**: Increase Docker memory limit:

```bash
# macOS/Windows: Docker Desktop → Settings → Resources → Memory → 8GB+
# Linux: Edit /etc/docker/daemon.json
```

### Issue: "Permission denied"

**Solution**: Ensure docker-test.sh is executable:

```bash
chmod +x docker-test.sh
```

## Cleaning Up

Remove all Docker resources:

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes (complete cleanup)
docker-compose down -v

# Remove images
docker rmi $(docker images -q localimagesearch_app)
docker rmi ollama/ollama
```

## Customization

### Test with your own images

Mount your image directory in docker-compose.yml:

```yaml
services:
  app:
    volumes:
      - /path/to/your/images:/app/my_images:ro
```

Then modify the command to test your images:

```yaml
uv run python src/main.py \
  --image-path /app/my_images \
  --model qwen3-vl:4b \
  --language zh
```

### Change model

Edit docker-compose.yml to use a different model:

```bash
curl -X POST http://ollama:11434/api/pull -d '{"name": "llava-v1.6:7b"}'
```

## Architecture

```
┌─────────────────────────────────────┐
│         Docker Host                 │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Ollama Container            │  │
│  │   - Port: 11434              │  │
│  │   - Model: qwen3-vl:4b       │  │
│  │   - Volume: ollama-data      │  │
│  └──────────────────────────────┘  │
│             ↕ HTTP API              │
│  ┌──────────────────────────────┐  │
│  │   App Container               │  │
│  │   - Python 3.11              │  │
│  │   - uv package manager       │  │
│  │   - Project code             │  │
│  │   - Volumes: ./data          │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Performance Notes

### First Run
- **Build time**: 2-5 minutes (downloading base images and dependencies)
- **Model download**: 3-5 minutes (qwen3-vl:4b ~3.3GB)
- **Total time**: 5-10 minutes

### Subsequent Runs
- **Startup time**: 10-30 seconds (using cached images and model)
- **Processing time**: 1-2 seconds per image

## Verification Checklist

After running the Docker test, verify:

- [ ] Ollama service started successfully
- [ ] qwen3-vl:4b model downloaded
- [ ] Python dependencies installed via uv
- [ ] Test image processed successfully
- [ ] Chinese tags generated correctly
- [ ] Database record created
- [ ] All tags are 2+ characters (Chinese requirement)
- [ ] Tags are noun-based descriptive phrases

## Next Steps

After successful Docker verification:

1. **Deploy on host machine**: Follow README.md instructions for native installation
2. **Process your images**: Use the same commands with your image directory
3. **Explore features**: Try different models, languages, and tag counts

## Support

If you encounter issues:
1. Check Docker logs: `docker-compose logs`
2. Verify Docker resources: RAM, disk space
3. Review README.md for detailed usage instructions
4. Check Ollama service: `curl http://localhost:11434/api/tags`

---

**Last Updated**: 2026-02-04
**Docker Image**: Python 3.11-slim
**Ollama Version**: Latest
**Tested Models**: qwen3-vl:4b
