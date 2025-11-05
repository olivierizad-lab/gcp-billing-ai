# Quick Start Guide - GCP Billing Agent

Get your React chat interface running in 5 minutes!

## Prerequisites

1. **Node.js** (v18 or higher) - [Download here](https://nodejs.org/)
2. **Python** (3.11+) with pip
3. **GCP credentials** configured (`gcloud auth application-default login`)
4. **At least one agent deployed** to Vertex AI Agent Engine

## Step 1: Configure Agent IDs

Make sure your agent `.env` files have the `REASONING_ENGINE_ID` set:

```bash
# In bq_agent_mick/.env
REASONING_ENGINE_ID=your_engine_id_here

# In bq_agent/.env  
REASONING_ENGINE_ID=your_engine_id_here
```

To find your Reasoning Engine IDs:
```bash
make list-deployments AGENT_NAME=bq_agent_mick
make list-deployments AGENT_NAME=bq_agent
```

## Step 2: Install Backend Dependencies

```bash
cd web/backend
pip install -r requirements.txt
```

Or install globally:
```bash
pip install fastapi uvicorn python-multipart python-dotenv google-auth requests
```

## Step 3: Install Frontend Dependencies

```bash
cd web/frontend
npm install
```

## Step 4: Start the Backend

In one terminal:

```bash
cd web/backend
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 5: Start the Frontend

In another terminal:

```bash
cd web/frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

## Step 6: Open in Browser

Open [http://localhost:3000](http://localhost:3000) in your browser.

1. Select an agent from the dropdown
2. Start chatting!

## Troubleshooting

### Backend won't start

- Check that you have GCP credentials: `gcloud auth application-default login`
- Verify Python dependencies are installed: `pip list | grep fastapi`

### Frontend shows "Failed to load agents"

- Make sure the backend is running on port 8000
- Check browser console for CORS errors
- Verify `REASONING_ENGINE_ID` is set in agent `.env` files

### "Agent not configured" error

- Make sure the agent's `.env` file exists and has `REASONING_ENGINE_ID` set
- Restart the backend after updating `.env` files

### No streaming responses

- Check that the backend is running
- Verify the agent's `REASONING_ENGINE_ID` is correct
- Check browser console for errors

## Next Steps

- See [web/README.md](./README.md) for detailed documentation
- Customize the UI in `web/frontend/src/App.jsx`
- Add more agents in `web/backend/main.py`

