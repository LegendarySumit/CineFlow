# 🔐 Security & Credentials Management

## Overview

This document explains how to safely manage credentials and deploy CineFlow without exposing secrets.

---

## ✅ Security Checklist

### Before First Commit
- [x] `.gitignore` configured (excludes `.env` and sensitive files)
- [x] `.env.example` created (template with placeholders)
- [x] No hardcoded API keys in code
- [x] All credentials loaded from environment variables
- [x] Production secrets never committed

### Before Deployment
- [ ] Create `.env` file locally (copy from `.env.example`)
- [ ] Fill in actual API keys in `.env`
- [ ] Verify `.env` is in `.gitignore`
- [ ] Run `git status` to confirm no `.env` file will be committed
- [ ] Test with actual credentials locally
- [ ] Deploy with environment variables set on server

---

## 🔑 Credential Management

### Local Development

**Step 1: Create Local `.env` File**
```bash
cd D:\WEBD\CineFlow
cp .env.example .env
```

**Step 2: Edit `.env` with Your Credentials**
```bash
# Open .env and fill in:
GEMINI_API_KEY=your_actual_gemini_key_here
PARALLEL_API_KEY=your_actual_parallel_key_here
```

**Step 3: Verify `.env` is Ignored**
```bash
git status
# Should NOT show .env file
```

**Step 4: Load Credentials in Code**
```python
# Credentials are automatically loaded from .env
# via python-dotenv (already in requirements.txt)
import os
api_key = os.getenv("GEMINI_API_KEY")
```

---

## 📝 How Credentials are Used

### FastAPI Bootstrap
**File**: `app/main.py`
```python
# All API keys loaded from environment variables
# Never hardcoded in source code
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PARALLEL_API_KEY = os.getenv("PARALLEL_API_KEY")
```

### Supervisor Agent
**File**: `app/agents/supervisor.py`
```python
# LLM credentials passed to Gemini API
# Loaded from environment at runtime
```

### External Services
**File**: `app/tools/parallel_mcp.py`
```python
# Parallel API key loaded from environment
# Only used when web search is needed
```

---

## 🚀 Deployment Security

### Docker Deployment

**Step 1: Build Docker Image (No Secrets Included)**
```bash
docker build -t cineflow:latest .
```

**Step 2: Run with Environment Variables**
```bash
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e PARALLEL_API_KEY=your_key \
  cineflow:latest
```

**Alternative: Use `.env` File at Runtime**
```bash
docker run -p 8000:8000 \
  --env-file /path/to/.env \
  cineflow:latest
```

### Cloud Deployment (GCP, AWS, Azure)

**Use Secrets Manager**
```bash
# GCP Secret Manager
gcloud secrets create gemini-api-key --data-file=- <<< "your_key"
gcloud secrets create parallel-api-key --data-file=- <<< "your_key"

# AWS Secrets Manager
aws secretsmanager create-secret --name gemini-api-key --secret-string "your_key"
aws secretsmanager create-secret --name parallel-api-key --secret-string "your_key"
```

**Reference in Deployment**
```yaml
# Example: Google Cloud Run deployment
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: cineflow
spec:
  template:
    spec:
      containers:
      - image: gcr.io/project/cineflow:latest
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-api-key
              key: password
```

---

## 🔍 What's Protected

### Files NOT Committed (in `.gitignore`)
```
.env                          # Local credentials
.env.*.local                  # Environment-specific configs
audit_logs/*                  # Session data
__pycache__/                  # Python cache
.vscode/                      # IDE settings
venv/                         # Virtual environment
*.pyc                         # Compiled Python
.DS_Store                     # Mac files
.idea/                        # IntelliJ config
```

### Files Always Safe to Commit
```
.env.example                  # Template only (placeholders)
app/**/*.py                   # Source code (no secrets)
requirements.txt              # Dependencies (no secrets)
README.md                      # Documentation
pyproject.toml               # Project config
.gitignore                    # Security config
SECURITY.md                   # This file
```

---

## ⚠️ What Could Go Wrong

### ❌ DO NOT
```python
# ❌ WRONG: Hardcoded API key
api_key = "sk-abc123..."  # This gets committed!

# ❌ WRONG: Credential in config file that's tracked
# config.json (if tracked by Git)

# ❌ WRONG: Logging secrets
print(f"Using API key: {api_key}")  # Don't log credentials
```

### ✅ DO
```python
# ✅ CORRECT: Load from environment
api_key = os.getenv("GEMINI_API_KEY")

# ✅ CORRECT: Use .env.example as template
# .env.example committed with placeholders
# .env created locally with actual values

# ✅ CORRECT: Never log credentials
if api_key:
    logger.info("API key loaded successfully")
    # Don't print the actual key!
```

---

## 🔐 Best Practices

### 1. Never Commit Secrets
```bash
# Check before committing
git status

# Should NOT show .env
# Should only show .env.example (with placeholders)
```

### 2. Use Environment Variables
```python
# Always use os.getenv() for production values
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")
```

### 3. Create `.env` from `.env.example`
```bash
# First time setup
cp .env.example .env

# Fill in actual values
nano .env

# Verify it's ignored
git status  # Should not show .env
```

### 4. Rotate Keys Regularly
- Change API keys every 90 days
- Immediately rotate if key is exposed
- Keep old keys for graceful migration

### 5. Use Different Keys per Environment
```
.env (development)      - Development key
.env.staging           - Staging key
.env.production        - Production key (in secrets manager)
```

---

## 🔄 Git Workflow

### Safe Push Process

**Step 1: Create `.env` Locally**
```bash
cp .env.example .env
# Edit .env with your actual API keys
```

**Step 2: Add `.env` to `.gitignore` (Already Done)**
```bash
cat .gitignore | grep -E "\.env|secrets"
# Should show .env and other sensitive patterns
```

**Step 3: Verify Nothing Will Leak**
```bash
git status
# .env should NOT be listed
# Only .env.example should be in repository
```

**Step 4: Commit & Push**
```bash
git add .
git commit -m "Add CineFlow production code and configuration"
git push origin main
```

**Step 5: Verify Remote is Clean**
```bash
# After push, verify no .env on GitHub
git ls-remote --heads origin main
# Check GitHub: https://github.com/yourusername/CineFlow
# Should NOT show .env file
```

---

## 🚨 If Credentials Are Accidentally Exposed

### Immediate Actions
1. **Invalidate compromised key immediately**
   ```bash
   # Revoke the exposed key in Google Cloud Console
   # Revoke the exposed key in Parallel Dashboard
   ```

2. **Create new credentials**
   ```bash
   # Generate new GEMINI_API_KEY
   # Generate new PARALLEL_API_KEY
   ```

3. **Update local `.env`**
   ```bash
   nano .env
   # Update with new credentials
   ```

4. **Force remove from Git history** (if committed)
   ```bash
   # Remove from history (caution: rewrites history)
   git filter-branch --tree-filter 'rm -f .env' HEAD
   git push --force
   ```

5. **Inform team**
   - Document the exposure
   - Update all deployment environments
   - Use new credentials everywhere

---

## 📋 Verification Checklist

Before Pushing to Public Repository:
```bash
# 1. Check .gitignore exists
[ -f .gitignore ] && echo "✅ .gitignore exists"

# 2. Check .env is ignored
git status | grep -q ".env" && echo "❌ .env would be committed!" || echo "✅ .env is ignored"

# 3. Check .env.example exists (with placeholders only)
[ -f .env.example ] && echo "✅ .env.example exists"

# 4. Verify no hardcoded API keys
grep -r "sk-" app/ && echo "❌ API key found in code!" || echo "✅ No hardcoded keys"
grep -r "api_key =" app/ && echo "⚠️  Check for hardcoded keys" || echo "✅ No hardcoded patterns"

# 5. Test with actual credentials locally
python -m uvicorn app.main:app --port 8000
# Should start without errors
```

---

## 📚 Additional Resources

- [Environment Variables Best Practices](https://12factor.net/config)
- [Git Secrets Prevention](https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work)
- [Python-dotenv Documentation](https://python-dotenv.readthedocs.io/)
- [GCP Secret Manager](https://cloud.google.com/secret-manager)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)

---

## ✅ Summary

| Item | Status | Action |
|------|--------|--------|
| `.gitignore` | ✅ Created | Configured to exclude `.env` |
| `.env.example` | ✅ Created | Template with placeholders |
| Hardcoded secrets | ✅ None | All loaded from environment |
| Code security | ✅ Clean | No API keys in source |
| Safe to push | ✅ Yes | Go ahead with confidence |

---

**You are now safe to push to GitHub without exposing credentials!** 🚀

1. Create `.env` file locally
2. Fill in your API keys
3. Run `git status` to verify `.env` is ignored
4. Push to GitHub
5. Share `.env.example` as setup guide

