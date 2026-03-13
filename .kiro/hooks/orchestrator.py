"""
Hook Orchestration Module

This module coordinates hook execution order, passes active steering file context
to all hooks, and handles hook failures and blocking. It ensures quality gates
execute before verification hooks and manages the complete hook lifecycle.

Requirements: 18.2, 18.3, 18.4
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from enum import Enum

from log_utils import get_active_steering_files


class HookPhase(Enum):
    """Execution phases for hooks."""
    QUALITY_GATE = "quality_gate"
    VERIFICATION = "verification"
    LOGGING = "logging"


class HookResult(Enum):
    """Result status from hook execution."""
    PASS = "pass"
    FAIL = "fail"
    BLOCK = "block"
    TIMEOUT = "timeout"
    ERROR = "error"


class HookExecutionResult:
    """Container for hook execution results."""
    
    def __init__(self, hook_name: str, result: HookResult, message: Optional[str] = None):
        self.hook_name = hook_name
        self.result = result
        self.message = message
        self.execution_time: float = 0.0
        self.should_block: bool = (result == HookResult.BLOCK)
    
    def __repr__(self):
        return f"HookExecutionResult({self.hook_name}, {self.result.value}, block={self.should_block})"


class HookOrchestrator:
    """
    Orchestrates hook execution across all integration points.
    
    Responsibilities:
    - Load hook configuration
    - Determine execution order (quality gates before verification)
    - Pass active steering file context to hooks
    - Handle timeouts and failures
    - Coordinate blocking behavior
    """
    
    def __init__(self, workspace_root: Optional[Path] = None):
        """
        Initialize the hook orchestrator.
        
        Args:
            workspace_root: Path to workspace root. If None, uses current directory.
        """
        self.workspace_root = workspace_root or Path.cwd()
        self.config_path = self.workspace_root / ".kiro" / "hooks" / "config.json"
        self.config: Dict[str, Any] = {}
        self.active_steering_files: List[str] = []
    
    def load_config(self) -> None:
        """
        Load hook configuration from config.json.
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Hook configuration file not found at {self.config_path}"
            )
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def refresh_active_steering_files(self) -> None:
        """
        Refresh the list of active steering files from the workspace.
        """
        self.active_steering_files = get_active_steering_files(self.workspace_root)
    
    def classify_hook_phase(self, hook_name: str, hook_config: Dict[str, Any]) -> HookPhase:
        """
        Classify a hook into its execution phase.
        
        Args:
            hook_name: Name of the hook
            hook_config: Hook configuration dictionary
            
        Returns:
            HookPhase classification
        """
        # Quality gate hooks require user approval
        if 'gate' in hook_name.lower() or hook_config.get('action') in [
            'require_user_approval',
            'require_user_approval_if_threshold_exceeded'
        ]:
            return HookPhase.QUALITY_GATE
        
        # Verification hooks validate outputs
        if any(term in hook_name.lower() for term in ['detection', 'review', 'compliance', 'validation']):
            return HookPhase.VERIFICATION
        
        # Default to logging phase
        return HookPhase.LOGGING
    
    def get_hooks_for_trigger(self, trigger: str) -> List[Tuple[str, Dict[str, Any], HookPhase]]:
        """
        Get all hooks for a specific trigger, sorted by execution phase.
        
        Args:
            trigger: Trigger name (e.g., 'before_file_operation')
            
        Returns:
            List of (hook_name, hook_config, phase) tuples, sorted by phase
        """
        hooks = self.config.get('hooks', {})
        matching_hooks = []
        
        for hook_name, hook_config in hooks.items():
            # Skip disabled hooks
            if not hook_config.get('enabled', False):
                continue
            
            # Check if hook matches trigger
            if hook_config.get('trigger') == trigger:
                phase = self.classify_hook_phase(hook_name, hook_config)
                matching_hooks.append((hook_name, hook_config, phase))
        
        # Sort by phase: quality gates first, then verification, then logging
        phase_order = {
            HookPhase.QUALITY_GATE: 0,
            HookPhase.VERIFICATION: 1,
            HookPhase.LOGGING: 2
        }
        matching_hooks.sort(key=lambda x: phase_order[x[2]])
        
        return matching_hooks
    
    def execute_hook(
        self,
        hook_name: str,
        hook_config: Dict[str, Any],
        operation_context: Dict[str, Any]
    ) -> HookExecutionResult:
        """
        Execute a single hook with timeout and error handling.
        
        Args:
            hook_name: Name of the hook
            hook_config: Hook configuration dictionary
            operation_context: Context about the operation being hooked
            
        Returns:
            HookExecutionResult with execution status
        """
        start_time = time.time()
        timeout = hook_config.get('timeout_seconds', self.config.get('global_settings', {}).get('default_timeout_seconds', 30))
        
        try:
            # Add active steering files to context
            operation_context['active_steering_files'] = self.active_steering_files
            operation_context['workspace_root'] = str(self.workspace_root)
            
            # Import and execute the hook script
            # In a real implementation, this would dynamically import and call the hook
            # For now, we simulate execution
            
            script_path = hook_config.get('script', '')
            
            # Simulate hook execution
            print(f"  Executing hook: {hook_name}")
            print(f"    Script: {script_path}")
            print(f"    Context: {len(self.active_steering_files)} active steering files")
            
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout:
                result = HookExecutionResult(hook_name, HookResult.TIMEOUT, f"Hook exceeded timeout of {timeout}s")
                result.execution_time = elapsed
                return result
            
            # Simulate success
            result = HookExecutionResult(hook_name, HookResult.PASS, "Hook executed successfully")
            result.execution_time = time.time() - start_time
            return result
        
        except Exception as e:
            elapsed = time.time() - start_time
            result = HookExecutionResult(hook_name, HookResult.ERROR, f"Hook execution failed: {str(e)}")
            result.execution_time = elapsed
            return result
    
    def handle_hook_failure(
        self,
        result: HookExecutionResult,
        hook_config: Dict[str, Any]
    ) -> bool:
        """
        Handle hook execution failure and determine if operation should be blocked.
        
        Args:
            result: HookExecutionResult from failed hook
            hook_config: Hook configuration dictionary
            
        Returns:
            True if operation should be blocked, False if it can proceed
        """
        action = hook_config.get('action', '')
        default_action = self.config.get('global_settings', {}).get('hook_failure_default_action', 'block')
        
        # Handle timeout
        if result.result == HookResult.TIMEOUT:
            print(f"  ⚠️  Hook '{result.hook_name}' timed out after {result.execution_time:.2f}s")
            print(f"     Bypassing hook to prevent blocking user")
            # Timeouts don't block by default (fail-open for availability)
            return False
        
        # Handle error
        if result.result == HookResult.ERROR:
            print(f"  ✗ Hook '{result.hook_name}' failed: {result.message}")
            
            # Check if hook should block on error
            if 'block' in action.lower() or default_action == 'block':
                print(f"     Blocking operation due to hook failure")
                return True
            else:
                print(f"     Allowing operation to proceed despite error")
                return False
        
        # Handle explicit block result
        if result.result == HookResult.BLOCK:
            print(f"  🛑 Hook '{result.hook_name}' blocked operation: {result.message}")
            return True
        
        return False
    
    def execute_hooks_for_trigger(
        self,
        trigger: str,
        operation_context: Dict[str, Any]
    ) -> Tuple[bool, List[HookExecutionResult]]:
        """
        Execute all hooks for a specific trigger in the correct order.
        
        Args:
            trigger: Trigger name (e.g., 'before_file_operation')
            operation_context: Context about the operation being hooked
            
        Returns:
            Tuple of (should_proceed, results)
            - should_proceed: True if operation should proceed, False if blocked
            - results: List of HookExecutionResult objects
        """
        # Refresh active steering files
        self.refresh_active_steering_files()
        
        # Get hooks for this trigger
        hooks = self.get_hooks_for_trigger(trigger)
        
        if not hooks:
            print(f"No hooks configured for trigger '{trigger}'")
            return (True, [])
        
        print(f"\nExecuting {len(hooks)} hook(s) for trigger '{trigger}':")
        
        results = []
        should_proceed = True
        
        # Execute hooks in phase order
        for hook_name, hook_config, phase in hooks:
            print(f"\n  Phase: {phase.value}")
            
            # Execute the hook
            result = self.execute_hook(hook_name, hook_config, operation_context)
            results.append(result)
            
            print(f"    Result: {result.result.value} ({result.execution_time:.3f}s)")
            
            # Handle failures
            if result.result in [HookResult.FAIL, HookResult.BLOCK, HookResult.ERROR, HookResult.TIMEOUT]:
                if self.handle_hook_failure(result, hook_config):
                    should_proceed = False
                    # Stop executing remaining hooks if blocked
                    break
        
        return (should_proceed, results)
    
    def execute_operation_with_hooks(
        self,
        trigger: str,
        operation_context: Dict[str, Any],
        operation_func: Optional[Callable] = None
    ) -> Tuple[bool, Any, List[HookExecutionResult]]:
        """
        Execute an operation with hook orchestration.
        
        This is the main entry point for integrating hooks into operations.
        
        Args:
            trigger: Trigger name for the operation
            operation_context: Context about the operation
            operation_func: Optional function to execute if hooks pass
            
        Returns:
            Tuple of (success, result, hook_results)
            - success: True if operation completed successfully
            - result: Result from operation_func (None if not executed)
            - hook_results: List of HookExecutionResult objects
        """
        # Execute hooks
        should_proceed, hook_results = self.execute_hooks_for_trigger(trigger, operation_context)
        
        if not should_proceed:
            print(f"\n🛑 Operation blocked by hooks")
            return (False, None, hook_results)
        
        # Execute the operation if provided
        if operation_func:
            try:
                print(f"\n✓ All hooks passed, executing operation...")
                result = operation_func()
                return (True, result, hook_results)
            except Exception as e:
                print(f"\n✗ Operation failed: {str(e)}")
                return (False, None, hook_results)
        
        return (True, None, hook_results)


def main():
    """
    Command-line interface for testing hook orchestration.
    
    Usage:
        python orchestrator.py <trigger> [--context key=value ...]
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test hook orchestration'
    )
    parser.add_argument(
        'trigger',
        type=str,
        help='Trigger name to test (e.g., before_file_operation)'
    )
    parser.add_argument(
        '--context',
        nargs='*',
        help='Context key=value pairs'
    )
    parser.add_argument(
        '--workspace',
        type=str,
        default='.',
        help='Path to workspace root (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Parse context
    operation_context = {}
    if args.context:
        for item in args.context:
            if '=' in item:
                key, value = item.split('=', 1)
                operation_context[key] = value
    
    # Initialize orchestrator
    workspace_root = Path(args.workspace).resolve()
    orchestrator = HookOrchestrator(workspace_root)
    
    print("=" * 70)
    print("Hook Orchestration Test")
    print("=" * 70)
    print(f"\nWorkspace: {workspace_root}")
    print(f"Trigger: {args.trigger}")
    print(f"Context: {operation_context}")
    
    try:
        # Load configuration
        orchestrator.load_config()
        
        # Execute hooks
        should_proceed, results = orchestrator.execute_hooks_for_trigger(
            args.trigger,
            operation_context
        )
        
        # Summary
        print("\n" + "=" * 70)
        print("Execution Summary")
        print("=" * 70)
        print(f"  Should Proceed: {should_proceed}")
        print(f"  Hooks Executed: {len(results)}")
        
        for result in results:
            status_icon = "✓" if result.result == HookResult.PASS else "✗"
            print(f"    {status_icon} {result.hook_name}: {result.result.value}")
        
        sys.exit(0 if should_proceed else 1)
    
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
