# Testing Firestore History Feature

Quick guide to test the query history functionality.

## Prerequisites

1. **GCP Authentication** (if not already set):
   ```bash
   gcloud auth application-default login
   ```

2. **Firestore API** (if not already enabled):
   ```bash
   gcloud services enable firestore.googleapis.com --project=YOUR_PROJECT_ID
   ```

3. **Firestore Database** (if not already created):
   - Go to [Firestore Console](https://console.cloud.google.com/firestore)
   - Create a database (Native mode is fine)
   - Choose a location (e.g., `us-central`)

## Step 1: Install Backend Dependencies

```bash
cd web/backend
pip install -r requirements.txt
```

This will install `google-cloud-firestore` and other dependencies.

## Step 2: Start Backend Server

```bash
cd web/backend
python main.py
```

✅ Backend should start on `http://localhost:8000`

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Note:** If you see a warning about Firestore initialization, that's okay - it will work once Firestore API is enabled.

## Step 3: Start Frontend (New Terminal)

```bash
cd web/frontend
npm install  # Only needed first time
npm run dev
```

✅ Frontend should start on `http://localhost:3000` (or `http://localhost:5173`)

## Step 4: Test History Features

### Test 1: Send a Query

1. Open `http://localhost:3000` in your browser
2. Select an agent from the dropdown
3. Send a query like: "What are the total costs by top 10 services?"
4. Wait for the response

✅ **Expected:** Query and response should be saved to Firestore automatically

### Test 2: View History

1. Click the **History button** (📜 icon) in the header
2. You should see a sidebar appear on the right
3. Your recent query should appear in the list

✅ **Expected:** History sidebar shows your query with:
   - Agent name
   - Query message (truncated)
   - Timestamp

### Test 3: Load History Item

1. In the history sidebar, click on any query item
2. The conversation should load in the main chat area

✅ **Expected:** Main chat shows the full query and response

### Test 4: Delete Individual Query

1. In the history sidebar, click the **trash icon** (🗑️) on any query
2. Confirm deletion
3. The query should disappear from the list

✅ **Expected:** Query is removed from history

### Test 5: Delete All History

1. In the history sidebar, click the **trash icon** (🗑️) in the header
2. Confirm deletion
3. All queries should be removed

✅ **Expected:** All history cleared, sidebar shows "No query history yet"

### Test 6: Reload History on Startup

1. Refresh the browser page
2. Click the History button
3. Your queries should still be there

✅ **Expected:** History persists across page reloads

## Verify in Firestore Console

1. Go to [Firestore Console](https://console.cloud.google.com/firestore)
2. Select your project
3. Look for collection: `query_history`
4. You should see documents with fields:
   - `user_id`: "web_user"
   - `agent_name`: e.g., "bq_agent_mick"
   - `message`: The user's query
   - `response`: The agent's response
   - `timestamp`: When the query was made

## Troubleshooting

### "Firestore client not initialized"
- Enable Firestore API: `gcloud services enable firestore.googleapis.com`
- Check GCP authentication: `gcloud auth application-default login`
- Verify project ID in `.env` or `BQ_PROJECT` environment variable

### "Failed to save query to Firestore"
- Check backend logs for detailed error
- Verify Firestore database exists in your project
- Check IAM permissions for Firestore

### History not loading
- Check browser console for errors
- Verify backend is running and accessible
- Check backend logs for API errors

### History sidebar not appearing
- Check browser console for JavaScript errors
- Verify frontend dependencies are installed: `npm install`
- Try hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)

## API Testing (Optional)

You can also test the API endpoints directly:

```bash
# Get history
curl "http://localhost:8000/history?user_id=web_user&limit=10"

# Delete a specific query (replace QUERY_ID)
curl -X DELETE "http://localhost:8000/history/QUERY_ID?user_id=web_user"

# Delete all history
curl -X DELETE "http://localhost:8000/history?user_id=web_user"
```

