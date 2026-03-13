#!/usr/bin/env python3
"""
Test script to apply reasoning review to the requirements document.
"""

import sys
from pathlib import Path

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).parent / ".kiro" / "hooks"))

from reasoning_review import reasoning_review_hook

def main():
    # Read requirements document
    requirements_path = Path(".kiro/specs/reasoning-context-framework/requirements.md")
    
    if not requirements_path.exists():
        print(f"Error: Requirements file not found at {requirements_path}")
        return 1
    
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements_content = f.read()
    
    print("=" * 80)
    print("REASONING REVIEW: Requirements Document")
    print("=" * 80)
    print()
    
    # Apply reasoning review
    should_proceed, failure_reasons = reasoning_review_hook(
        requirements_content,
        workspace_root=Path.cwd(),
        block_on_failure=True
    )
    
    print()
    print("=" * 80)
    print("REVIEW RESULT")
    print("=" * 80)
    print()
    
    if should_proceed:
        print("✓ Requirements document PASSED reasoning review")
        print()
        print("All criteria met:")
        print("  • Factual accuracy validated")
        print("  • Logical consistency confirmed")
        print("  • Completeness verified")
        print("  • Context alignment checked")
        return 0
    else:
        print("✗ Requirements document FAILED reasoning review")
        print()
        print("Failure reasons:")
        for reason in failure_reasons:
            print(f"  • {reason}")
        print()
        print("Review log written to: .kiro/logs/reasoning-reviews.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
