# Quick Start Guide - The Easy Way! 🚀

Having trouble with setup? This guide makes it super simple.

## The Easiest Way (Recommended)

Just run the interactive setup wizard:

```bash
python easy_setup.py
```

That's it! The wizard will:
- ✅ Check everything automatically
- ✅ Guide you through each step
- ✅ Open the right websites for you
- ✅ Test your setup
- ✅ Even run a test for you!

The wizard asks questions and helps you at every step. Just follow along!

---

## What You Need

Before starting, make sure you have:

1. **Python 3.7+** installed (probably already have it)
2. **A Google account** with some Google Docs
3. **10 minutes** of time

You'll get:
- A Google Cloud account (free)
- An Anthropic API key (free trial available)

---

## Step-by-Step (If You Want to Do It Manually)

### 1. Install Python Packages

```bash
pip install -r requirements.txt
```

### 2. Get Google Credentials

**The wizard does this for you**, but if doing manually:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project
3. Enable "Google Drive API" and "Google Docs API"
4. Create OAuth credentials (Desktop app)
5. Download as `credentials.json`

**Stuck?** Run `python easy_setup.py` - it opens the right pages and shows detailed steps!

### 3. Get Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com)
2. Sign up (free trial available)
3. Create an API key
4. Copy it

### 4. Configure

```bash
# Create config file
cp config.json.example config.json

# Edit it and add your API key
nano config.json  # or use any text editor
```

### 5. Test It!

```bash
python google_docs_organizer.py
```

---

## Common Issues & Solutions

### "I don't know how to get Google credentials"

Run `python easy_setup.py` - it will open the right pages and show you exactly what to click!

### "Where do I get an Anthropic API key?"

Run `python easy_setup.py` - it opens the console for you. Or go directly to: https://console.anthropic.com/settings/keys

### "The setup is too complicated"

Use the easy setup wizard:
```bash
python easy_setup.py
```

It does almost everything for you!

### "I want to test with just a few documents first"

Good idea! The wizard asks this and sets it up. Or manually edit `config.json`:

```json
{
  "max_docs_to_process": 10,
  "dry_run": true
}
```

### "What's dry run mode?"

Dry run means it shows you what it WOULD do, but doesn't actually move files. Perfect for testing!

The first run is always in dry run mode for safety.

---

## Super Quick Reference

```bash
# Easy setup (RECOMMENDED - does everything for you!)
python easy_setup.py

# Or manual setup
pip install -r requirements.txt
# ... get credentials.json ...
# ... get API key ...
cp config.json.example config.json
# ... edit config.json ...

# Test run (safe - won't move files)
python google_docs_organizer.py

# When ready to organize for real
# Edit config.json: "dry_run": false
python google_docs_organizer.py
```

---

## Video Walkthrough (What the Wizard Does)

The `easy_setup.py` wizard:

1. **Checks Python version** ✓
2. **Installs packages automatically** ✓
3. **Opens Google Cloud Console** and shows you exactly what to click
4. **Waits for you** to download credentials.json
5. **Opens Anthropic Console** for your API key
6. **Saves everything** to config.json
7. **Asks about preferences** (folder name, how many docs to test, etc.)
8. **Tests the setup** to make sure everything works
9. **Offers to run a test** right away!

Takes about 10 minutes total, and most of that is waiting for websites to load.

---

## Still Stuck?

1. Check the full [README.md](README.md) for detailed documentation
2. Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for step-by-step instructions with screenshots
3. Re-run the wizard - it's safe to run multiple times:
   ```bash
   python easy_setup.py
   ```

---

## Once It's Working

After setup, using it is super simple:

```bash
# Run in dry mode to see what it would do
python google_docs_organizer.py

# When happy, turn off dry mode in config.json
# Then run again to actually organize
python google_docs_organizer.py
```

That's it! The AI will:
- Read your Google Docs
- Understand what each document is about
- Create organized folders
- Move files to the right places
- Show you a nice summary

Happy organizing! 🎉
