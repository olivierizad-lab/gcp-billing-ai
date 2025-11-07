# 📚 GCP Billing Agent Documentation

| **Current Version: v1.4.0-rc3** | **Status: Production Ready** | **Auto-Updated** |
| --------------------------- | ---------------------------- | ---------------- |

Welcome to the comprehensive documentation for the GCP Billing Agent Application - a Gen AI solution for analyzing GCP billing data using Google's Agent Development Kit (ADK) and Vertex AI Agent Engine.

## 🌐 **Quick Access**

* **📖 Documentation Index** - Complete documentation directory with all guides and references
* **🏗️ Architecture Guide** - Technical architecture and design decisions with Mermaid diagrams
* **🚀 Deployment Guide** - Step-by-step deployment instructions
* **🔒 Authentication Setup** - Firestore authentication configuration
* **📊 Agent Documentation** - Complete agent implementation details
* **📈 Metrics Dashboard** - Repository analytics and AI effectiveness metrics
* **🔧 Troubleshooting** - Common issues and solutions

## 🎯 **Key Features**

### **Agent Engine Integration**

* **Auto-Discovery**: Automatically discovers deployed reasoning engines from Vertex AI Agent Engine
* **Multi-Agent Support**: Support for multiple BigQuery agents with easy switching
* **Fallback Mechanism**: Environment variable fallback if auto-discovery fails

### **Web Interface**

* **Real-time Streaming**: Watch responses appear in real-time
* **Query History**: View and manage your query history
* **Firestore Authentication**: Secure user authentication with domain restrictions
* **Modern UI**: Clean, modern chat interface built with React

### **Agent Capabilities**

* **BigQuery Analysis**: Query and analyze GCP billing data
* **Natural Language**: Ask questions in natural language
* **Cost Analysis**: Get insights into GCP costs and usage patterns

## 🛠️ **Technology Stack**

* **Frontend**: React 18, Vite, Tailwind CSS
* **Backend**: FastAPI, Python 3.11+
* **Agents**: Google ADK, Google GenAI, Vertex AI Agent Engine
* **Infrastructure**: Cloud Run, Firestore, Vertex AI
* **Authentication**: Custom Firestore-based JWT authentication

## 🚀 **Quick Start**

```bash
# Deploy agents
make deploy-all-agents PROJECT_ID=your-project-id

# Deploy web interface
make deploy-web-simple PROJECT_ID=your-project-id
```

## 📚 **Documentation Sections**

### Getting Started
* [Start Here](START_HERE.md) - Quick start guide for the web interface
* [Getting Started](GETTING_STARTED.md) - Detailed setup instructions
* [Architecture](architecture.md) - Complete system architecture with diagrams

### Deployment
* [Automated Deployment](AUTOMATED_DEPLOYMENT.md) - Automated deployment guide
* [Cloud Run Deployment](DEPLOYMENT_CLOUD_RUN.md) - Cloud Run deployment details
* [Deployment Overview](DEPLOYMENT.md) - General deployment information
* [Backend Deployment](DEPLOYMENT_BACKEND.md) - Backend-specific deployment
* [Frontend Deployment](DEPLOYMENT_FRONTEND.md) - Frontend-specific deployment
* [Deployment FAQ](DEPLOYMENT_FAQ.md) - Common deployment questions

### Authentication & Security
* [Authentication Setup](AUTHENTICATION_SETUP.md) - Firestore authentication configuration
* [Security](SECURITY.md) - Security best practices and architecture

### Agents
* [Agent Overview](agents/) - Overview of available agents
  * [bq_agent_mick](agents/bq_agent_mick.md) - Alternative BigQuery agent implementation
  * [bq_agent](agents/bq_agent.md) - Production-ready BigQuery agent
  * [bq_agent_mick Deployment](agents/bq_agent_mick_deployment.md) - Deployment guide
  * [bq_agent_mick Usage](agents/bq_agent_mick_usage.md) - Usage guide
  * [Deployment Automation](agents/deployment_automation.md) - Agent deployment automation
  * [Deployment Management](agents/deployment_management.md) - Managing deployments
  * [Session Management](agents/session_management.md) - Agent session management

### Solution Documentation
* [Gen AI Solution](GEN_AI_SOLUTION.md) - Complete Gen AI solution overview

### Testing
* [Testing History](TESTING_HISTORY.md) - Testing history and results
* [Test Documentation](tests/tests.md) - Test documentation and guides

---

**📝 Note**: This documentation is automatically updated with every push to the main branch. All guides are consolidated and comprehensive, covering architecture, deployment, security, and troubleshooting.

| **🔄 Last Updated**: 2025-01-27 | **Version**: v1.4.0-rc3 |
| ------------------------------- | ------------------- |

