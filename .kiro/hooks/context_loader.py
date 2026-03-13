"""
Context Loader Module

This module provides utilities for loading steering files and building complete
context by following reference chains. It integrates with the reference resolver
to handle the full context composition process.

Requirements: 5.4, 7.1, 18.3
"""

import os
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from reference_resolver import (
    parse_references,
    resolve_relative_path,
    load_referenced_file,
    detect_circular_references,
    resolve_all_references,
    validate_reference_hierarchy,
    CircularReferenceError,
    MissingReferenceError,
    InvalidReferenceError
)


class ContextLoadError(Exception):
    """Raised when context loading fails."""
    pass


class SteeringContext:
    """
    Represents a loaded steering file context with all referenced files.
    """
    
    def __init__(self, root_file: str):
        """
        Initialize a steering context.
        
        Args:
            root_file: Absolute path to the root steering file (typically a task file)
        """
        self.root_file = os.path.normpath(root_file)
        self.files: List[Tuple[str, str]] = []  # List of (path, content) tuples
        self.active_files: List[str] = []  # List of active file paths
        self.errors: List[str] = []  # List of error messages
        self.warnings: List[str] = []  # List of warning messages
    
    def get_active_file_list(self) -> List[str]:
        """
        Get a list of active steering file paths for hook logging.
        
        Returns:
            List of absolute paths to active steering files
        """
        return self.active_files.copy()
    
    def get_combined_content(self) -> str:
        """
        Get all steering file content combined in dependency order.
        
        Returns:
            Combined content from all active steering files
        """
        sections = []
        for file_path, content in self.files:
            sections.append(f"# Context from: {file_path}\n\n{content}\n")
        return "\n---\n\n".join(sections)
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        Get content of a specific file in the context.
        
        Args:
            file_path: Absolute path to the file
            
        Returns:
            File content, or None if not found
        """
        normalized = os.path.normpath(file_path)
        for path, content in self.files:
            if os.path.normpath(path) == normalized:
                return content
        return None
    
    def has_errors(self) -> bool:
        """Check if any errors occurred during loading."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if any warnings occurred during loading."""
        return len(self.warnings) > 0


def load_task_context(task_file_path: str) -> SteeringContext:
    """
    Load a task steering file and all referenced parent files.
    
    This function builds complete context by following the reference chain
    from the task file up through project/role/household and framework files.
    
    Args:
        task_file_path: Absolute path to the task steering file
        
    Returns:
        SteeringContext object containing all loaded files and metadata
        
    Raises:
        ContextLoadError: If context loading fails due to errors
    """
    context = SteeringContext(task_file_path)
    
    # Validate that the file exists
    if not os.path.exists(task_file_path):
        context.errors.append(f"Task file does not exist: {task_file_path}")
        raise ContextLoadError(f"Task file does not exist: {task_file_path}")
    
    # Check for circular references first
    try:
        detect_circular_references(task_file_path)
    except CircularReferenceError as e:
        context.errors.append(str(e))
        raise ContextLoadError(f"Circular reference detected: {' → '.join(e.chain)}")
    except MissingReferenceError as e:
        context.errors.append(str(e))
        raise ContextLoadError(str(e))
    
    # Validate reference hierarchy
    hierarchy_warnings = validate_reference_hierarchy(task_file_path)
    context.warnings.extend(hierarchy_warnings)
    
    # Resolve all references
    try:
        resolved_files = resolve_all_references(task_file_path)
        context.files = resolved_files
        context.active_files = [path for path, _ in resolved_files]
    except CircularReferenceError as e:
        context.errors.append(str(e))
        raise ContextLoadError(f"Circular reference detected: {' → '.join(e.chain)}")
    except MissingReferenceError as e:
        context.errors.append(str(e))
        raise ContextLoadError(str(e))
    except InvalidReferenceError as e:
        context.errors.append(str(e))
        raise ContextLoadError(str(e))
    except Exception as e:
        context.errors.append(f"Unexpected error loading context: {str(e)}")
        raise ContextLoadError(f"Unexpected error loading context: {str(e)}")
    
    return context


def load_steering_file_context(file_path: str) -> SteeringContext:
    """
    Load any steering file and all referenced files.
    
    This is a more general version of load_task_context that works with
    any steering file (household, role, project, task, or framework).
    
    Args:
        file_path: Absolute path to the steering file
        
    Returns:
        SteeringContext object containing all loaded files and metadata
        
    Raises:
        ContextLoadError: If context loading fails due to errors
    """
    return load_task_context(file_path)  # Same implementation


def get_active_steering_files(file_path: str) -> List[str]:
    """
    Get a list of active steering files for a given file.
    
    This is a convenience function for hooks that need just the file list
    without loading full content.
    
    Args:
        file_path: Absolute path to the steering file
        
    Returns:
        List of absolute paths to active steering files
        
    Raises:
        ContextLoadError: If context loading fails
    """
    context = load_steering_file_context(file_path)
    return context.get_active_file_list()


def validate_steering_file(file_path: str) -> Tuple[bool, List[str], List[str]]:
    """
    Validate a steering file without loading full content.
    
    Checks for:
    - File existence
    - Circular references
    - Missing reference targets
    - Invalid reference paths
    - Hierarchy violations
    
    Args:
        file_path: Absolute path to the steering file
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    # Check file exists
    if not os.path.exists(file_path):
        errors.append(f"File does not exist: {file_path}")
        return (False, errors, warnings)
    
    # Check for circular references
    try:
        detect_circular_references(file_path)
    except CircularReferenceError as e:
        errors.append(str(e))
        return (False, errors, warnings)
    except MissingReferenceError as e:
        errors.append(str(e))
        return (False, errors, warnings)
    
    # Validate hierarchy
    hierarchy_warnings = validate_reference_hierarchy(file_path)
    warnings.extend(hierarchy_warnings)
    
    # Try to resolve all references
    try:
        resolve_all_references(file_path)
    except CircularReferenceError as e:
        errors.append(str(e))
        return (False, errors, warnings)
    except MissingReferenceError as e:
        errors.append(str(e))
        return (False, errors, warnings)
    except InvalidReferenceError as e:
        errors.append(str(e))
        return (False, errors, warnings)
    except Exception as e:
        errors.append(f"Unexpected error: {str(e)}")
        return (False, errors, warnings)
    
    is_valid = len(errors) == 0
    return (is_valid, errors, warnings)


def find_steering_file(file_name: str, search_root: Optional[str] = None) -> Optional[str]:
    """
    Find a steering file by name, searching from a root directory.
    
    Args:
        file_name: Name of the file to find (e.g., "context.md")
        search_root: Root directory to search from (defaults to .kiro/steering/)
        
    Returns:
        Absolute path to the file, or None if not found
    """
    if search_root is None:
        # Default to .kiro/steering/ in current working directory
        search_root = os.path.join(os.getcwd(), '.kiro', 'steering')
    
    if not os.path.exists(search_root):
        return None
    
    # Walk the directory tree
    for root, dirs, files in os.walk(search_root):
        if file_name in files:
            return os.path.join(root, file_name)
    
    return None


def get_framework_references(file_path: str) -> List[str]:
    """
    Get all framework steering files referenced from a given file.
    
    Args:
        file_path: Absolute path to the steering file
        
    Returns:
        List of absolute paths to framework steering files
    """
    framework_files = []
    
    try:
        context = load_steering_file_context(file_path)
        for path in context.active_files:
            if '/steering/framework/' in path or '\\steering\\framework\\' in path:
                framework_files.append(path)
    except ContextLoadError:
        pass
    
    return framework_files


def get_reasoning_frameworks(file_path: str) -> List[str]:
    """
    Get all reasoning framework pattern files referenced from a given file.
    
    Args:
        file_path: Absolute path to the steering file
        
    Returns:
        List of absolute paths to reasoning framework pattern files
    """
    reasoning_frameworks = []
    
    try:
        context = load_steering_file_context(file_path)
        for path in context.active_files:
            if '/steering/framework/reasoning-patterns/' in path or \
               '\\steering\\framework\\reasoning-patterns\\' in path:
                reasoning_frameworks.append(path)
    except ContextLoadError:
        pass
    
    return reasoning_frameworks


def get_context_summary(file_path: str) -> Dict[str, any]:
    """
    Get a summary of the context for a steering file.
    
    Args:
        file_path: Absolute path to the steering file
        
    Returns:
        Dictionary with context summary information
    """
    summary = {
        'root_file': file_path,
        'total_files': 0,
        'framework_files': 0,
        'household_files': 0,
        'role_files': 0,
        'project_files': 0,
        'task_files': 0,
        'errors': [],
        'warnings': [],
        'is_valid': False
    }
    
    try:
        context = load_steering_file_context(file_path)
        summary['total_files'] = len(context.active_files)
        summary['errors'] = context.errors
        summary['warnings'] = context.warnings
        summary['is_valid'] = not context.has_errors()
        
        # Count files by layer
        for path in context.active_files:
            if '/steering/framework/' in path or '\\steering\\framework\\' in path:
                summary['framework_files'] += 1
            elif '/steering/household/' in path or '\\steering\\household\\' in path:
                summary['household_files'] += 1
            elif '/steering/roles/' in path or '\\steering\\roles\\' in path:
                summary['role_files'] += 1
            elif '/steering/projects/' in path or '\\steering\\projects\\' in path:
                summary['project_files'] += 1
            elif '/steering/tasks/' in path or '\\steering\\tasks\\' in path:
                summary['task_files'] += 1
    except ContextLoadError as e:
        summary['errors'].append(str(e))
        summary['is_valid'] = False
    
    return summary
