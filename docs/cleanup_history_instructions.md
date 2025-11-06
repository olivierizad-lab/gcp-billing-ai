# Query History Cleanup Instructions

## Quick Start

### Option 1: Using Make (Recommended)

```bash
# List history statistics
make clean-history-list PROJECT_ID=qwiklabs-asl-04-8e9f23e85ced

# Delete history for a specific user
make clean-history-user PROJECT_ID=qwiklabs-asl-04-8e9f23e85ced USER_ID=user-id-here

# Delete ALL history (use with caution!)
make clean-history-all PROJECT_ID=qwiklabs-asl-04-8e9f23e85ced
```

### Option 2: Direct Python Script

First, ensure dependencies are installed:

```bash
# Install dependencies (if not already installed)
cd web/backend
pip install -r requirements.txt

# Or use a virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then run the script:

```bash
# List history statistics
python3 cleanup_history.py --project-id=qwiklabs-asl-04-8e9f23e85ced --list

# Delete history for a specific user
python3 cleanup_history.py --project-id=qwiklabs-asl-04-8e9f23e85ced --user=user-id-here

# Delete ALL history (use with caution!)
python3 cleanup_history.py --project-id=qwiklabs-asl-04-8e9f23e85ced --all
```

### Option 3: Using Cloud Shell

1. Open Google Cloud Shell
2. Clone or upload the repository
3. Install dependencies: `pip install -r web/backend/requirements.txt`
4. Run the script: `python3 web/backend/cleanup_history.py --project-id=YOUR_PROJECT_ID --all`

## Safety Features

- **Double confirmation** required for `--all` flag
- **User-specific deletion** available with `--user` flag
- **Statistics** shown before deletion with `--list` flag

## What Gets Deleted

- Collection: `query_history`
- All documents in the collection (when using `--all`)
- Only documents for the specified user (when using `--user`)

## Notes

- The script uses Firestore batch operations (500 documents per batch)
- Deletions are permanent and cannot be undone
- Make sure you have the correct `PROJECT_ID` before running

