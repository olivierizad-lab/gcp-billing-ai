# Documentation Index - GCP Billing Agent

This directory contains all project documentation for the GCP Billing Agent Gen AI solution.

## 📚 Documentation Structure

### Getting Started
- **[START_HERE.md](./START_HERE.md)** - Entry point and overview (start here!)
- **[GETTING_STARTED.md](./GETTING_STARTED.md)** - Detailed local development and deployment guide
- **[architecture.md](./architecture.md)** - Complete system architecture with Mermaid diagrams

### Comprehensive Guides
- **[GEN_AI_SOLUTION.md](./GEN_AI_SOLUTION.md)** - Complete solution documentation (architecture, features, API, troubleshooting)

### Deployment Guides
- **[AUTOMATED_DEPLOYMENT.md](./AUTOMATED_DEPLOYMENT.md)** - Fully automated deployment with Firestore authentication
- **[DEPLOYMENT_CLOUD_RUN.md](./DEPLOYMENT_CLOUD_RUN.md)** - Complete Cloud Run deployment guide
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - General deployment information
- **[DEPLOYMENT_BACKEND.md](./DEPLOYMENT_BACKEND.md)** - Backend-specific deployment details
- **[DEPLOYMENT_FRONTEND.md](./DEPLOYMENT_FRONTEND.md)** - Frontend-specific deployment details
- **[DEPLOYMENT_FAQ.md](./DEPLOYMENT_FAQ.md)** - Common deployment questions and answers

### Authentication & Security
- **[AUTHENTICATION_SETUP.md](./AUTHENTICATION_SETUP.md)** - Firestore authentication setup guide
- **[SECURITY.md](./SECURITY.md)** - Security considerations and best practices

### Testing & Troubleshooting
- **[TESTING_HISTORY.md](./TESTING_HISTORY.md)** - Testing the Firestore history feature

### Agent Documentation
- **[agents/](./agents/)** - Agent-specific documentation
  - `bq_agent_mick.md` - bq_agent_mick agent documentation
  - `bq_agent.md` - bq_agent agent documentation
  - `bq_agent_mick_deployment.md` - Deployment guide
  - `bq_agent_mick_usage.md` - Usage guide
  - `session_management.md` - Session management for Agent Engine

---

## 🚀 Quick Navigation

**New to the project?** Start with [START_HERE.md](./START_HERE.md) or [GETTING_STARTED.md](./GETTING_STARTED.md)

**Want to deploy?** Check [AUTOMATED_DEPLOYMENT.md](./AUTOMATED_DEPLOYMENT.md) for the easiest deployment option

**Need comprehensive info?** See [GEN_AI_SOLUTION.md](./GEN_AI_SOLUTION.md)

**Want to understand the architecture?** See [architecture.md](./architecture.md) with Mermaid diagrams

**Troubleshooting?** Check [GEN_AI_SOLUTION.md](./GEN_AI_SOLUTION.md) troubleshooting section or [DEPLOYMENT_FAQ.md](./DEPLOYMENT_FAQ.md)

---

## 📋 Current Deployment Method

The application uses **Firestore Authentication** with custom JWT tokens. Deployment is simplified:
- ✅ **No Load Balancer** required
- ✅ **No DNS** required (uses Cloud Run URLs)
- ✅ **No Firebase Authentication** (uses Firestore directly)
- ✅ **Custom JWT authentication** with domain restrictions
- ✅ **Auto-discovery** of agents from Vertex AI Agent Engine

### Quick Deploy

```bash
# Deploy everything with one command
make deploy-web-simple PROJECT_ID=your-project-id
```

See [AUTOMATED_DEPLOYMENT.md](./AUTOMATED_DEPLOYMENT.md) for details.

---

## 📖 Documentation by Topic

### Architecture & Design
- [architecture.md](./architecture.md) - Complete system architecture with diagrams

### Deployment
- [AUTOMATED_DEPLOYMENT.md](./AUTOMATED_DEPLOYMENT.md) - Automated deployment guide
- [DEPLOYMENT_CLOUD_RUN.md](./DEPLOYMENT_CLOUD_RUN.md) - Cloud Run deployment details
- [DEPLOYMENT.md](./DEPLOYMENT.md) - General deployment info
- [DEPLOYMENT_FAQ.md](./DEPLOYMENT_FAQ.md) - Common questions

### Authentication
- [AUTHENTICATION_SETUP.md](./AUTHENTICATION_SETUP.md) - Firestore auth setup
- [SECURITY.md](./SECURITY.md) - Security best practices

### Agents
- [agents/bq_agent_mick.md](./agents/bq_agent_mick.md) - bq_agent_mick documentation
- [agents/bq_agent.md](./agents/bq_agent.md) - bq_agent documentation
- [agents/bq_agent_mick_deployment.md](./agents/bq_agent_mick_deployment.md) - Agent deployment
- [agents/bq_agent_mick_usage.md](./agents/bq_agent_mick_usage.md) - Agent usage

---

## 🔧 Makefile Commands

The project uses a Makefile for common operations:

```bash
make help                    # Show all available commands
make deploy-web-simple       # Deploy web app to Cloud Run
make deploy-agent-engine     # Deploy agents to Vertex AI
make clean-history           # Clean up Firestore history
```

See the main [README.md](../README.md) for full command list.

---

## 📝 Contributing

When updating documentation:
1. Keep it current with the latest deployment method
2. Remove references to obsolete features (IAP, Load Balancer, Firebase Auth)
3. Update architecture diagrams if needed
4. Test all code examples
