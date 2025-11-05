#!/usr/bin/env python3
"""
Display agent information: model, prompt/instructions, and configuration.

Usage:
    python -m bq_agent.show_agent_info
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def show_agent_info():
    """Display agent configuration and prompt."""
    try:
        from bq_agent.agent import root_agent
        
        print("=" * 80)
        print("bq_agent Configuration")
        print("=" * 80)
        print()
        
        # Model information
        print("📊 Model:")
        print(f"   {root_agent.model}")
        print()
        
        # Agent name and description
        print("🤖 Agent Details:")
        print(f"   Name: {root_agent.name}")
        print(f"   Description: {root_agent.description}")
        print()
        
        # Tools
        print("🛠️  Tools:")
        if hasattr(root_agent, 'tools') and root_agent.tools:
            for i, tool in enumerate(root_agent.tools, 1):
                tool_name = getattr(tool, 'name', str(type(tool).__name__))
                print(f"   {i}. {tool_name}")
        else:
            print("   No tools configured")
        print()
        
        # Instructions/Prompt
        print("📝 Agent Instructions/Prompt:")
        print("-" * 80)
        if hasattr(root_agent, 'instruction') and root_agent.instruction:
            print(root_agent.instruction)
        else:
            print("   No instructions found")
        print("-" * 80)
        print()
        
        # Summary
        if hasattr(root_agent, 'instruction'):
            print(f"📏 Prompt length: {len(root_agent.instruction)} characters")
        
        print("=" * 80)
        
    except ImportError as e:
        print(f"✗ Error importing agent: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    show_agent_info()
