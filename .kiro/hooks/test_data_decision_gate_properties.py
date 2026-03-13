"""
Property-Based Tests for Data Decision Quality Gate

Feature: reasoning-context-framework
Property 5: Data Decision Approval and Blocking
Property 6: Sensitive Data Privacy Marking
Property 7: Data Decision Impact Summary

For any data decision operation (deletion or modification of data), the quality gate
hook should require explicit user approval before execution, and if the user rejects
the decision, the hook should block execution and log the rejection reason.

For any data decision involving sensitive information, the quality gate hook should
flag the operation with privacy markers in the log entry.

For any data decision operation, the quality gate hook should generate and present
a summary of data impact before requesting user approval.

Validates: Requirements 9.2, 9.3, 9.4, 9.5
"""

import pytest
from hypothesis import given, strategies as st, settings
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from io import StringIO

from data_decision_gate import DataDecisionGate, DataImpactType


# Strategies for generating test data

@st.composite
def operation_type_strategy(draw):
    """Generate valid operation types."""
    return draw(st.sampled_from([
        'delete', 'remove', 'rm',
        'modify', 'update', 'edit', 'write',
        'create', 'add'
    ]))


@st.composite
def file_path_strategy(draw):
    """Generate file paths, including sensitive paths."""
    # Mix of normal and sensitive paths
    normal_paths = st.text(
        alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='/-_.'),
        min_size=5,
        max_size=50
    ).filter(lambda x: len(x.strip()) > 0)
    
    sensitive_paths = st.sampled_from([
        'credentials/api_keys.json',
        'secrets/passwords.txt',
        '.ssh/id_rsa',
        '.aws/credentials',
        '.env',
        'private/keys.pem',
        'config/database_passwords.yml'
    ])
    
    return draw(st.one_of(normal_paths, sensitive_paths))


@st.composite
def content_strategy(draw):
    """Generate content, including sensitive content."""
    # Mix of normal and sensitive content
    normal_content = st.text(min_size=0, max_size=200)
    
    sensitive_content = st.sampled_from([
        'password=secret123',
        'api_key=sk_live_abc123',
        'secret_token=xyz789',
        'private_key=-----BEGIN RSA PRIVATE KEY-----',
        'credential=admin:password',
        'ssn=123-45-6789',
        'social_security_number=987654321'
    ])
    
    return draw(st.one_of(normal_content, sensitive_content))


@st.composite
def data_operation_strategy(draw):
    """Generate complete data operation dictionaries."""
    op_type = draw(operation_type_strategy())
    
    # Generate single or multiple file paths
    is_bulk = draw(st.booleans())
    if is_bulk:
        file_path = draw(st.lists(file_path_strategy(), min_size=2, max_size=10))
    else:
        file_path = draw(file_path_strategy())
    
    operation = {
        'operation_type': op_type,
        'file_path': file_path,
        'is_bulk': is_bulk,
        'rationale': draw(st.text(min_size=0, max_size=100))
    }
    
    # Add content for modification operations
    if op_type in ['modify', 'update', 'edit', 'write']:
        operation['content'] = draw(content_strategy())
    
    return operation


# Property 5: Data Decision Approval and Blocking
# Feature: reasoning-context-framework, Property 5: For any data decision operation
# (deletion or modification of data), the quality gate hook should require explicit
# user approval before execution, and if the user rejects the decision, the hook
# should block execution and log the rejection reason.

@settings(max_examples=100)
@given(operation=data_operation_strategy())
def test_property_5_approval_required_for_data_decisions(operation):
    """
    Property 5: Data Decision Approval and Blocking
    
    For any data decision operation (deletion or modification), the hook should:
    1. Require explicit user approval
    2. Block execution if user rejects
    3. Log the rejection reason
    
    Validates: Requirements 9.2, 9.5
    """
    # Setup with temporary directory
    tmp_path = Path(tempfile.mkdtemp())
    try:
        gate = DataDecisionGate(workspace_root=tmp_path)
    
    # Only test deletion and modification operations
    op_type = operation['operation_type'].lower()
    if op_type not in ['delete', 'remove', 'rm', 'modify', 'update', 'edit', 'write']:
        return  # Skip non-data-decision operations
    
    # Test with user approval
    with patch('builtins.input', side_effect=['yes']):
        with patch('sys.stdout', new_callable=StringIO):
            approved = gate.execute(operation)
    
    assert approved is True, \
        f"Operation should be approved when user says 'yes' for {op_type}"
    
    # Verify log entry was created
    assert gate.log_path.exists(), "Log file should be created"
    log_content = gate.log_path.read_text()
    assert "User Decision: Approved" in log_content, \
        "Log should contain approval decision"
    
    # Test with user rejection
    rejection_reason = "Test rejection reason"
    with patch('builtins.input', side_effect=['no', rejection_reason]):
        with patch('sys.stdout', new_callable=StringIO):
            rejected = gate.execute(operation)
    
    assert rejected is False, \
        f"Operation should be blocked when user says 'no' for {op_type}"
    
    # Verify rejection was logged with reason
    log_content = gate.log_path.read_text()
    assert "User Decision: Rejected" in log_content, \
        "Log should contain rejection decision"
    assert rejection_reason in log_content, \
        "Log should contain the rejection reason provided by user"
    finally:
        # Cleanup
        if tmp_path.exists():
            shutil.rmtree(tmp_path)


# Property 6: Sensitive Data Privacy Marking
# Feature: reasoning-context-framework, Property 6: For any data decision involving
# sensitive information, the quality gate hook should flag the operation with privacy
# markers in the log entry.

@settings(max_examples=100)
@given(operation=data_operation_strategy())
def test_property_6_sensitive_data_privacy_marking(operation):
    """
    Property 6: Sensitive Data Privacy Marking
    
    For any data decision involving sensitive information, the hook should:
    1. Detect sensitive data
    2. Flag the operation with privacy markers in the log
    
    Validates: Requirements 9.3
    """
    # Setup with temporary directory
    tmp_path = Path(tempfile.mkdtemp())
    try:
        gate = DataDecisionGate(workspace_root=tmp_path)
    
    # Detect if operation involves sensitive data
    impact_types = gate.detect_operation_type(operation)
    has_sensitive_data = DataImpactType.SENSITIVE_DATA in impact_types
    
    # Execute with approval
    with patch('builtins.input', return_value='yes'):
        with patch('sys.stdout', new_callable=StringIO):
            gate.execute(operation)
    
    # Read log content
    assert gate.log_path.exists(), "Log file should be created"
    log_content = gate.log_path.read_text()
    
    if has_sensitive_data:
        # Verify privacy marker is present
        assert "Sensitive Data" in log_content, \
            "Log should contain 'Sensitive Data' marker for sensitive operations"
        
        # Verify the impact summary includes privacy warning
        assert "🔒 PRIVACY" in log_content or "PRIVACY" in log_content, \
            "Impact summary should include privacy warning for sensitive data"
    else:
        # For non-sensitive operations, we don't require the marker
        # (but it's okay if it's there due to false positives)
        pass
    finally:
        # Cleanup
        if tmp_path.exists():
            shutil.rmtree(tmp_path)


# Property 7: Data Decision Impact Summary
# Feature: reasoning-context-framework, Property 7: For any data decision operation,
# the quality gate hook should generate and present a summary of data impact before
# requesting user approval.

@settings(max_examples=100)
@given(operation=data_operation_strategy())
def test_property_7_impact_summary_generation(operation):
    """
    Property 7: Data Decision Impact Summary
    
    For any data decision operation, the hook should:
    1. Generate an impact summary
    2. Present the summary before requesting approval
    3. Include the summary in the log entry
    
    Validates: Requirements 9.4
    """
    # Setup with temporary directory
    tmp_path = Path(tempfile.mkdtemp())
    try:
        gate = DataDecisionGate(workspace_root=tmp_path)
    
    # Detect impact types
    impact_types = gate.detect_operation_type(operation)
    
    # Generate impact summary
    impact_summary = gate.generate_impact_summary(operation, impact_types)
    
    # Verify impact summary is not empty
    assert impact_summary, "Impact summary should not be empty"
    assert len(impact_summary) > 0, "Impact summary should have content"
    
    # Verify impact summary contains key information
    assert "Operation Type:" in impact_summary, \
        "Impact summary should include operation type"
    
    # Verify file information is included
    file_path = operation.get('file_path', [])
    if isinstance(file_path, list):
        if len(file_path) == 1:
            assert "Affected File:" in impact_summary, \
                "Impact summary should mention affected file for single file"
        else:
            assert "Affected Files:" in impact_summary, \
                "Impact summary should mention affected files for multiple files"
    else:
        assert "Affected File:" in impact_summary, \
            "Impact summary should mention affected file"
    
    # Verify impact classification is included if there are impact types
    if impact_types:
        assert "Impact Classification:" in impact_summary, \
            "Impact summary should include impact classification"
    
    # Execute operation and verify summary is in log
    with patch('builtins.input', return_value='yes'):
        with patch('sys.stdout', new_callable=StringIO):
            gate.execute(operation)
    
    # Verify log contains the impact summary
    assert gate.log_path.exists(), "Log file should be created"
    log_content = gate.log_path.read_text()
    
    assert "Impact Summary" in log_content, \
        "Log should contain 'Impact Summary' field"
    
    # Verify key elements of the summary are in the log
    assert operation['operation_type'] in log_content, \
        "Log should contain the operation type from the summary"
    finally:
        # Cleanup
        if tmp_path.exists():
            shutil.rmtree(tmp_path)


# Additional property: Verify log entry completeness for data decisions
# This validates that all required fields are present in the log

@settings(max_examples=100)
@given(operation=data_operation_strategy())
def test_data_decision_log_entry_completeness(operation):
    """
    Verify that data decision log entries contain all required fields.
    
    This test validates Property 4 (Hook Log Entry Completeness) specifically
    for data decision operations.
    
    Validates: Requirements 8.3, 8.4
    """
    # Setup with temporary directory
    tmp_path = Path(tempfile.mkdtemp())
    try:
        gate = DataDecisionGate(workspace_root=tmp_path)
    
    # Execute with approval
    with patch('builtins.input', return_value='yes'):
        with patch('sys.stdout', new_callable=StringIO):
            gate.execute(operation)
    
    # Read log content
    assert gate.log_path.exists(), "Log file should be created"
    log_content = gate.log_path.read_text()
    
    # Verify required fields are present
    required_fields = [
        "## ",  # Timestamp header
        "Data Decision",  # Log type
        "Context:",  # Active steering files
        "Operation:",  # Operation type
        "Impact:",  # Impact classification
        "Affected Files:",  # File information
        "Impact Summary:",  # Impact summary
        "User Decision:"  # Approval/rejection
    ]
    
    for field in required_fields:
        assert field in log_content, \
            f"Log entry should contain required field: {field}"
    
    # Verify timestamp format (ISO 8601)
    import re
    timestamp_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'
    assert re.search(timestamp_pattern, log_content), \
        "Log entry should contain ISO 8601 timestamp"
    finally:
        # Cleanup
        if tmp_path.exists():
            shutil.rmtree(tmp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
