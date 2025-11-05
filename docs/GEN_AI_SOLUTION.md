# Gen AI Solutions Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Components](#components)
5. [Setup & Installation](#setup--installation)
6. [Usage](#usage)
7. [API Reference](#api-reference)
8. [Deployment](#deployment)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This Gen AI solution provides a comprehensive platform for deploying and interacting with Google ADK (Agent Development Kit) agents on Vertex AI Agent Engine. It includes:

- **Multiple AI Agents**: Deploy and manage multiple BigQuery-powered agents
- **Web Interface**: Modern React-based chat interface for interacting with agents
- **Query History**: Firestore-based persistent query history with user isolation
- **Conversation Context**: Session-based context retention for natural conversations
- **Agent Management**: Automated deployment and cleanup tools

---

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│  React Frontend │  (Chat UI)
│  (Port 3000)    │
└────────┬────────┘
         │ HTTP/SSE
         ▼
┌─────────────────┐
│  FastAPI Backend│  (Port 8000)
│  (Proxy Layer)  │
└────────┬────────┘
         │ REST API
         ▼
┌─────────────────┐
│ Vertex AI Agent │
│     Engine      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   BigQuery      │     │   Firestore     │
│  (Data Source)  │     │  (History)      │
└─────────────────┘     └─────────────────┘
```

### Component Flow

1. **User Interaction**: User sends message via React frontend
2. **Backend Processing**: FastAPI backend receives request, includes session_id for context
3. **Agent Engine**: Vertex AI Agent Engine processes query with conversation context
4. **BigQuery Execution**: Agent executes SQL queries against BigQuery
5. **Response Streaming**: Results stream back through backend to frontend
6. **History Storage**: Query/response saved to Firestore for future reference

---

## Features

### 1. Multi-Agent Support

- **bq_agent_mick**: BigQuery billing data analysis agent (Mick's version)
- **bq_agent**: Standard BigQuery data analysis agent
- Easy addition of new agents via configuration

### 2. Web Chat Interface

- Modern React-based UI
- Real-time streaming responses
- Agent selection dropdown
- Message history display
- Clean, responsive design

### 3. Query History (Firestore)

- **Automatic Saving**: All queries saved after execution
- **User Isolation**: Users only see their own history
- **History Sidebar**: Clickable history items
- **Delete Functionality**: Delete individual or all queries
- **Persistent Storage**: History survives page refreshes

### 4. Conversation Context

- **Session Management**: Each conversation gets a unique session_id
- **Context Retention**: Agent remembers previous messages in the same session
- **Natural Conversations**: Support for follow-up questions and references
- **Session Reset**: New session when clearing chat or loading old history

### 5. Deployment Management

- **Automated Deployment**: One-command agent deployment
- **Cleanup Tools**: Automatic cleanup of old deployments
- **Multi-Agent Support**: Deploy individual or all agents
- **Makefile Integration**: Simple commands for common tasks

---

## Components

### Backend (`web/backend/`)

#### `main.py`
FastAPI application providing:
- `/agents` - List available agents
- `/query/stream` - Stream query to agent (with session support)
- `/query` - Non-streaming query endpoint
- `/history` - Get user's query history
- `/history/{query_id}` - Delete specific query
- `/history` (DELETE) - Delete all user's history

#### `history.py`
Firestore service for query history:
- `save_query()` - Save query/response to Firestore
- `get_query_history()` - Retrieve user's history
- `delete_query()` - Delete specific query
- `delete_all_history()` - Delete all user's queries

### Frontend (`web/frontend/`)

#### `App.jsx`
Main React component:
- Agent selection
- Message display
- Streaming response handling
- History sidebar
- Session management

#### Key Features:
- Real-time message streaming (SSE)
- Session ID generation and management
- History loading and display
- Delete functionality

### Agents

#### `bq_agent_mick/agent.py`
- BigQuery billing data analysis agent
- Custom instructions for currency formatting
- SQL query generation and execution

#### `bq_agent/agent.py`
- Standard BigQuery agent
- General data analysis capabilities

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Cloud Project with:
  - Vertex AI API enabled
  - BigQuery API enabled
  - Firestore API enabled
  - Appropriate IAM permissions

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd gcp-billing-ai

# Install Python dependencies
pip install -r requirements.txt
pip install -r web/backend/requirements.txt

# Install Node.js dependencies
cd web/frontend
npm install
cd ../..
```

### 2. Configure Environment

Create `.env` files:

**Root `.env`:**
```bash
BQ_PROJECT=your-project-id
GCP_PROJECT_ID=your-project-id
LOCATION=us-central1
```

**Agent-specific `.env` files:**
- `bq_agent_mick/.env`: `REASONING_ENGINE_ID=<deployed-engine-id>`
- `bq_agent/.env`: `REASONING_ENGINE_ID=<deployed-engine-id>`

### 3. Deploy Agents

```bash
# Deploy specific agent
make deploy-bq-agent-mick

# Deploy all agents
make deploy-all-agents
```

### 4. Setup Firestore

```bash
# Enable Firestore API
gcloud services enable firestore.googleapis.com --project=YOUR_PROJECT_ID

# Create Firestore database
gcloud firestore databases create --location=us-central1 --project=YOUR_PROJECT_ID
```

### 5. Start Services

**Terminal 1 - Backend:**
```bash
cd web/backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd web/frontend
npm run dev
```

### 6. Access Application

Open browser: `http://localhost:3000`

---

## Usage

### Web Interface

1. **Select Agent**: Choose agent from dropdown
2. **Send Query**: Type your question and press Enter
3. **View History**: Click history button (📜) to see past queries
4. **Load History**: Click any history item to reload conversation
5. **Delete History**: Use trash icon to delete queries

### Conversation Context

The agent maintains context within a conversation session:

1. **First Query**: Creates new session automatically
2. **Follow-up Queries**: Use same session_id (automatic)
3. **Clear Chat**: Starts new session
4. **Load Old History**: Starts new session (old context not loaded)

**Example Conversation:**
```
User: "What are the top 10 projects by cost?"
Agent: [Shows results with project IDs and costs]

User: "Order them by TLA"
Agent: [Remembers previous query and orders by TLA]
```

### Agent Deployment

**Deploy Single Agent:**
```bash
make deploy-bq-agent-mick
```

**Deploy All Agents:**
```bash
make deploy-all-agents
```

**List Deployments:**
```bash
make list-deployments
```

**Cleanup Old Deployments:**
```bash
make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1
```

---

## API Reference

### Backend Endpoints

#### `GET /agents`
List all available agents.

**Response:**
```json
[
  {
    "name": "bq_agent_mick",
    "display_name": "BigQuery Agent (Mick)",
    "description": "BigQuery billing data analysis agent",
    "reasoning_engine_id": "123456789",
    "is_available": true
  }
]
```

#### `POST /query/stream`
Stream query to agent (recommended).

**Request:**
```json
{
  "agent_name": "bq_agent_mick",
  "message": "What are the top 10 projects?",
  "user_id": "web_user",
  "session_id": "session-123456"  // Optional, for context
}
```

**Response:** Server-Sent Events (SSE) stream
```
data: {"text": "I'll query..."}
data: {"text": " the top 10..."}
data: {"query_id": "abc123", "done": true}
```

#### `GET /history`
Get user's query history.

**Query Parameters:**
- `user_id` (required): User identifier
- `limit` (optional, default: 50): Max number of queries

**Response:**
```json
[
  {
    "id": "doc123",
    "user_id": "web_user",
    "agent_name": "bq_agent_mick",
    "message": "What are the top 10 projects?",
    "response": "Here are the results...",
    "timestamp": "2025-11-05T18:20:33.806283Z"
  }
]
```

#### `DELETE /history/{query_id}`
Delete specific query.

**Query Parameters:**
- `user_id` (required): User identifier

#### `DELETE /history`
Delete all user's history.

**Query Parameters:**
- `user_id` (required): User identifier

---

## Deployment

### Local Development

See [GETTING_STARTED.md](./GETTING_STARTED.md) for local setup.

### Cloud Run Deployment

#### Simple IAP Deployment (No DNS)

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
./deploy-simple-iap.sh
```

**Features:**
- No DNS configuration required
- IAP security enabled
- Quick deployment for course/temporary use

#### Full IAP + Load Balancer Deployment

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
./deploy-all.sh
```

**Features:**
- Custom domain support
- Load balancer
- Full IAP integration
- Production-ready

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment guides.

---

## Troubleshooting

### Agent Not Responding

**Symptoms:** Agent returns errors or doesn't respond

**Solutions:**
1. Check `REASONING_ENGINE_ID` in agent `.env` file
2. Verify agent is deployed: `make list-deployments`
3. Check backend logs for errors
4. Verify BigQuery permissions

### History Not Loading

**Symptoms:** 500 error when loading history

**Solutions:**
1. Enable Firestore API: `gcloud services enable firestore.googleapis.com`
2. Create Firestore database
3. Check backend logs for specific errors
4. Verify Firestore permissions

### Conversation Context Not Working

**Symptoms:** Agent doesn't remember previous messages

**Solutions:**
1. Check backend logs for session_id usage
2. Verify session_id is being passed from frontend
3. Ensure same session_id is used for follow-up queries
4. Check Agent Engine API endpoint includes session_id

### Permission Errors

**Common Issues:**
- BigQuery: Grant `roles/bigquery.dataViewer` and `roles/bigquery.jobUser`
- Firestore: Ensure service account has Firestore access
- Agent Engine: Verify service account has Vertex AI permissions

**Fix Permissions:**
```bash
# BigQuery permissions
make grant-bq-permissions

# Check service accounts
gcloud projects get-iam-policy YOUR_PROJECT_ID
```

---

## Security Considerations

### User Isolation

- Each user's history is isolated by `user_id`
- Firestore queries filter by `user_id`
- Delete operations verify ownership

### Authentication

**Local Development:**
- Uses default GCP credentials
- `gcloud auth application-default login`

**Production:**
- IAP (Identity-Aware Proxy) for web interface
- Service account for backend → Agent Engine
- User ID from authenticated session

### Data Privacy

- Query history stored in Firestore
- User-scoped queries only
- No cross-user data access
- Session IDs are user-specific

---

## Best Practices

### Agent Development

1. **Clear Instructions**: Write explicit agent instructions
2. **Tool Selection**: Use appropriate BigQuery toolsets
3. **Error Handling**: Include error handling in agent logic
4. **Testing**: Test agents locally before deployment

### Deployment

1. **Cleanup**: Regularly clean up old deployments
2. **Monitoring**: Monitor Agent Engine logs
3. **Versioning**: Track agent versions
4. **Backup**: Backup important configurations

### Performance

1. **Session Management**: Reuse sessions for related queries
2. **History Limits**: Limit history retrieval to reasonable sizes
3. **Caching**: Consider caching common queries
4. **Indexing**: Create Firestore indexes for better performance

---

## Future Enhancements

### Planned Features

- [ ] Multi-user authentication
- [ ] Query analytics and insights
- [ ] Export history functionality
- [ ] Agent performance metrics
- [ ] Advanced conversation management
- [ ] Query templates and suggestions
- [ ] Multi-language support

### Integration Opportunities

- Google Cloud Monitoring integration
- Cloud Logging for query analytics
- BigQuery Data Transfer Service
- Cloud Functions for automated tasks
- Cloud Scheduler for periodic queries

---

## Support & Resources

### Documentation

- [Getting Started Guide](./GETTING_STARTED.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Testing Guide](./TESTING_HISTORY.md)
- [Agent Development](./agents/)

### Google Cloud Resources

- [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/docs/agent-builder)
- [ADK Documentation](https://cloud.google.com/vertex-ai/docs/adk)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)

### Troubleshooting

- Check backend logs for detailed error messages
- Review Agent Engine logs in Google Cloud Console
- Verify IAM permissions
- Check Firestore indexes

---

## License

[Add your license information here]

---

## Contributors

[Add contributor information here]


