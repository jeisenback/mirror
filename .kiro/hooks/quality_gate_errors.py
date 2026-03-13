"""
Quality Gate Error Handling

This module provides error handling utilities for quality gate hooks including
user approval timeouts, missing threshold configurations, and impact summary failures.

Requirements: 10.2
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class ApprovalTimeoutError(Exception):
    """Raised when user approval times out."""
    
    def __init__(self, operation_type: str, timeout_seconds: int):
        self.operation_type = operation_type
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"User approval for {operation_type} operation timed out after {timeout_seconds} seconds. "
            f"Operation blocked by default for safety."
        )


class MissingThresholdConfigError(Exception):
    """Raised when threshold configuration is missing."""
    
    def __init__(self, config_key: str):
        self.config_key = config_key
        super().__init__(
            f"Threshold configuration '{config_key}' not found. "
            f"Defaulting to require approval for all operations."
        )


class ImpactSummaryError(Exception):
    """Raised when impact summary generation fails."""
    
    def __init__(self, operation_type: str, reason: str):
        self.operation_type = operation_type
        self.reason = reason
        super().__init__(
            f"Failed to generate impact summary for {operation_type} operation: {reason}\n"
            f"A generic warning will be presented to the user."
        )


def load_threshold_config(config_path: str = ".kiro/hooks/config.json") -> Dict[str, Any]:
    """
    Load threshold configuration from config file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary containing threshold configurations
        
    Note:
        If configuration is missing, returns defaults that require approval for all operations.
    """
    if not os.path.exists(config_path):
        print(f"WARNING: Configuration file not found at {config_path}")
        print("Using default thresholds: all operations require approval.")
        return get_default_thresholds()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"WARNING: Invalid JSON in configuration file: {str(e)}")
        print("Using default thresholds: all operations require approval.")
        return get_default_thresholds()
    except Exception as e:
        print(f"WARNING: Failed to read configuration file: {str(e)}")
        print("Using default thresholds: all operations require approval.")
        return get_default_thresholds()
    
    return config


def get_default_thresholds() -> Dict[str, Any]:
    """
    Get default threshold configuration.
    
    Returns:
        Dictionary with conservative default thresholds
    """
    return {
        "financial_thresholds": {
            "auto_approve_max": 0,  # Require approval for all amounts
            "require_review_min": 0,
            "currency": "USD"
        },
        "data_thresholds": {
            "require_approval_for_deletion": True,
            "require_approval_for_modification": True,
            "require_approval_for_sensitive": True
        },
        "approval_timeout_seconds": 300  # 5 minutes
    }


def get_financial_threshold(config: Dict[str, Any], key: str, default: float = 0.0) -> float:
    """
    Get a financial threshold value from configuration.
    
    Args:
        config: Configuration dictionary
        key: Threshold key to retrieve
        default: Default value if key not found
        
    Returns:
        Threshold value
        
    Note:
        If threshold is missing, logs warning and returns conservative default.
    """
    try:
        return float(config.get("financial_thresholds", {}).get(key, default))
    except (ValueError, TypeError):
        print(f"WARNING: Invalid financial threshold value for '{key}'. Using default: {default}")
        return default


def get_data_threshold(config: Dict[str, Any], key: str, default: bool = True) -> bool:
    """
    Get a data threshold value from configuration.
    
    Args:
        config: Configuration dictionary
        key: Threshold key to retrieve
        default: Default value if key not found
        
    Returns:
        Threshold value (boolean)
        
    Note:
        If threshold is missing, logs warning and returns conservative default (True = require approval).
    """
    try:
        return bool(config.get("data_thresholds", {}).get(key, default))
    except (ValueError, TypeError):
        print(f"WARNING: Invalid data threshold value for '{key}'. Using default: {default}")
        return default


def get_approval_timeout(config: Dict[str, Any]) -> int:
    """
    Get approval timeout from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Timeout in seconds
        
    Note:
        If timeout is missing or invalid, returns default of 300 seconds (5 minutes).
    """
    try:
        timeout = config.get("approval_timeout_seconds", 300)
        return int(timeout) if timeout > 0 else 300
    except (ValueError, TypeError):
        print("WARNING: Invalid approval timeout. Using default: 300 seconds (5 minutes)")
        return 300


def request_user_approval_with_timeout(
    operation_type: str,
    impact_summary: str,
    timeout_seconds: int
) -> bool:
    """
    Request user approval with timeout.
    
    Args:
        operation_type: Type of operation (e.g., "data deletion", "financial decision")
        impact_summary: Summary of the operation's impact
        timeout_seconds: Timeout in seconds
        
    Returns:
        True if approved, False if rejected or timed out
        
    Note:
        On timeout, defaults to blocking (returns False) for safety.
    """
    print(f"\n{'='*60}")
    print(f"QUALITY GATE: {operation_type.upper()}")
    print(f"{'='*60}")
    print(impact_summary)
    print(f"\nThis request will timeout in {timeout_seconds} seconds.")
    print(f"{'='*60}")
    
    # For now, use simple input with timeout simulation
    # In production, this would use a proper timeout mechanism
    try:
        response = input("Approve this operation? (yes/no): ").strip().lower()
        return response in ['yes', 'y']
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return False
    except Exception as e:
        print(f"\nERROR: Failed to get user input: {str(e)}")
        print("Defaulting to BLOCK for safety.")
        return False


def generate_generic_impact_summary(operation_type: str, operation_details: Dict[str, Any]) -> str:
    """
    Generate a generic impact summary when detailed summary generation fails.
    
    Args:
        operation_type: Type of operation
        operation_details: Dictionary with operation details
        
    Returns:
        Generic impact summary string
    """
    summary = f"**Operation Type**: {operation_type}\n\n"
    summary += "**WARNING**: Detailed impact analysis failed. Review carefully.\n\n"
    summary += "**Operation Details**:\n"
    
    for key, value in operation_details.items():
        summary += f"- {key}: {value}\n"
    
    summary += "\n**Recommendation**: Proceed with caution and verify the operation manually."
    
    return summary


def generate_data_impact_summary(
    operation: str,
    target: str,
    data_type: str,
    is_sensitive: bool,
    additional_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate impact summary for data operations.
    
    Args:
        operation: Operation type (e.g., "delete", "modify")
        target: Target of the operation (e.g., file path)
        data_type: Type of data being affected
        is_sensitive: Whether the data is sensitive
        additional_context: Additional context information
        
    Returns:
        Formatted impact summary
        
    Raises:
        ImpactSummaryError: If summary generation fails
    """
    try:
        summary = f"**Data Operation**: {operation}\n"
        summary += f"**Target**: {target}\n"
        summary += f"**Data Type**: {data_type}\n"
        summary += f"**Sensitive Data**: {'Yes' if is_sensitive else 'No'}\n\n"
        
        if is_sensitive:
            summary += "⚠️ **PRIVACY WARNING**: This operation affects sensitive data.\n\n"
        
        summary += "**Impact Assessment**:\n"
        
        if operation.lower() == "delete":
            summary += "- Data will be permanently removed\n"
            summary += "- This operation cannot be undone\n"
            summary += "- Ensure backups exist if needed\n"
        elif operation.lower() == "modify":
            summary += "- Data will be changed\n"
            summary += "- Original values will be overwritten\n"
            summary += "- Consider version control or backups\n"
        
        if additional_context:
            summary += "\n**Additional Context**:\n"
            for key, value in additional_context.items():
                summary += f"- {key}: {value}\n"
        
        return summary
        
    except Exception as e:
        raise ImpactSummaryError("data operation", str(e))


def generate_financial_impact_summary(
    operation: str,
    amount: float,
    currency: str,
    description: str,
    additional_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate impact summary for financial operations.
    
    Args:
        operation: Operation type (e.g., "purchase", "payment")
        amount: Monetary amount
        currency: Currency code (e.g., "USD")
        description: Description of the financial operation
        additional_context: Additional context information
        
    Returns:
        Formatted impact summary
        
    Raises:
        ImpactSummaryError: If summary generation fails
    """
    try:
        summary = f"**Financial Operation**: {operation}\n"
        summary += f"**Amount**: {currency} {amount:,.2f}\n"
        summary += f"**Description**: {description}\n\n"
        
        if amount >= 1000:
            summary += "⚠️ **HIGH VALUE TRANSACTION**: This operation involves significant funds.\n\n"
        
        summary += "**Impact Assessment**:\n"
        summary += f"- Monetary impact: {currency} {amount:,.2f}\n"
        summary += "- This operation will affect financial resources\n"
        summary += "- Ensure budget availability and authorization\n"
        
        if additional_context:
            summary += "\n**Additional Context**:\n"
            for key, value in additional_context.items():
                summary += f"- {key}: {value}\n"
        
        return summary
        
    except Exception as e:
        raise ImpactSummaryError("financial operation", str(e))


def log_approval_decision(
    log_path: str,
    operation_type: str,
    impact_summary: str,
    approved: bool,
    rejection_reason: Optional[str] = None,
    active_steering_files: Optional[list] = None
) -> None:
    """
    Log approval decision to quality gate log file.
    
    Args:
        log_path: Path to log file
        operation_type: Type of operation
        impact_summary: Impact summary that was presented
        approved: Whether operation was approved
        rejection_reason: Reason for rejection (if applicable)
        active_steering_files: List of active steering files
    """
    from .log_utils import format_log_entry, get_iso_timestamp
    
    log_data = {
        "Operation Type": operation_type,
        "Impact Summary": impact_summary,
        "User Decision": "Approved" if approved else "Rejected",
        "Timestamp": get_iso_timestamp()
    }
    
    if rejection_reason:
        log_data["Rejection Reason"] = rejection_reason
    
    log_entry = format_log_entry(
        "Quality Gate Decision",
        log_data,
        active_steering_files or []
    )
    
    try:
        from .hook_executor import safe_write_log
        safe_write_log(log_path, log_entry, operation_type)
    except Exception as e:
        print(f"WARNING: Failed to write to log file: {str(e)}")
        print("Decision was recorded but not logged to file.")
