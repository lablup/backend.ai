#!/usr/bin/env python3
import re
import glob

# Get all test files
test_files = glob.glob("/Users/hyeokjin/dev/lablup/backend.ai/tests/manager/services/session/actions/test_*.py")

for filepath in test_files:
    if filepath.endswith("test_check_and_transit_status.py"):
        continue  # Already fixed
        
    with open(filepath, 'r') as f:
        content = f.read()
    
    modified = False
    
    # Check if this file imports fixture dicts
    if "KERNEL_FIXTURE_DICT" in content and "AGENT_FIXTURE_DICT" not in content:
        # Add AGENT_FIXTURE_DICT to imports
        pattern = r'from \.\.fixtures import \((.*?)\)'
        def add_agent_import(match):
            imports = match.group(1)
            if "AGENT_FIXTURE_DICT" not in imports:
                # Add AGENT_FIXTURE_DICT at the beginning
                lines = [line.strip() for line in imports.split(',')]
                if lines[0]:  # Not empty
                    lines.insert(0, "AGENT_FIXTURE_DICT")
                    return f"from ..fixtures import (\n    {',\n    '.join(lines)}\n)"
            return match.group(0)
        
        content = re.sub(pattern, add_agent_import, content, flags=re.DOTALL)
        modified = True
    
    # Update extra_fixtures to include agents
    if '"sessions":' in content and '"agents":' not in content:
        # Find and update extra_fixtures
        pattern = r'(\{\s*"sessions":\s*\[.*?\],\s*"kernels":\s*\[.*?\]\s*\})'
        def add_agents_fixture(match):
            fixture_dict = match.group(1)
            # Add agents at the beginning
            return fixture_dict.replace(
                '{\n            "sessions"',
                '{\n            "agents": [AGENT_FIXTURE_DICT],\n            "sessions"'
            ).replace(
                '{"sessions"',
                '{"agents": [AGENT_FIXTURE_DICT], "sessions"'
            )
        
        content = re.sub(pattern, add_agents_fixture, content, flags=re.DOTALL)
        modified = True
    
    if modified:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
    else:
        print(f"Skipped: {filepath}")

print("Done!")