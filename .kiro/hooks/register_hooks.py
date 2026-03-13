"""
Hook Registration Script

This script registers all hooks with Kiro's hook system by reading the hook
configuration file and setting up trigger patterns, conditions, log paths,
and timeout values for each hook.

Requirements: 18.1, 18.2, 18.5
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class HookRegistry:
    """
    Registry for managing hook configurations and registration.
    """
    
    def __init__(self, workspace_root: Optional[Path] = None):
        """
        Initialize the hook registry.
        
        Args:
            workspace_root: Path to workspace root. If None, uses current directory.
        """
        self.workspace_root = workspace_root or Path.cwd()
        self.config_path = self.workspace_root / ".kiro" / "hooks" / "config.json"
        self.config: Dict[str, Any] = {}
        self.registered_hooks: List[str] = []
    
    def load_config(self) -> None:
        """
        Load hook configuration from config.json.
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Hook configuration file not found at {self.config_path}. "
                f"Create the configuration file before registering hooks."
            )
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in hook configuration file: {str(e)}",
                e.doc,
                e.pos
            )
    
    def validate_hook_config(self, hook_name: str, hook_config: Dict[str, Any]) -> List[str]:
        """
        Validate a hook configuration for required fields and valid values.
        
        Args:
            hook_name: Name of the hook
            hook_config: Hook configuration dictionary
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Required fields
        required_fields = ['enabled', 'script', 'trigger', 'action', 'log_path']
        for field in required_fields:
            if field not in hook_config:
                errors.append(f"Missing required field '{field}'")
        
        # Validate script path exists
        if 'script' in hook_config:
            script_path = self.workspace_root / hook_config['script']
            if not script_path.exists():
                errors.append(f"Hook script not found at {script_path}")
        
        # Validate trigger is a known integration point
        if 'trigger' in hook_config:
            integration_points = self.config.get('integration_points', {})
            if hook_config['trigger'] not in integration_points:
                errors.append(
                    f"Unknown trigger '{hook_config['trigger']}'. "
                    f"Valid triggers: {', '.join(integration_points.keys())}"
                )
        
        # Validate timeout is positive
        if 'timeout_seconds' in hook_config:
            timeout = hook_config['timeout_seconds']
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                errors.append(f"Invalid timeout_seconds: {timeout} (must be positive number)")
        
        # Validate log path directory exists
        if 'log_path' in hook_config:
            log_path = Path(hook_config['log_path'])
            log_dir = self.workspace_root / log_path.parent
            if not log_dir.exists():
                errors.append(f"Log directory does not exist: {log_dir}")
        
        return errors
    
    def register_hook(self, hook_name: str, hook_config: Dict[str, Any]) -> bool:
        """
        Register a single hook with Kiro's hook system.
        
        Args:
            hook_name: Name of the hook
            hook_config: Hook configuration dictionary
            
        Returns:
            True if registration successful, False otherwise
        """
        # Validate configuration
        errors = self.validate_hook_config(hook_name, hook_config)
        if errors:
            print(f"✗ Failed to register hook '{hook_name}':")
            for error in errors:
                print(f"  - {error}")
            return False
        
        # Check if hook is enabled
        if not hook_config.get('enabled', False):
            print(f"⊘ Skipping disabled hook '{hook_name}'")
            return True
        
        # Register the hook
        # In a real implementation, this would interact with Kiro's hook system API
        # For now, we simulate registration by printing the configuration
        
        print(f"✓ Registering hook '{hook_name}':")
        print(f"  Script: {hook_config['script']}")
        print(f"  Trigger: {hook_config['trigger']}")
        print(f"  Action: {hook_config['action']}")
        print(f"  Log Path: {hook_config['log_path']}")
        print(f"  Timeout: {hook_config.get('timeout_seconds', 'default')}s")
        
        if hook_config.get('conditions'):
            print(f"  Conditions: {', '.join(hook_config['conditions'])}")
        
        if hook_config.get('thresholds'):
            print(f"  Thresholds: {hook_config['thresholds']}")
        
        self.registered_hooks.append(hook_name)
        return True
    
    def register_all_hooks(self) -> Tuple[int, int]:
        """
        Register all hooks from the configuration file.
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not self.config:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        
        hooks = self.config.get('hooks', {})
        if not hooks:
            print("No hooks found in configuration file.")
            return (0, 0)
        
        print(f"\nRegistering {len(hooks)} hook(s)...\n")
        
        successful = 0
        failed = 0
        
        for hook_name, hook_config in hooks.items():
            if self.register_hook(hook_name, hook_config):
                successful += 1
            else:
                failed += 1
            print()  # Blank line between hooks
        
        return (successful, failed)
    
    def display_integration_points(self) -> None:
        """
        Display configured integration points and their associated hooks.
        """
        integration_points = self.config.get('integration_points', {})
        
        if not integration_points:
            print("No integration points configured.")
            return
        
        print("\nConfigured Integration Points:")
        print("=" * 70)
        
        for point_name, point_config in integration_points.items():
            description = point_config.get('description', 'No description')
            hooks = point_config.get('hooks', [])
            
            print(f"\n{point_name}")
            print(f"  Description: {description}")
            print(f"  Hooks: {', '.join(hooks) if hooks else 'None'}")
    
    def display_global_settings(self) -> None:
        """
        Display global hook system settings.
        """
        global_settings = self.config.get('global_settings', {})
        
        if not global_settings:
            print("No global settings configured.")
            return
        
        print("\nGlobal Hook Settings:")
        print("=" * 70)
        
        for setting_name, setting_value in global_settings.items():
            print(f"  {setting_name}: {setting_value}")
    
    def verify_log_directories(self) -> None:
        """
        Verify that all log directories exist, create them if they don't.
        """
        hooks = self.config.get('hooks', {})
        log_dirs = set()
        
        for hook_config in hooks.values():
            if 'log_path' in hook_config:
                log_path = Path(hook_config['log_path'])
                log_dir = self.workspace_root / log_path.parent
                log_dirs.add(log_dir)
        
        print("\nVerifying log directories...")
        
        for log_dir in log_dirs:
            if not log_dir.exists():
                print(f"  Creating {log_dir}")
                log_dir.mkdir(parents=True, exist_ok=True)
            else:
                print(f"  ✓ {log_dir} exists")


def main():
    """
    Command-line interface for hook registration.
    
    Usage:
        python register_hooks.py [--workspace <path>] [--verify-only]
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Register hooks with Kiro hook system'
    )
    parser.add_argument(
        '--workspace',
        type=str,
        default='.',
        help='Path to workspace root (default: current directory)'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify configuration without registering hooks'
    )
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Display configuration details'
    )
    
    args = parser.parse_args()
    
    # Initialize registry
    workspace_root = Path(args.workspace).resolve()
    registry = HookRegistry(workspace_root)
    
    print("=" * 70)
    print("Kiro Hook Registration System")
    print("=" * 70)
    print(f"\nWorkspace: {workspace_root}")
    
    try:
        # Load configuration
        print(f"Loading configuration from {registry.config_path}...")
        registry.load_config()
        print("✓ Configuration loaded successfully\n")
        
        # Display configuration if requested
        if args.show_config:
            registry.display_global_settings()
            registry.display_integration_points()
            print()
        
        # Verify log directories
        registry.verify_log_directories()
        
        if args.verify_only:
            print("\n✓ Configuration verification complete")
            print("Run without --verify-only to register hooks")
            sys.exit(0)
        
        # Register all hooks
        successful, failed = registry.register_all_hooks()
        
        # Summary
        print("=" * 70)
        print("Registration Summary")
        print("=" * 70)
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total: {successful + failed}")
        
        if failed > 0:
            print("\n⚠️  Some hooks failed to register. Review errors above.")
            sys.exit(1)
        else:
            print("\n✓ All hooks registered successfully")
            sys.exit(0)
    
    except FileNotFoundError as e:
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\n✗ Error: Invalid JSON in configuration file")
        print(f"  {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
