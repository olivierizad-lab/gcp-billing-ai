# 🚀 GCP Billing Agent - Web Interface for Agent Engine

Welcome! This is the **web interface** for interacting with your deployed Vertex AI Agent Engine agents.

## 📁 What's Here

```
web/
├── backend/          # FastAPI server (Python)
│   ├── main.py      # Main API server
│   └── requirements.txt
│
├── frontend/         # React UI (Vite + React)
│   ├── src/
│   │   ├── App.jsx  # Main React component
│   │   └── ...
│   └── package.json
│
├── README.md         # Full documentation
└── START_HERE.md     # This file!
```

## ⚡ Quick Start

### Option 1: Local Development (Recommended First) ✅

Test everything locally before deploying:

```bash
# 1. Configure agent IDs
make list-deployments AGENT_NAME=bq_agent_mick

# 2. Start backend (Terminal 1)
cd web/backend
pip install -r requirements.txt
python main.py

# 3. Start frontend (Terminal 2)
cd web/frontend
npm install
npm run dev

# 4. Open http://localhost:3000
```

### Option 2: Deploy to Cloud Run

Deploy directly to Cloud Run with Firestore authentication:

```bash
# Makefile helper (recommended)
make deploy-web-simple PROJECT_ID=your-project-id

# Or use the deployment script
cd web/deploy
export PROJECT_ID="your-project-id"
./deploy-web.sh
```

**See [GETTING_STARTED.md](./GETTING_STARTED.md) and [AUTOMATED_DEPLOYMENT.md](./AUTOMATED_DEPLOYMENT.md) for detailed instructions.**

## 🎯 What You Can Do

- ✅ **Chat with your agents** - Select an agent and ask questions
- ✅ **See streaming responses** - Watch responses appear in real-time
- ✅ **Switch between agents** - Use the dropdown to change agents
- ✅ **Clear conversation** - Start fresh anytime
- ✅ **Modern UI** - Clean, modern chat interface

## 📚 Documentation

- **[GETTING_STARTED.md](./GETTING_STARTED.md)** - Local development & deployment guide
- **[AUTOMATED_DEPLOYMENT.md](./AUTOMATED_DEPLOYMENT.md)** - End-to-end Cloud Run pipeline
- **[README.md](./README.md)** - Full documentation with API details

## 🐛 Troubleshooting

**Backend won't start?**
- Run: `gcloud auth application-default login`
- Check: `pip list | grep fastapi`

**Frontend shows errors?**
- Make sure backend is running on port 8000
- Check browser console for details

**"Agent not configured"?**
- Verify `REASONING_ENGINE_ID` in agent `.env` files
- Restart backend after updating `.env`

## 🎨 Customization

- **Add more agents**: Edit `web/backend/main.py` → `load_agent_configs()`
- **Change UI colors**: Edit `web/frontend/src/index.css`
- **Modify layout**: Edit `web/frontend/src/App.jsx`

## 🚀 Next Steps

1. Try asking your agents questions!
2. Read the [full documentation](./README.md)
3. Customize the UI to your liking
4. Deploy to Cloud Run (see README.md)

---

**Questions?** Check [GETTING_STARTED.md](./GETTING_STARTED.md) or [README.md](./README.md) for more details!

