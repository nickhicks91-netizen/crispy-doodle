# Google Docs AI Organizer 🤖📁

An intelligent agent that automatically organizes your Google Docs into labeled folders based on AI-powered content analysis.

## Features

- **AI-Powered Categorization**: Uses Claude AI to analyze document content and intelligently categorize files
- **Automatic Folder Creation**: Creates organized folder structure in your Google Drive
- **Customizable Categories**: Define your own categories or use smart defaults
- **Dry Run Mode**: Preview changes before making them
- **Batch Processing**: Handles large numbers of documents efficiently
- **Detailed Statistics**: Track what was organized and any issues encountered

## How It Works

1. **Authenticates** with your Google Account (OAuth2 - secure and local)
2. **Fetches** all Google Docs from your Drive
3. **Analyzes** each document's content using Claude AI
4. **Categorizes** documents into relevant folders
5. **Organizes** by moving files into category-based folders
6. **Reports** detailed statistics on the organization process

## Quick Start - The Easy Way! 🚀

**New to setup?** Use the interactive wizard - it does everything for you:

```bash
python easy_setup.py
```

The wizard will:
- ✅ Guide you through each step
- ✅ Open the right websites automatically
- ✅ Check everything works
- ✅ Run a test for you!

Takes about 10 minutes. See [QUICKSTART.md](QUICKSTART.md) for details.

---

## Prerequisites

- Python 3.7 or higher
- Google Account with Google Docs
- Anthropic API key (for Claude AI - free trial available)
- Google Cloud Project with Drive & Docs APIs enabled (free)

## Setup Instructions

### Option 1: Easy Setup (Recommended)

```bash
python easy_setup.py
```

Follow the prompts! The wizard handles everything.

### Option 2: Manual Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Drive API
   - Google Docs API
4. Create OAuth 2.0 credentials:
   - Navigate to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Download the credentials file
5. Rename the downloaded file to `credentials.json` and place it in the project directory

### 3. Get Anthropic API Key

1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Navigate to API Keys
3. Create a new API key
4. Copy the key for the next step

### 4. Configure the Organizer

1. Copy the example config:
   ```bash
   cp config.json.example config.json
   ```

2. Edit `config.json` and add your Anthropic API key:
   ```json
   {
     "anthropic_api_key": "sk-ant-api03-...",
     "dry_run": true,
     ...
   }
   ```

### 5. Customize Categories (Optional)

Edit the `categories` section in `config.json`:

```json
"categories": {
  "default": [
    "Work",
    "Personal",
    "Finance",
    "Health",
    "Education",
    "Projects",
    "Notes",
    "Miscellaneous"
  ],
  "custom": [
    "Client Proposals",
    "Meeting Notes",
    "Research",
    "Drafts"
  ]
}
```

If you provide custom categories, they will be used instead of defaults.

## Usage

### First Run (Dry Run - Recommended)

Test the organizer without making changes:

```bash
python google_docs_organizer.py
```

The default config has `"dry_run": true`, so it will show you what it would do without actually moving files.

### Organize for Real

Once you're happy with the dry run results:

1. Edit `config.json` and set `"dry_run": false`
2. Run the organizer:
   ```bash
   python google_docs_organizer.py
   ```

### First-Time Authentication

The first time you run the script, it will:
1. Open your browser
2. Ask you to sign in to your Google Account
3. Request permission to access your Drive and Docs
4. Save authentication credentials locally (`token.pickle`)

Future runs will use the saved credentials automatically.

## Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `anthropic_api_key` | string | Your Anthropic API key |
| `credentials_file` | string | Path to Google OAuth credentials (default: `credentials.json`) |
| `token_file` | string | Where to save auth token (default: `token.pickle`) |
| `create_organized_folder` | boolean | Create a parent "Organized Docs" folder (default: `true`) |
| `organized_folder_name` | string | Name of the parent folder (default: `"Organized Docs"`) |
| `dry_run` | boolean | Preview mode - don't actually move files (default: `true`) |
| `max_docs_to_process` | number/null | Limit number of docs to process (default: `null` = all) |
| `categories.default` | array | Default categories to use |
| `categories.custom` | array | Your custom categories (overrides default if provided) |

## Example Output

```
🚀 Starting Google Docs Organizer Agent...

============================================================
🤖 Google Docs AI Organizer Agent
============================================================
🔐 Authenticating with Google...
✅ Successfully authenticated with Google
✅ Claude API initialized

📄 Fetching Google Docs...
✅ Found 47 Google Docs

📁 Setting up 'Organized Docs' folder...
  ✅ Created folder: Organized Docs

🔄 Processing 47 documents...
------------------------------------------------------------

[1/47] Q4 Budget Planning
  🤔 Analyzing content...
  📂 Category: Finance
  ✅ Created folder: Finance
  ✅ Moved to Finance

[2/47] Team Meeting Notes - Nov 2024
  🤔 Analyzing content...
  📂 Category: Work
  ✅ Created folder: Work
  ✅ Moved to Work

...

============================================================
📊 Organization Summary
============================================================
Documents analyzed: 47
Documents organized: 47
Folders created: 8
Errors: 0
============================================================
```

## Security & Privacy

- **OAuth Authentication**: Uses Google's official OAuth2 flow - your credentials stay secure
- **Local Processing**: Authentication tokens are stored locally on your machine
- **API Keys**: Keep your `config.json` private (it's in `.gitignore`)
- **Read-Only Docs Access**: The script only reads document content for analysis
- **No Data Storage**: Document content is analyzed on-the-fly, not stored anywhere

## Troubleshooting

### "Credentials file not found"

Make sure you've downloaded `credentials.json` from Google Cloud Console and placed it in the project directory.

### "Anthropic API key not configured"

Update `config.json` with your actual API key from Anthropic Console.

### "No documents found"

- Check that you have Google Docs in your Drive
- Ensure the OAuth authentication completed successfully
- Try re-authenticating by deleting `token.pickle` and running again

### Rate Limiting

If you have many documents, the script might hit API rate limits. Use `max_docs_to_process` to process in batches.

## Advanced Usage

### Process Limited Number of Documents

```json
{
  "max_docs_to_process": 20
}
```

### Use Different Folder Name

```json
{
  "organized_folder_name": "AI Sorted Docs"
}
```

### Test with Dry Run First

Always recommended before organizing for the first time:

```json
{
  "dry_run": true
}
```

## Contributing

Feel free to submit issues or pull requests to improve the organizer!

## License

MIT License - feel free to use and modify as needed.

## Acknowledgments

- Uses [Google Drive API](https://developers.google.com/drive) for file management
- Powered by [Claude AI](https://www.anthropic.com/claude) for intelligent categorization
