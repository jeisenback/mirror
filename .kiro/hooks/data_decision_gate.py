"""
Data Decision Quality Gate Hook

This hook reviews data operations that affect integrity, privacy, or persistence.
It detects data decisions, generates impact summaries, requests user approval,
and logs all decisions with timestamps and context.

Requirements: 8.1, 8.3, 8.4, 9.1, 9.2, 9.3, 9.4, 9.5
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from log_utils import format_log_entry, append_log_entry


class DataImpactType(Enum):
    """Types of data impact for classification."""
    DELETION = "Deletion"
    MODIFICATION = "Modification"
    SENSITIVE_DATA = "Sensitive Data"
    BULK_OPERATION = "Bulk Operation"


class DataDecisionGate:
    """
    Quality gate hook for data decisions.
    
    Detects data operations, generates impact summaries, requests user approval,
    and logs decisions to .kiro/logs/data-decisions.md.
    """
    
    def __init__(self, workspace_root: Optional[Path] = None):
        """
        Initialize the data decision gate.
        
        Args:
            workspace_root: Path to workspace root. If None, uses current directory.
        """
        self.workspace_root = workspace_root or Path.cwd()
        self.log_path = self.workspace_root / ".kiro" / "logs" / "data-decisions.md"
    
    def detect_operation_type(self, operation: Dict[str, Any]) -> List[DataImpactType]:
        """
        Detect the type of data operation and classify its impact.
        
        Args:
            operation: Dictionary describing the operation with keys:
                - operation_type: str (e.g., 'delete', 'modify', 'create')
                - file_path: str or List[str]
                - content: Optional[str] (for modification operations)
                - is_bulk: Optional[bool]
                
        Returns:
            List of DataImpactType classifications
        """
        impact_types = []
        
        op_type = operation.get('operation_type', '').lower()
        
        # Check for deletion
        if op_type in ['delete', 'remove', 'rm']:
            impact_types.append(DataImpactType.DELETION)
        
        # Check for modification
        if op_type in ['modify', 'update', 'edit', 'write']:
            impact_types.append(DataImpactType.MODIFICATION)
        
        # Check for bulk operations
        if operation.get('is_bulk', False):
            impact_types.append(DataImpactType.BULK_OPERATION)
        
        # Check if multiple files are affected
        file_path = operation.get('file_path', [])
        if isinstance(file_path, list) and len(file_path) > 1:
            impact_types.append(DataImpactType.BULK_OPERATION)
        
        # Check for sensitive data
        if self._contains_sensitive_data(operation):
            impact_types.append(DataImpactType.SENSITIVE_DATA)
        
        return impact_types
    
    def _contains_sensitive_data(self, operation: Dict[str, Any]) -> bool:
        """
        Check if the operation involves sensitive data.
        
        Sensitive data indicators:
        - Files in sensitive directories (credentials, keys, secrets, etc.)
        - Content containing sensitive patterns (passwords, tokens, API keys)
        - Personal information (PII)
        
        Args:
            operation: Operation dictionary
            
        Returns:
            True if sensitive data is detected
        """
        # Check file paths for sensitive directories
        sensitive_dirs = [
            'credentials', 'secrets', 'keys', 'passwords',
            '.ssh', '.aws', '.env', 'private'
        ]
        
        file_path = operation.get('file_path', '')
        if isinstance(file_path, list):
            file_paths = file_path
        else:
            file_paths = [file_path]
        
        for path in file_paths:
            path_lower = str(path).lower()
            if any(sensitive_dir in path_lower for sensitive_dir in sensitive_dirs):
                return True
        
        # Check content for sensitive patterns
        content = operation.get('content', '')
        if content:
            sensitive_patterns = [
                'password', 'api_key', 'secret', 'token',
                'private_key', 'credential', 'ssn', 'social_security'
            ]
            content_lower = content.lower()
            if any(pattern in content_lower for pattern in sensitive_patterns):
                return True
        
        return False
    
    def generate_impact_summary(
        self,
        operation: Dict[str, Any],
        impact_types: List[DataImpactType]
    ) -> str:
        """
        Generate a human-readable impact summary for the data operation.
        
        Args:
            operation: Operation dictionary
            impact_types: List of detected impact types
            
        Returns:
            Formatted impact summary string
        """
        lines = []
        
        # Operation description
        op_type = operation.get('operation_type', 'Unknown')
        lines.append(f"Operation Type: {op_type}")
        
        # Affected files
        file_path = operation.get('file_path', [])
        if isinstance(file_path, list):
            if len(file_path) == 1:
                lines.append(f"Affected File: {file_path[0]}")
            else:
                lines.append(f"Affected Files: {len(file_path)} files")
                for path in file_path[:5]:  # Show first 5
                    lines.append(f"  - {path}")
                if len(file_path) > 5:
                    lines.append(f"  ... and {len(file_path) - 5} more")
        else:
            lines.append(f"Affected File: {file_path}")
        
        # Impact classification
        if impact_types:
            impact_str = ", ".join([t.value for t in impact_types])
            lines.append(f"Impact Classification: {impact_str}")
        
        # Warnings for specific impact types
        if DataImpactType.DELETION in impact_types:
            lines.append("⚠️  WARNING: This operation will permanently delete data")
        
        if DataImpactType.SENSITIVE_DATA in impact_types:
            lines.append("🔒 PRIVACY: This operation involves sensitive data")
        
        if DataImpactType.BULK_OPERATION in impact_types:
            lines.append("📦 BULK: This operation affects multiple files")
        
        # Rationale if provided
        rationale = operation.get('rationale', '')
        if rationale:
            lines.append(f"Rationale: {rationale}")
        
        return "\n".join(lines)
    
    def request_user_approval(self, impact_summary: str) -> Tuple[bool, Optional[str]]:
        """
        Request explicit user approval for the data operation.
        
        Args:
            impact_summary: The generated impact summary
            
        Returns:
            Tuple of (approved: bool, rejection_reason: Optional[str])
        """
        print("\n" + "="*70)
        print("DATA DECISION QUALITY GATE")
        print("="*70)
        print("\nA data operation requires your approval:\n")
        print(impact_summary)
        print("\n" + "-"*70)
        
        while True:
            response = input("\nApprove this operation? (yes/no): ").strip().lower()
            
            if response in ['yes', 'y']:
                return True, None
            elif response in ['no', 'n']:
                reason = input("Please provide a reason for rejection: ").strip()
                return False, reason or "User rejected without providing reason"
            else:
                print("Please enter 'yes' or 'no'")
    
    def execute(self, operation: Dict[str, Any]) -> bool:
        """
        Execute the data decision quality gate.
        
        This is the main entry point for the hook. It:
        1. Detects the operation type and impact
        2. Generates an impact summary
        3. Requests user approval
        4. Logs the decision
        5. Returns whether to proceed with the operation
        
        Args:
            operation: Dictionary describing the data operation
            
        Returns:
            True if operation should proceed, False if blocked
        """
        # Detect impact types
        impact_types = self.detect_operation_type(operation)
        
        # Generate impact summary
        impact_summary = self.generate_impact_summary(operation, impact_types)
        
        # Request user approval
        approved, rejection_reason = self.request_user_approval(impact_summary)
        
        # Prepare log fields
        log_fields = {
            "Operation": operation.get('operation_type', 'Unknown'),
            "Impact": ", ".join([t.value for t in impact_types]) if impact_types else "None",
            "Affected Files": self._format_file_list(operation.get('file_path', [])),
            "Impact Summary": impact_summary,
            "User Decision": "Approved" if approved else "Rejected"
        }
        
        if not approved and rejection_reason:
            log_fields["Rejection Reason"] = rejection_reason
        
        # Log the decision
        try:
            append_log_entry(
                self.log_path,
                "Data Decision",
                log_fields,
                self.workspace_root
            )
        except Exception as e:
            print(f"\nWARNING: Failed to write to log file: {e}")
            print("The operation will still proceed based on your approval.")
        
        return approved
    
    def _format_file_list(self, file_path) -> str:
        """Format file path(s) for logging."""
        if isinstance(file_path, list):
            if len(file_path) == 1:
                return file_path[0]
            else:
                return f"{len(file_path)} files: " + ", ".join(file_path[:3]) + \
                       (f" ... and {len(file_path) - 3} more" if len(file_path) > 3 else "")
        return str(file_path)


def main():
    """
    Command-line interface for testing the data decision gate.
    
    Usage:
        python data_decision_gate.py <operation_type> <file_path> [--bulk] [--sensitive]
    """
    if len(sys.argv) < 3:
        print("Usage: python data_decision_gate.py <operation_type> <file_path> [--bulk] [--sensitive]")
        print("\nExample:")
        print("  python data_decision_gate.py delete /path/to/file.txt")
        print("  python data_decision_gate.py modify credentials/api_keys.json --sensitive")
        sys.exit(1)
    
    operation_type = sys.argv[1]
    file_path = sys.argv[2]
    
    # Parse flags
    is_bulk = '--bulk' in sys.argv
    is_sensitive = '--sensitive' in sys.argv
    
    # Create operation dictionary
    operation = {
        'operation_type': operation_type,
        'file_path': file_path,
        'is_bulk': is_bulk,
        'rationale': 'Testing data decision gate from command line'
    }
    
    # If sensitive flag is set, add sensitive content marker
    if is_sensitive:
        operation['content'] = 'password=secret123'
    
    # Execute the gate
    gate = DataDecisionGate()
    approved = gate.execute(operation)
    
    if approved:
        print("\n✅ Operation APPROVED - would proceed with execution")
        sys.exit(0)
    else:
        print("\n❌ Operation REJECTED - execution blocked")
        sys.exit(1)


if __name__ == '__main__':
    main()
