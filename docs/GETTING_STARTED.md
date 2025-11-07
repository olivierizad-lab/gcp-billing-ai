# Getting Started - Local Development & Deployment

Two options: **Local Development** (test first) or **Deploy to Cloud Run** (production-ready).

## Option 1: Local Development (Recommended First) ✅

Test everything locally before deploying. This is the easiest way to get started!

### Prerequisites

```bash
# Check you have these installed
python3 --version  # Should be 3.11+
node --version     # Should be 18+
npm --version
```

### Step 1: Set Up Agent IDs

Make sure your agents have `REASONING_ENGINE_ID` set in their `.env` files:

```bash
# Find your Reasoning Engine IDs
make list-deployments AGENT_NAME=bq_agent_mick
make list-deployments AGENT_NAME=bq_agent

# Update .env files
# bq_agent_mick/.env
REASONING_ENGINE_ID=your_id_here

# bq_agent/.env
REASONING_ENGINE_ID=your_id_here
```

### Step 2: Start Backend

```bash
cd web/backend

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

✅ Backend running on `http://localhost:8000`

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Start Frontend (New Terminal)

```bash
cd web/frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

✅ Frontend running on `http://localhost:3000`

You should see:
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:3000/
```

### Step 4: Open in Browser

Open **http://localhost:3000** in your browser!

1. Select an agent from the dropdown
2. Start chatting! 🎉

### Troubleshooting Local

**Backend won't start?**
- Check GCP credentials: `gcloud auth application-default login`
- Check agent IDs are set in `.env` files

**Frontend can't connect?**
- Make sure backend is running on port 8000
- Check browser console for errors

**"Agent not configured"?**
- Verify `REASONING_ENGINE_ID` in agent `.env` files
- Restart backend after updating `.env`

---

## Option 2: Deploy to Cloud Run (Production)

Once you've tested locally, deploy to Cloud Run with IAP security.

### Quick Deploy (No DNS Required)

Perfect for course/temporary deployments:

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
./deploy-simple-iap.sh
```

**That's it!** You'll get URLs like:
- API: `https://agent-engine-api-xxxxx-uc.a.run.app`
- UI: `https://agent-engine-ui-xxxxx-uc.a.run.app`

End users sign in using the custom Firestore-based authentication flow (restricted to `@asl.apps-eval.com`).

### Clean Up When Done

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
./cleanup.sh
```

For a full walkthrough of provisioning Firestore authentication and environment variables, see [START_HERE.md](./START_HERE.md).

---

## Which Should I Use?

| Use Case | Recommendation |
|----------|---------------|
| **Testing / Development** | Local development (`npm run dev`, `python main.py`) |
| **Course / Temporary Environments** | `make deploy-web-simple PROJECT_ID=...` (Firestore auth) |
| **Production** | See [AUTOMATED_DEPLOYMENT.md](./AUTOMATED_DEPLOYMENT.md) for the full Cloud Run pipeline |

---

## Quick Reference

### Local Development
```bash
# Terminal 1: Backend
cd web/backend && pip install -r requirements.txt && python main.py

# Terminal 2: Frontend
cd web/frontend && npm install && npm run dev

# Browser: http://localhost:3000
```

### Cloud Run Deployment
```bash
# Option A: Makefile helper (recommended)
make deploy-web-simple PROJECT_ID=your-project-id

# Option B: Deployment script
cd web/deploy
export PROJECT_ID="your-project-id"
./deploy-web.sh
```

---

## Next Steps

1. **Start with Local** - Test everything locally first
2. **Deploy to Cloud Run** - Use the commands above to publish the Firestore-authenticated UI
3. **Clean Up** - Run `web/deploy/cleanup.sh` when finished to remove Cloud Run resources

See [START_HERE.md](./START_HERE.md) and [AUTOMATED_DEPLOYMENT.md](./AUTOMATED_DEPLOYMENT.md) for comprehensive deployment guidance.

