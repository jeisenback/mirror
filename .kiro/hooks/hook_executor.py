"""
Hook Execution Error Handler

This module provides utilities for handling hook execution errors including
timeouts, configuration errors, and log write failures.

Requirements: 18.5
"""

import os
import json
import time
import signal
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager


class HookTimeoutError(Exception):
    """Raised when a hook execution exceeds the configured timeout."""
    
    def __init__(self, hook_name: str, timeout_seconds: int):
        self.hook_name = hook_name
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Hook '{hook_name}' exceeded timeout of {timeout_seconds} seconds. "
            f"Validation was skipped to prevent blocking."
        )


class HookConfigurationError(Exception):
    """Raised when a hook configuration is invalid."""
    
    def __init__(self, hook_name: str, reason: str):
        self.hook_name = hook_name
        self.reason = reason
        super().__init__(
            f"Hook '{hook_name}' has invalid configuration: {reason}"
        )


class LogWriteError(Exception):
    """Raised when a hook cannot write to its log file."""
    
    def __init__(self, log_path: str, reason: str):
        self.log_path = log_path
        self.reason = reason
        super().__init__(
            f"Failed to write to log file '{log_path}': {reason}\n"
            f"Suggested actions:\n"
            f"  - Check file permissions\n"
            f"  - Verify disk space is available\n"
            f"  - Ensure parent directory exists"
        )


@contextmanager
def hook_timeout(seconds: int, hook_name: str):
    """
    Context manager for hook execution timeout.
    
    Args:
        seconds: Timeout in seconds
        hook_name: Name of the hook (for error messages)
        
    Raises:
        HookTimeoutError: If execution exceeds timeout
        
    Example:
        with hook_timeout(30, "data-decision-gate"):
            # Hook execution code
            pass
    """
    def timeout_handler(signum, frame):
        raise HookTimeoutError(hook_name, seconds)
    
    # Set up the timeout
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Cancel the alarm and restore old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def load_hook_config(config_path: str = ".kiro/hooks/config.json") -> Dict[str, Any]:
    """
    Load hook configuration from JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary of hook configurations
        
    Raises:
        HookConfigurationError: If configuration is invalid or missing
    """
    if not os.path.exists(config_path):
        raise HookConfigurationError(
            "config",
            f"Configuration file not found at '{config_path}'"
        )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise HookConfigurationError(
            "config",
            f"Invalid JSON in configuration file: {str(e)}"
        )
    except Exception as e:
        raise HookConfigurationError(
            "config",
            f"Failed to read configuration file: {str(e)}"
        )
    
    return config


def validate_hook_config(hook_name: str, config: Dict[str, Any]) -> None:
    """
    Validate a hook configuration has all required fields.
    
    Args:
        hook_name: Name of the hook
        config: Hook configuration dictionary
        
    Raises:
        HookConfigurationError: If configuration is invalid
    """
    required_fields = ['log_path', 'timeout_seconds']
    
    for field in required_fields:
        if field not in config:
            raise HookConfigurationError(
                hook_name,
                f"Missing required field '{field}'"
            )
    
    # Validate timeout is positive
    if not isinstance(config['timeout_seconds'], (int, float)) or config['timeout_seconds'] <= 0:
        raise HookConfigurationError(
            hook_name,
            f"'timeout_seconds' must be a positive number, got {config['timeout_seconds']}"
        )
    
    # Validate log path is a string
    if not isinstance(config['log_path'], str):
        raise HookConfigurationError(
            hook_name,
            f"'log_path' must be a string, got {type(config['log_path'])}"
        )


def safe_write_log(log_path: str, content: str, hook_name: str) -> None:
    """
    Safely write to a log file with error handling.
    
    Args:
        log_path: Path to the log file
        content: Content to write
        hook_name: Name of the hook (for error messages)
        
    Raises:
        LogWriteError: If writing fails
    """
    # Ensure parent directory exists
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            raise LogWriteError(
                log_path,
                f"Failed to create log directory: {str(e)}"
            )
    
    # Try to write the log
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(content)
            f.write('\n\n')
    except PermissionError:
        raise LogWriteError(
            log_path,
            "Permission denied. Check file permissions."
        )
    except OSError as e:
        if e.errno == 28:  # No space left on device
            raise LogWriteError(
                log_path,
                "No space left on device. Free up disk space."
            )
        else:
            raise LogWriteError(
                log_path,
                f"OS error: {str(e)}"
            )
    except Exception as e:
        raise LogWriteError(
            log_path,
            f"Unexpected error: {str(e)}"
        )


def execute_hook_safely(
    hook_func: Callable,
    hook_name: str,
    config: Dict[str, Any],
    *args,
    **kwargs
) -> Optional[Any]:
    """
    Execute a hook function with timeout and error handling.
    
    Args:
        hook_func: The hook function to execute
        hook_name: Name of the hook
        config: Hook configuration
        *args: Positional arguments for the hook function
        **kwargs: Keyword arguments for the hook function
        
    Returns:
        Result of the hook function, or None if bypassed due to timeout
        
    Raises:
        HookConfigurationError: If configuration is invalid
    """
    # Validate configuration
    validate_hook_config(hook_name, config)
    
    timeout_seconds = int(config['timeout_seconds'])
    
    try:
        with hook_timeout(timeout_seconds, hook_name):
            return hook_func(*args, **kwargs)
    except HookTimeoutError as e:
        # Log the timeout and bypass the hook
        print(f"WARNING: {str(e)}")
        
        # Try to log the timeout
        try:
            from .log_utils import format_log_entry, get_iso_timestamp
            log_entry = format_log_entry(
                "Hook Timeout",
                {
                    "Hook Name": hook_name,
                    "Timeout": f"{timeout_seconds} seconds",
                    "Action": "Bypassed to prevent blocking"
                },
                []
            )
            safe_write_log(config['log_path'], log_entry, hook_name)
        except:
            pass  # Don't fail if we can't log the timeout
        
        return None


def get_hook_config(hook_name: str, config_path: str = ".kiro/hooks/config.json") -> Dict[str, Any]:
    """
    Get configuration for a specific hook.
    
    Args:
        hook_name: Name of the hook
        config_path: Path to the configuration file
        
    Returns:
        Hook configuration dictionary
        
    Raises:
        HookConfigurationError: If hook not found or configuration invalid
    """
    config = load_hook_config(config_path)
    
    if hook_name not in config:
        raise HookConfigurationError(
            hook_name,
            f"Hook '{hook_name}' not found in configuration"
        )
    
    hook_config = config[hook_name]
    validate_hook_config(hook_name, hook_config)
    
    return hook_config
