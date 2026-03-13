"""
Reference Resolution Module

This module provides utilities for parsing and resolving references between
steering files in the Reasoning Context Framework. It handles relative path
resolution, circular reference detection, and missing reference target errors.

Requirements: 1.4, 2.4, 3.4, 4.3, 4.4, 5.3, 7.1, 7.2, 7.4, 7.5
"""

import os
import re
from pathlib import Path
from typing import List, Set, Tuple, Optional


class CircularReferenceError(Exception):
    """Raised when a circular reference chain is detected."""
    
    def __init__(self, chain: List[str]):
        self.chain = chain
        chain_str = " → ".join(chain)
        super().__init__(f"Circular reference detected: {chain_str}")


class MissingReferenceError(Exception):
    """Raised when a referenced file does not exist."""
    
    def __init__(self, reference_path: str, source_file: str, suggested_path: Optional[str] = None):
        self.reference_path = reference_path
        self.source_file = source_file
        self.suggested_path = suggested_path
        
        message = f"Missing reference target: '{reference_path}' referenced in '{source_file}'"
        if suggested_path:
            message += f"\nDid you mean: '{suggested_path}'?"
        super().__init__(message)


class InvalidReferenceError(Exception):
    """Raised when a reference path is malformed or invalid."""
    
    def __init__(self, reference_path: str, source_file: str, reason: str):
        self.reference_path = reference_path
        self.source_file = source_file
        self.reason = reason
        super().__init__(
            f"Invalid reference in '{source_file}': '{reference_path}'\n"
            f"Reason: {reason}"
        )


def parse_references(content: str) -> List[str]:
    """
    Parse markdown content to extract steering file references.
    
    References use the format: [[relative/path/to/file.md]]
    
    Args:
        content: Markdown content to parse
        
    Returns:
        List of reference paths found in the content
    """
    # Match [[...]] patterns
    pattern = r'\[\[([^\]]+)\]\]'
    matches = re.findall(pattern, content)
    return matches


def resolve_relative_path(reference_path: str, source_file_path: str) -> str:
    """
    Resolve a relative reference path to an absolute path.
    
    Args:
        reference_path: Relative path from the reference (e.g., "../../household/context.md")
        source_file_path: Absolute path to the file containing the reference
        
    Returns:
        Absolute path to the referenced file
        
    Raises:
        InvalidReferenceError: If the reference path is absolute or malformed
    """
    # Check for absolute paths
    if os.path.isabs(reference_path):
        raise InvalidReferenceError(
            reference_path,
            source_file_path,
            "Reference paths must be relative, not absolute. Use relative paths like '../../household/context.md'"
        )
    
    # Get the directory containing the source file
    source_dir = os.path.dirname(source_file_path)
    
    # Resolve the reference path relative to the source directory
    resolved_path = os.path.normpath(os.path.join(source_dir, reference_path))
    
    return resolved_path


def load_referenced_file(file_path: str) -> str:
    """
    Load the content of a referenced file.
    
    Args:
        file_path: Absolute path to the file to load
        
    Returns:
        Content of the file
        
    Raises:
        MissingReferenceError: If the file does not exist
    """
    if not os.path.exists(file_path):
        # Try to suggest a corrected path
        suggested = _suggest_corrected_path(file_path)
        raise MissingReferenceError(file_path, "unknown", suggested)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Failed to read file '{file_path}': {str(e)}")


def _suggest_corrected_path(file_path: str) -> Optional[str]:
    """
    Suggest a corrected path if the file doesn't exist.
    
    Looks for similar files in the same directory or nearby directories.
    
    Args:
        file_path: Path that doesn't exist
        
    Returns:
        Suggested corrected path, or None if no suggestion available
    """
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    
    # Check if directory exists
    if not os.path.exists(directory):
        # Try to suggest the directory structure
        parent_dir = os.path.dirname(directory)
        if os.path.exists(parent_dir):
            try:
                subdirs = [d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
                if subdirs:
                    # Suggest the first similar directory
                    target_dir_name = os.path.basename(directory)
                    for subdir in subdirs:
                        if subdir.lower() == target_dir_name.lower():
                            return os.path.join(parent_dir, subdir, filename)
            except:
                pass
        return None
    
    # Look for similar filenames in the directory
    try:
        files = os.listdir(directory)
        # Simple case-insensitive match
        for f in files:
            if f.lower() == filename.lower() and f != filename:
                return os.path.join(directory, f)
        
        # Look for files with similar names (e.g., context.md vs Context.md)
        base_name = os.path.splitext(filename)[0]
        for f in files:
            if os.path.splitext(f)[0].lower() == base_name.lower():
                return os.path.join(directory, f)
    except:
        pass
    
    return None


def detect_circular_references(
    file_path: str,
    visited: Optional[Set[str]] = None,
    chain: Optional[List[str]] = None
) -> None:
    """
    Detect circular references in steering file reference chains.
    
    Args:
        file_path: Absolute path to the file to check
        visited: Set of already visited file paths (for recursion)
        chain: Current reference chain (for error reporting)
        
    Raises:
        CircularReferenceError: If a circular reference is detected
        MissingReferenceError: If a referenced file doesn't exist
    """
    if visited is None:
        visited = set()
    if chain is None:
        chain = []
    
    # Normalize the path for comparison
    normalized_path = os.path.normpath(file_path)
    
    # Check if we've seen this file before in the current chain
    if normalized_path in visited:
        # Found a cycle - add the file again to show the complete loop
        chain.append(normalized_path)
        raise CircularReferenceError(chain)
    
    # Check if file exists
    if not os.path.exists(normalized_path):
        source = chain[-1] if chain else "unknown"
        raise MissingReferenceError(normalized_path, source)
    
    # Add to visited set and chain
    visited.add(normalized_path)
    chain.append(normalized_path)
    
    # Load and parse the file
    try:
        content = load_referenced_file(normalized_path)
        references = parse_references(content)
        
        # Recursively check each reference
        for ref in references:
            try:
                resolved_path = resolve_relative_path(ref, normalized_path)
                detect_circular_references(resolved_path, visited.copy(), chain.copy())
            except InvalidReferenceError:
                # Skip invalid references - they'll be caught elsewhere
                pass
    except MissingReferenceError:
        # Re-raise with proper context
        raise
    except Exception as e:
        # Other errors during file loading
        pass
    
    # Remove from chain when backtracking (not from visited - we want to allow DAGs)
    chain.pop()


def resolve_all_references(
    file_path: str,
    visited: Optional[Set[str]] = None
) -> List[Tuple[str, str]]:
    """
    Resolve all references in a file recursively, returning a list of
    (file_path, content) tuples in dependency order.
    
    Args:
        file_path: Absolute path to the starting file
        visited: Set of already visited files (to avoid duplicates)
        
    Returns:
        List of (file_path, content) tuples for all referenced files
        
    Raises:
        CircularReferenceError: If a circular reference is detected
        MissingReferenceError: If a referenced file doesn't exist
        InvalidReferenceError: If a reference path is malformed
    """
    if visited is None:
        visited = set()
    
    result = []
    normalized_path = os.path.normpath(file_path)
    
    # Skip if already visited
    if normalized_path in visited:
        return result
    
    visited.add(normalized_path)
    
    # Load the file
    if not os.path.exists(normalized_path):
        raise MissingReferenceError(normalized_path, "unknown")
    
    content = load_referenced_file(normalized_path)
    references = parse_references(content)
    
    # Recursively resolve references first (depth-first)
    for ref in references:
        resolved_path = resolve_relative_path(ref, normalized_path)
        referenced_files = resolve_all_references(resolved_path, visited)
        result.extend(referenced_files)
    
    # Add this file after its dependencies
    result.append((normalized_path, content))
    
    return result


def validate_reference_hierarchy(file_path: str) -> List[str]:
    """
    Validate that references follow the hierarchy rules:
    - Framework files cannot reference other layers
    - Household files cannot reference roles, projects, or tasks
    - Role files cannot reference projects or tasks
    - Project files cannot reference tasks
    
    Args:
        file_path: Absolute path to the file to validate
        
    Returns:
        List of validation warnings (empty if valid)
    """
    warnings = []
    
    # Determine the layer of the source file
    source_layer = _get_file_layer(file_path)
    
    if source_layer is None:
        return warnings  # Not a steering file
    
    # Load and parse references
    try:
        content = load_referenced_file(file_path)
        references = parse_references(content)
        
        for ref in references:
            try:
                resolved_path = resolve_relative_path(ref, file_path)
                target_layer = _get_file_layer(resolved_path)
                
                if target_layer is None:
                    continue  # Not a steering file
                
                # Check hierarchy rules
                if not _is_valid_reference(source_layer, target_layer):
                    warnings.append(
                        f"Invalid reference hierarchy: {source_layer} layer file "
                        f"'{file_path}' references {target_layer} layer file '{resolved_path}'. "
                        f"This may create circular dependencies."
                    )
            except (InvalidReferenceError, MissingReferenceError):
                # These will be caught by other validation
                pass
    except Exception:
        pass
    
    return warnings


def _get_file_layer(file_path: str) -> Optional[str]:
    """Determine which layer a file belongs to based on its path."""
    normalized = os.path.normpath(file_path)
    
    if '/steering/framework/' in normalized or '\\steering\\framework\\' in normalized:
        return 'framework'
    elif '/steering/household/' in normalized or '\\steering\\household\\' in normalized:
        return 'household'
    elif '/steering/roles/' in normalized or '\\steering\\roles\\' in normalized:
        return 'role'
    elif '/steering/projects/' in normalized or '\\steering\\projects\\' in normalized:
        return 'project'
    elif '/steering/tasks/' in normalized or '\\steering\\tasks\\' in normalized:
        return 'task'
    
    return None


def _is_valid_reference(source_layer: str, target_layer: str) -> bool:
    """Check if a reference from source_layer to target_layer is valid."""
    # Framework can be referenced from anywhere
    if target_layer == 'framework':
        return True
    
    # Define valid reference patterns
    valid_references = {
        'framework': [],  # Framework cannot reference other layers
        'household': [],  # Household cannot reference other layers (except framework, handled above)
        'role': ['household'],
        'project': ['household', 'role'],
        'task': ['household', 'role', 'project']
    }
    
    return target_layer in valid_references.get(source_layer, [])
