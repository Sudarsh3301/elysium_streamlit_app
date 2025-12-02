# 🔐 Security Setup Guide - Groq API Key Management

## ⚠️ CRITICAL: API Key Security

**NEVER commit API keys to git!** This guide shows you how to securely configure your Groq API key for both local development and Streamlit Cloud deployment.

---

## 🏠 Local Development Setup

### Step 1: Get Your Groq API Key

1. Go to [Groq Console](https://console.groq.com/keys)
2. Sign in or create an account
3. Click "Create API Key"
4. Copy the key (starts with `gsk_`)
5. **Save it securely** - you won't be able to see it again!

### Step 2: Create .env File

1. Navigate to `elysium_streamlit_app/` directory
2. Copy the example file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your API key:
   ```bash
   GROQ_API_KEY="gsk_your_actual_key_here"
   ```

### Step 3: Verify .gitignore

Ensure `.env` is in `.gitignore` (already configured):
```bash
# Check if .env is ignored
git check-ignore .env
# Should output: .env
```

### Step 4: Test Local Setup

```bash
cd elysium_streamlit_app
streamlit run app.py
```

The app should start without API key errors.

---

## ☁️ Streamlit Cloud Deployment

### Step 1: Deploy Your App

1. Push your code to GitHub (without .env file!)
2. Go to [Streamlit Cloud](https://share.streamlit.io/)
3. Click "New app"
4. Select your repository and branch
5. Set main file path: `elysium_streamlit_app/app.py`

### Step 2: Configure Secrets

1. In your app dashboard, click "⚙️ Settings"
2. Navigate to "Secrets" section
3. Add your secret in TOML format:
   ```toml
   GROQ_API_KEY = "gsk_your_actual_key_here"
   ```
4. Click "Save"
5. App will automatically redeploy

### Step 3: Verify Deployment

- Check app logs for "Groq client initialized successfully"
- Test AI features (Catalogue search, Athena)
- Verify no API key appears in logs

---

## 🔄 Rotating a Compromised Key

If your API key was exposed (committed to git, shared publicly, etc.):

### Step 1: Revoke Old Key

1. Go to [Groq Console](https://console.groq.com/keys)
2. Find the compromised key
3. Click "Delete" or "Revoke"

### Step 2: Generate New Key

1. Click "Create API Key"
2. Copy the new key
3. Update in both locations:
   - Local: `.env` file
   - Cloud: Streamlit Cloud secrets

### Step 3: Clean Git History (if key was committed)

**⚠️ WARNING: This rewrites git history!**

```bash
# Install git-filter-repo
pip install git-filter-repo

# Remove the file containing the key from ALL history
git filter-repo --path elysium_streamlit_app/GROQ_MIGRATION_SUMMARY.md --invert-paths

# Force push (coordinate with team first!)
git push origin --force --all
```

### Step 4: Verify Security

1. Check GitHub Security tab: Settings → Security → Secret scanning
2. Confirm no active secrets detected
3. Verify old key no longer works

---

## 🧪 Testing Your Setup

### Test 1: Local Environment

```bash
cd elysium_streamlit_app

# Test environment variable is set
python -c "import os; print('✅ Key found' if os.getenv('GROQ_API_KEY') else '❌ Key missing')"

# Test Groq client initialization
python -c "from groq_client import GroqClient; c = GroqClient(); print('✅ Client initialized')"
```

### Test 2: Streamlit Cloud

After deployment:
1. Open your app URL
2. Check browser console for errors
3. Test AI features:
   - Catalogue → Natural Language Search
   - Athena → Client Brief Parsing
4. Verify responses are generated

---

## 🚨 Common Issues & Solutions

### Issue: "Groq API key not found"

**Local Development:**
- Check `.env` file exists in `elysium_streamlit_app/`
- Verify variable name is `GROQ_API_KEY` (not `groq`)
- Ensure no extra spaces or quotes

**Streamlit Cloud:**
- Check secrets are saved in app settings
- Verify TOML format: `GROQ_API_KEY = "value"`
- Redeploy app after adding secrets

### Issue: "Invalid Groq API key format"

- Key should start with `gsk_`
- Key should be 50+ characters
- No extra spaces or newlines
- Check for copy-paste errors

### Issue: Git push rejected (secret detected)

1. **DO NOT** force push with the secret still in history
2. Follow "Rotating a Compromised Key" steps above
3. Remove secret from git history first
4. Then push with new key (not in code)

---

## 📋 Security Checklist

Before committing code:

- [ ] `.env` file is NOT staged for commit
- [ ] No API keys in source code
- [ ] No API keys in documentation
- [ ] `.gitignore` includes `.env` and `secrets.toml`
- [ ] Only `.env.example` and `secrets.toml.example` are committed
- [ ] API key works locally
- [ ] API key configured in Streamlit Cloud secrets

Before deploying:

- [ ] Secrets configured in Streamlit Cloud
- [ ] App starts without errors
- [ ] AI features work correctly
- [ ] No keys visible in logs or UI
- [ ] GitHub security scan shows no issues

---

## 🔗 Useful Links

- [Groq Console](https://console.groq.com/)
- [Groq API Documentation](https://console.groq.com/docs)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)

---

## 📞 Support

If you encounter issues:

1. Check this guide first
2. Review app logs for specific errors
3. Verify API key is valid in Groq Console
4. Test with a fresh API key
5. Check Streamlit Cloud deployment logs

**Remember: Security is not optional. Protect your API keys!** 🔐

