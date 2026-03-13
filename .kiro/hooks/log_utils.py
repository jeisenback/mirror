"""
Hook Log Entry Utilities

This module provides utility functions for creating consistent log entries
across all hook types in the Reasoning Context Framework.

Functions:
- get_iso8601_timestamp(): Generate ISO 8601 formatted timestamps
- get_active_steering_files(): List currently active steering files
- format_log_entry(): Format a complete log entry with required fields
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional


def get_iso8601_timestamp() -> str:
    """
    Generate an ISO 8601 formatted timestamp in UTC.
    
    Returns:
        str: Timestamp in format YYYY-MM-DDTHH:MM:SSZ
        
    Example:
        >>> timestamp = get_iso8601_timestamp()
        >>> print(timestamp)
        2024-02-25T14:30:45Z
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_active_steering_files(workspace_root: Optional[Path] = None) -> List[str]:
    """
    List currently active steering files in the workspace.
    
    This function scans the .kiro/steering/ directory and identifies
    steering files that are currently in use (not in .template directories).
    
    Args:
        workspace_root: Path to workspace root. If None, uses current directory.
        
    Returns:
        List[str]: List of relative paths to active steering files
        
    Example:
        >>> files = get_active_steering_files()
        >>> print(files)
        ['.kiro/steering/household/context.md', 
         '.kiro/steering/roles/non-profit-president/context.md']
    """
    if workspace_root is None:
        workspace_root = Path.cwd()
    else:
        workspace_root = Path(workspace_root)
    
    steering_dir = workspace_root / ".kiro" / "steering"
    
    if not steering_dir.exists():
        return []
    
    active_files = []
    
    # Walk through steering directory
    for md_file in steering_dir.rglob("*.md"):
        # Skip template files
        if ".template" in md_file.parts:
            continue
        
        # Skip README files (they're documentation, not context)
        if md_file.name == "README.md":
            continue
        
        # Get relative path from workspace root
        relative_path = md_file.relative_to(workspace_root)
        active_files.append(str(relative_path).replace("\\", "/"))
    
    return sorted(active_files)


def format_log_entry(
    log_type: str,
    fields: Dict[str, Any],
    workspace_root: Optional[Path] = None
) -> str:
    """
    Format a complete log entry with required fields.
    
    All log entries include:
    - ISO 8601 timestamp
    - Log type (e.g., "Data Decision", "AI Drift Detected")
    - Active steering files
    - Type-specific fields
    
    Args:
        log_type: Type of log entry (e.g., "Data Decision", "Financial Decision")
        fields: Dictionary of type-specific fields to include
        workspace_root: Path to workspace root for finding steering files
        
    Returns:
        str: Formatted markdown log entry
        
    Example:
        >>> entry = format_log_entry(
        ...     "Data Decision",
        ...     {
        ...         "Operation": "Delete file",
        ...         "Impact": "Deletion",
        ...         "User Decision": "Approved"
        ...     }
        ... )
        >>> print(entry)
        ## 2024-02-25T14:30:45Z Data Decision
        
        **Context**: .kiro/steering/household/context.md
        **Operation**: Delete file
        **Impact**: Deletion
        **User Decision**: Approved
    """
    timestamp = get_iso8601_timestamp()
    active_files = get_active_steering_files(workspace_root)
    
    # Build log entry
    lines = [
        f"## {timestamp} {log_type}",
        ""
    ]
    
    # Add context (active steering files)
    if active_files:
        context_list = ", ".join(active_files)
        lines.append(f"**Context**: {context_list}")
    else:
        lines.append("**Context**: No active steering files")
    
    # Add type-specific fields
    for field_name, field_value in fields.items():
        # Handle multi-line values
        if isinstance(field_value, str) and "\n" in field_value:
            lines.append(f"**{field_name}**:")
            lines.append(field_value)
        else:
            lines.append(f"**{field_name}**: {field_value}")
    
    lines.append("")  # Blank line after entry
    
    return "\n".join(lines)


def append_log_entry(
    log_file_path: Path,
    log_type: str,
    fields: Dict[str, Any],
    workspace_root: Optional[Path] = None
) -> None:
    """
    Append a formatted log entry to a log file.
    
    Creates the log file if it doesn't exist. Handles errors gracefully
    by raising exceptions that can be caught by calling code.
    
    Args:
        log_file_path: Path to the log file
        log_type: Type of log entry
        fields: Dictionary of type-specific fields
        workspace_root: Path to workspace root for finding steering files
        
    Raises:
        IOError: If log file cannot be written
        PermissionError: If insufficient permissions to write log file
        
    Example:
        >>> append_log_entry(
        ...     Path(".kiro/logs/data-decisions.md"),
        ...     "Data Decision",
        ...     {"Operation": "Delete file", "User Decision": "Approved"}
        ... )
    """
    # Ensure log directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format the entry
    entry = format_log_entry(log_type, fields, workspace_root)
    
    # Append to log file
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(entry)
