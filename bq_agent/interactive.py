#!/usr/bin/env python3
"""
Interactive prompt mode for bq_agent.

This allows you to have a continuous conversation with the agent,
asking questions in an interactive prompt.

Usage:
    python -m bq_agent.interactive
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (try agent-specific first, then root)
agent_dir = Path(__file__).parent
project_root = agent_dir.parent

# Load agent-specific .env with override=True to ensure it takes precedence
load_dotenv(agent_dir / ".env", override=True)  # Try bq_agent/.env first
# Load root .env without override so agent-specific values aren't overwritten
load_dotenv(project_root / ".env", override=False)  # Then try root .env

PROJECT_ID = os.getenv("BQ_PROJECT") or os.getenv("GCP_PROJECT_ID", "qwiklabs-asl-04-8e9f23e85ced")
LOCATION = os.getenv("LOCATION", "us-central1")
REASONING_ENGINE_ID = os.getenv("REASONING_ENGINE_ID", "")

def query_agent(query_text, user_id="default_user"):
    """Query the deployed Agent Engine."""
    if not REASONING_ENGINE_ID:
        print("✗ Error: REASONING_ENGINE_ID not set")
        print("\nPlease set it in bq_agent/.env file with: REASONING_ENGINE_ID=your-id")
        print("To find your REASONING_ENGINE_ID, run: make list-deployments AGENT_NAME=bq_agent")
        return None
    
    try:
        from google.auth import default
        from google.auth.transport.requests import Request
        import requests
        
        # Get credentials
        credentials, _ = default()
        if not credentials.valid:
            credentials.refresh(Request())
        
        # Build API endpoint
        base_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1"
        endpoint = f"{base_url}/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}:streamQuery"
        
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "input": {
                "message": query_text,
                "user_id": user_id
            }
        }
        
        # Stream the response
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            stream=True,
            timeout=180
        )
        
        if response.status_code != 200:
            print(f"✗ Error: HTTP {response.status_code}")
            print(response.text[:500])
            return None
        
        # Parse streaming JSON response
        import json
        response_text = ""
        
        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    data = json.loads(line)
                    # Extract text from response
                    content = data.get("content", {})
                    if isinstance(content, dict):
                        parts = content.get("parts", [])
                        for part in parts:
                            if isinstance(part, dict):
                                text = part.get("text")
                                if text:
                                    print(text, end='', flush=True)
                                    response_text += text
                except json.JSONDecodeError:
                    # Skip non-JSON lines
                    pass
        
        print()  # New line after response
        return response_text
        
    except Exception as e:
        print(f"✗ Error querying agent: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Interactive prompt loop."""
    print("=" * 80)
    print("bq_agent Interactive Mode")
    print("=" * 80)
    print()
    
    if not REASONING_ENGINE_ID:
        print("✗ Error: REASONING_ENGINE_ID not set")
        print("\nPlease set it in bq_agent/.env file with: REASONING_ENGINE_ID=your-id")
        print("To find your REASONING_ENGINE_ID, run: make list-deployments AGENT_NAME=bq_agent")
        sys.exit(1)
    
    print(f"Connected to Reasoning Engine: {REASONING_ENGINE_ID}")
    print(f"Project: {PROJECT_ID}, Location: {LOCATION}")
    print()
    print("Type your questions below. Type 'exit', 'quit', or 'q' to exit.")
    print("Type 'help' for available commands.")
    print()
    print("-" * 80)
    print()
    
    # Interactive loop
    question_count = 0
    while True:
        try:
            # Get user input
            question = input("🤖 > ").strip()
            
            # Handle empty input
            if not question:
                continue
            
            # Handle exit commands
            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Handle help
            if question.lower() in ['help', 'h']:
                print("\nAvailable commands:")
                print("  exit, quit, q  - Exit interactive mode")
                print("  help, h        - Show this help message")
                print("  clear          - Clear screen")
                print("\nJust type your question to ask the agent!")
                print()
                continue
            
            # Handle clear
            if question.lower() == 'clear':
                os.system('clear' if os.name != 'nt' else 'cls')
                continue
            
            # Query the agent
            question_count += 1
            print()
            print(f"[Question {question_count}]")
            print("-" * 80)
            
            response = query_agent(question)
            
            if response:
                print()
                print("-" * 80)
            
            print()  # Extra newline for readability
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! (Interrupted)")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
            print()


if __name__ == "__main__":
    main()
