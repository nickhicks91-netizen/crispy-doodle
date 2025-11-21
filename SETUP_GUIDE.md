# Google Docs Organizer - Quick Setup Guide

## Step-by-Step Setup

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Get Google Cloud Credentials

#### 2.1 Create Google Cloud Project

1. Visit https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Enter project name (e.g., "docs-organizer")
4. Click "Create"

#### 2.2 Enable Required APIs

1. In the Cloud Console, go to "APIs & Services" → "Library"
2. Search for and enable:
   - **Google Drive API**
   - **Google Docs API**

#### 2.3 Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: **External**
   - App name: "Google Docs Organizer"
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: You can skip this for now
   - Test users: Add your email address
   - Save and continue
4. Back in Credentials, create OAuth client ID:
   - Application type: **Desktop app**
   - Name: "Docs Organizer Desktop"
5. Click "Create"
6. Download the JSON file
7. Rename it to `credentials.json`
8. Move it to the project directory

### Step 3: Get Anthropic API Key

1. Visit https://console.anthropic.com/
2. Sign up or log in
3. Go to "API Keys" section
4. Click "Create Key"
5. Name it "Docs Organizer"
6. Copy the API key (starts with `sk-ant-api03-...`)

### Step 4: Configure the Application

1. Copy the example config:
   ```bash
   cp config.json.example config.json
   ```

2. Open `config.json` in a text editor

3. Replace `YOUR_ANTHROPIC_API_KEY_HERE` with your actual API key:
   ```json
   {
     "anthropic_api_key": "sk-ant-api03-YOUR-ACTUAL-KEY-HERE",
     ...
   }
   ```

4. Optionally customize categories and settings

### Step 5: Test Run (Dry Run)

```bash
python google_docs_organizer.py
```

This will:
- Open your browser for Google authentication
- Analyze your Google Docs
- Show what it would organize (without actually moving files)

### Step 6: Organize for Real

1. Review the dry run output
2. If happy with the results, edit `config.json`:
   ```json
   {
     "dry_run": false,
     ...
   }
   ```
3. Run again:
   ```bash
   python google_docs_organizer.py
   ```

## Configuration Checklist

Before running, ensure you have:

- [ ] Installed Python dependencies (`pip install -r requirements.txt`)
- [ ] Created `credentials.json` from Google Cloud Console
- [ ] Created `config.json` from the example
- [ ] Added your Anthropic API key to `config.json`
- [ ] Tested with dry run mode first

## Common Issues

### "credentials.json not found"

Download OAuth credentials from Google Cloud Console and save as `credentials.json` in the project directory.

### "API key not configured"

Edit `config.json` and replace `YOUR_ANTHROPIC_API_KEY_HERE` with your actual Anthropic API key.

### Browser doesn't open for authentication

The script will print a URL - copy and paste it into your browser manually.

### "Access blocked: This app's request is invalid"

Make sure you've:
1. Enabled both Google Drive API and Google Docs API
2. Configured the OAuth consent screen
3. Added yourself as a test user

## Need Help?

Check the main README.md for detailed documentation and troubleshooting tips.
