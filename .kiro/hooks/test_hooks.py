"""
CLI Utility for Testing Hooks

This script provides a command-line interface for testing individual hooks
with simulated operation types and contexts. It displays hook outputs and
log entries for debugging and validation.

Requirements: Testing strategy
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import argparse


def simulate_data_decision(workspace_root: Path, operation_type: str, file_path: str, **kwargs) -> None:
    """
    Simulate a data decision operation and test the data decision gate hook.
    
    Args:
        workspace_root: Path to workspace root
        operation_type: Type of operation (delete, modify, etc.)
        file_path: Path to file being operated on
        **kwargs: Additional operation parameters
    """
    print("\n" + "=" * 70)
    print("Testing Data Decision Gate Hook")
    print("=" * 70)
    
    # Import the hook
    sys.path.insert(0, str(workspace_root / ".kiro" / "hooks"))
    from data_decision_gate import DataDecisionGate
    
    # Create operation context
    operation = {
        'operation_type': operation_type,
        'file_path': file_path,
        'is_bulk': kwargs.get('is_bulk', False),
        'rationale': kwargs.get('rationale', 'Testing data decision gate')
    }
    
    if kwargs.get('sensitive'):
        operation['content'] = 'password=secret123'
    
    # Execute the gate
    gate = DataDecisionGate(workspace_root)
    
    print(f"\nOperation: {operation_type} {file_path}")
    print(f"Bulk: {operation.get('is_bulk', False)}")
    print(f"Sensitive: {kwargs.get('sensitive', False)}")
    print()
    
    approved = gate.execute(operation)
    
    print("\n" + "-" * 70)
    if approved:
        print("✓ Operation APPROVED")
    else:
        print("✗ Operation REJECTED")
    
    # Display log entry
    log_path = workspace_root / ".kiro" / "logs" / "data-decisions.md"
    if log_path.exists():
        print(f"\nLog entry written to: {log_path}")
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Show last log entry (last 20 lines)
            print("\nLast log entry:")
            print("".join(lines[-20:]))


def simulate_drift_detection(workspace_root: Path, output_file: Optional[str] = None) -> None:
    """
    Simulate AI drift detection on sample output.
    
    Args:
        workspace_root: Path to workspace root
        output_file: Optional path to file containing AI output to test
    """
    print("\n" + "=" * 70)
    print("Testing AI Drift Detection Hook")
    print("=" * 70)
    
    # Import the hook
    sys.path.insert(0, str(workspace_root / ".kiro" / "hooks"))
    from drift_detection import drift_detection_hook
    
    # Get test output
    if output_file:
        output_path = Path(output_file)
        if not output_path.exists():
            print(f"✗ Output file not found: {output_file}")
            return
        with open(output_path, 'r', encoding='utf-8') as f:
            test_output = f.read()
    else:
        # Use default test output
        test_output = """
        This is a very short response.
        """
    
    print(f"\nTesting output ({len(test_output)} characters, {len(test_output.split())} words)")
    print("\nOutput preview:")
    print("-" * 70)
    print(test_output[:200] + ("..." if len(test_output) > 200 else ""))
    print("-" * 70)
    
    # Execute drift detection
    deviations = drift_detection_hook(test_output, workspace_root)
    
    print("\n" + "-" * 70)
    if deviations:
        print(f"✓ Detected {len(deviations)} deviation(s):")
        for dtype, score, desc in deviations:
            print(f"  - {dtype.value} (score: {score:.2f}): {desc}")
    else:
        print("✓ No significant deviations detected")
    
    # Display log entry
    log_path = workspace_root / ".kiro" / "logs" / "ai-drift.md"
    if log_path.exists():
        print(f"\nLog entries in: {log_path}")


def simulate_hallucination_detection(workspace_root: Path, output_file: Optional[str] = None, critical: bool = False) -> None:
    """
    Simulate hallucination detection on sample output.
    
    Args:
        workspace_root: Path to workspace root
        output_file: Optional path to file containing AI output to test
        critical: Whether to test in critical context (requires citations)
    """
    print("\n" + "=" * 70)
    print("Testing Hallucination Detection Hook")
    print("=" * 70)
    
    # Import the hook
    sys.path.insert(0, str(workspace_root / ".kiro" / "hooks"))
    from hallucination_detection import hallucination_detection_hook
    
    # Get test output
    if output_file:
        output_path = Path(output_file)
        if not output_path.exists():
            print(f"✗ Output file not found: {output_file}")
            return
        with open(output_path, 'r', encoding='utf-8') as f:
            test_output = f.read()
    else:
        # Use default test output with factual claims
        test_output = """
        The catalytic converter efficiency is below 95% threshold.
        This requires immediate replacement which will cost approximately $1,200.
        The repair procedure is documented in section 7.3 of the service manual.
        """
    
    print(f"\nTesting output ({len(test_output)} characters)")
    print(f"Critical context: {critical}")
    print("\nOutput preview:")
    print("-" * 70)
    print(test_output[:300] + ("..." if len(test_output) > 300 else ""))
    print("-" * 70)
    
    # Execute hallucination detection
    should_proceed, message, flagged = hallucination_detection_hook(
        test_output,
        workspace_root,
        is_critical_context=critical,
        require_user_confirmation=False  # Non-interactive for testing
    )
    
    print("\n" + "-" * 70)
    if message:
        print(message)
    
    if flagged:
        print(f"\n⚠️  {len(flagged)} claim(s) flagged")
        for claim in flagged:
            print(f"  - {claim.claim_text[:80]}...")
            print(f"    Status: {claim.validation_status.value}")
    else:
        print("✓ No hallucinations detected")


def simulate_reasoning_review(workspace_root: Path, output_file: Optional[str] = None) -> None:
    """
    Simulate reasoning review on sample output.
    
    Args:
        workspace_root: Path to workspace root
        output_file: Optional path to file containing AI output to test
    """
    print("\n" + "=" * 70)
    print("Testing Reasoning Review Hook")
    print("=" * 70)
    
    # Import the hook
    sys.path.insert(0, str(workspace_root / ".kiro" / "hooks"))
    from reasoning_review import reasoning_review_hook
    
    # Get test output
    if output_file:
        output_path = Path(output_file)
        if not output_path.exists():
            print(f"✗ Output file not found: {output_file}")
            return
        with open(output_path, 'r', encoding='utf-8') as f:
            test_output = f.read()
    else:
        # Use default test output
        test_output = """
        Based on the diagnostic procedures, the check engine light indicates
        error code P0420, which suggests a catalytic converter efficiency issue.
        
        Steps to diagnose:
        1. Verify error code with OBD-II scanner
        2. Check oxygen sensor readings
        3. Inspect catalytic converter
        
        Consider that this may require professional inspection if readings are abnormal.
        """
    
    print(f"\nTesting output ({len(test_output)} characters)")
    print("\nOutput preview:")
    print("-" * 70)
    print(test_output[:300] + ("..." if len(test_output) > 300 else ""))
    print("-" * 70)
    
    # Execute reasoning review
    should_proceed, failures = reasoning_review_hook(test_output, workspace_root, block_on_failure=True)
    
    print("\n" + "-" * 70)
    if should_proceed:
        print("✓ Reasoning review PASSED")
    else:
        print("✗ Reasoning review FAILED:")
        if failures:
            for reason in failures:
                print(f"  - {reason}")
    
    # Display log entry
    log_path = workspace_root / ".kiro" / "logs" / "reasoning-reviews.md"
    if log_path.exists():
        print(f"\nLog entry written to: {log_path}")


def simulate_framework_compliance(workspace_root: Path, output_file: Optional[str] = None) -> None:
    """
    Simulate framework compliance checking on sample output.
    
    Args:
        workspace_root: Path to workspace root
        output_file: Optional path to file containing AI output to test
    """
    print("\n" + "=" * 70)
    print("Testing Framework Compliance Hook")
    print("=" * 70)
    
    # Import the hook
    sys.path.insert(0, str(workspace_root / ".kiro" / "hooks"))
    from framework_compliance import framework_compliance_hook
    
    # Get test output
    if output_file:
        output_path = Path(output_file)
        if not output_path.exists():
            print(f"✗ Output file not found: {output_file}")
            return
        with open(output_path, 'r', encoding='utf-8') as f:
            test_output = f.read()
    else:
        # Use default test output with framework steps
        test_output = """
        To diagnose the issue, I'll follow a systematic approach:
        
        Step 1: Verify Error Code
        First, connect the OBD-II scanner to retrieve the diagnostic trouble code.
        
        Step 2: Check Sensor Readings
        Next, examine the oxygen sensor data to determine if sensors are functioning.
        
        Step 3: Inspect Component
        Finally, perform a visual inspection for physical damage.
        """
    
    print(f"\nTesting output ({len(test_output)} characters)")
    print("\nOutput preview:")
    print("-" * 70)
    print(test_output[:300] + ("..." if len(test_output) > 300 else ""))
    print("-" * 70)
    
    # Execute framework compliance check
    is_compliant, message, results = framework_compliance_hook(
        test_output,
        workspace_root,
        flag_non_compliance=True
    )
    
    print("\n" + "-" * 70)
    if is_compliant:
        print("✓ Framework compliance check PASSED")
        if results:
            for fw, status, details in results:
                print(f"  - {fw.name}: {status.value} ({details.get('compliance_rate', 'N/A')})")
    else:
        print("✗ Framework compliance issues detected")
        if message:
            print(message)


def list_available_hooks(workspace_root: Path) -> None:
    """
    List all available hooks from configuration.
    
    Args:
        workspace_root: Path to workspace root
    """
    config_path = workspace_root / ".kiro" / "hooks" / "config.json"
    
    if not config_path.exists():
        print(f"✗ Configuration file not found: {config_path}")
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    hooks = config.get('hooks', {})
    
    print("\n" + "=" * 70)
    print("Available Hooks")
    print("=" * 70)
    
    for hook_name, hook_config in hooks.items():
        enabled = "✓" if hook_config.get('enabled', False) else "✗"
        print(f"\n{enabled} {hook_name}")
        print(f"  Description: {hook_config.get('description', 'No description')}")
        print(f"  Trigger: {hook_config.get('trigger', 'Unknown')}")
        print(f"  Script: {hook_config.get('script', 'Unknown')}")


def main():
    """
    Command-line interface for testing hooks.
    
    Usage:
        python test_hooks.py <hook_type> [options]
    """
    parser = argparse.ArgumentParser(
        description='Test individual hooks with simulated contexts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test data decision gate
  python test_hooks.py data-decision --operation delete --file test.txt
  
  # Test drift detection with custom output
  python test_hooks.py drift --output my_output.txt
  
  # Test hallucination detection in critical context
  python test_hooks.py hallucination --critical
  
  # Test reasoning review
  python test_hooks.py reasoning-review --output my_output.txt
  
  # Test framework compliance
  python test_hooks.py framework-compliance
  
  # List all available hooks
  python test_hooks.py list
        """
    )
    
    parser.add_argument(
        'hook_type',
        choices=['data-decision', 'drift', 'hallucination', 'reasoning-review', 'framework-compliance', 'list'],
        help='Type of hook to test'
    )
    parser.add_argument(
        '--workspace',
        type=str,
        default='.',
        help='Path to workspace root (default: current directory)'
    )
    parser.add_argument(
        '--operation',
        type=str,
        help='Operation type for data decision (delete, modify, etc.)'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='File path for data decision'
    )
    parser.add_argument(
        '--bulk',
        action='store_true',
        help='Mark data decision as bulk operation'
    )
    parser.add_argument(
        '--sensitive',
        action='store_true',
        help='Mark data decision as involving sensitive data'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Path to file containing AI output to test'
    )
    parser.add_argument(
        '--critical',
        action='store_true',
        help='Test hallucination detection in critical context'
    )
    
    args = parser.parse_args()
    
    workspace_root = Path(args.workspace).resolve()
    
    try:
        if args.hook_type == 'list':
            list_available_hooks(workspace_root)
        
        elif args.hook_type == 'data-decision':
            if not args.operation or not args.file:
                print("✗ Error: --operation and --file are required for data-decision")
                sys.exit(1)
            simulate_data_decision(
                workspace_root,
                args.operation,
                args.file,
                is_bulk=args.bulk,
                sensitive=args.sensitive
            )
        
        elif args.hook_type == 'drift':
            simulate_drift_detection(workspace_root, args.output)
        
        elif args.hook_type == 'hallucination':
            simulate_hallucination_detection(workspace_root, args.output, args.critical)
        
        elif args.hook_type == 'reasoning-review':
            simulate_reasoning_review(workspace_root, args.output)
        
        elif args.hook_type == 'framework-compliance':
            simulate_framework_compliance(workspace_root, args.output)
        
        print("\n" + "=" * 70)
        print("Test Complete")
        print("=" * 70)
    
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
