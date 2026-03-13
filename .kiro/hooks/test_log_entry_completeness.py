"""
Property-Based Tests for Hook Log Entry Completeness

Feature: reasoning-context-framework
Property 4: Hook Log Entry Completeness

For any hook execution (quality gate, verification, or logging hook), the resulting
log entry should contain a timestamp in ISO 8601 format, a list of active steering
files at execution time, and all type-specific required fields.

Validates: Requirements 8.3, 8.4, 14.3, 14.4, 15.4, 16.5, 17.5

This test suite uses property-based testing to verify that log entries generated
by all hook types contain the required fields and follow the correct format.
"""

import re
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import pytest

# Import hypothesis for property-based testing
try:
    from hypothesis import given, strategies as st, settings
    from hypothesis.strategies import composite
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    pytest.skip("Hypothesis not installed", allow_module_level=True)

# Import the modules under test
from log_utils import (
    get_iso8601_timestamp,
    get_active_steering_files,
    format_log_entry,
    append_log_entry
)


# ============================================================================
# Strategy Definitions
# ============================================================================

@composite
def log_type_strategy(draw):
    """Generate valid log types for different hook categories."""
    log_types = [
        "Data Decision",
        "Financial Decision",
        "AI Drift Detected",
        "Hallucination Flag",
        "Reasoning Review",
        "Framework Compliance"
    ]
    return draw(st.sampled_from(log_types))


@composite
def data_decision_fields_strategy(draw):
    """Generate fields for data decision log entries."""
    operations = ["Delete file", "Modify sensitive data", "Bulk data operation"]
    impacts = ["Deletion", "Modification", "Sensitive"]
    decisions = ["Approved", "Rejected"]
    
    fields = {
        "Operation": draw(st.sampled_from(operations)),
        "Impact": draw(st.sampled_from(impacts)),
        "Rationale": draw(st.text(min_size=10, max_size=200)),
        "User Decision": draw(st.sampled_from(decisions))
    }
    
    if fields["User Decision"] == "Rejected":
        fields["Rejection Reason"] = draw(st.text(min_size=10, max_size=100))
    
    return fields


@composite
def financial_decision_fields_strategy(draw):
    """Generate fields for financial decision log entries."""
    operations = ["Purchase", "Payment", "Resource allocation", "Financial commitment"]
    decisions = ["Approved", "Rejected"]
    
    fields = {
        "Operation": draw(st.sampled_from(operations)),
        "Amount": f"${draw(st.integers(min_value=1, max_value=10000))}",
        "Threshold": f"${draw(st.integers(min_value=50, max_value=500))}",
        "Rationale": draw(st.text(min_size=10, max_size=200)),
        "User Decision": draw(st.sampled_from(decisions))
    }
    
    if fields["User Decision"] == "Rejected":
        fields["Rejection Reason"] = draw(st.text(min_size=10, max_size=100))
    
    return fields


@composite
def drift_detection_fields_strategy(draw):
    """Generate fields for AI drift detection log entries."""
    deviation_types = ["Response length", "Reasoning pattern", "Output format"]
    
    fields = {
        "Deviation Type": draw(st.sampled_from(deviation_types)),
        "Deviation Score": str(draw(st.floats(min_value=0.1, max_value=1.0))),
        "Expected Pattern": draw(st.text(min_size=20, max_size=100)),
        "Observed Pattern": draw(st.text(min_size=20, max_size=100))
    }
    
    return fields


@composite
def hallucination_fields_strategy(draw):
    """Generate fields for hallucination detection log entries."""
    validation_results = ["Supported", "Unsupported", "Inference"]
    user_actions = ["Confirmed", "Rejected", "Updated Steering"]
    
    fields = {
        "Claim": draw(st.text(min_size=20, max_size=200)),
        "Validation Result": draw(st.sampled_from(validation_results)),
        "User Action": draw(st.sampled_from(user_actions))
    }
    
    return fields


@composite
def reasoning_review_fields_strategy(draw):
    """Generate fields for reasoning review log entries."""
    scores = ["Pass", "Partial", "Fail"]
    
    criteria = ["Factual Accuracy", "Logical Consistency", "Completeness", "Context Alignment"]
    results_lines = []
    
    for criterion in criteria:
        score = draw(st.sampled_from(scores))
        notes = draw(st.text(min_size=10, max_size=100))
        results_lines.append(f"- {criterion}: {score} - {notes}")
    
    overall_pass = draw(st.booleans())
    
    fields = {
        "Review Type": draw(st.sampled_from(["Standard", "Domain-Specific"])),
        "Criteria Applied": ", ".join(criteria),
        "Results": "\n" + "\n".join(results_lines),
        "Overall Status": "Pass" if overall_pass else "Fail",
        "Action": "Proceed" if overall_pass else "Block"
    }
    
    if not overall_pass:
        failure_count = draw(st.integers(min_value=1, max_value=len(criteria)))
        failure_reasons = [f"Criterion {i}: Failed" for i in range(failure_count)]
        fields["Failure Reasons"] = "\n" + "\n".join(f"  - {reason}" for reason in failure_reasons)
    
    return fields


@composite
def framework_compliance_fields_strategy(draw):
    """Generate fields for framework compliance log entries."""
    frameworks = ["Root Cause Analysis", "Decision Tree", "Risk Assessment", "Troubleshooting"]
    compliance_statuses = ["Compliant", "Non-Compliant", "Partial"]
    
    fields = {
        "Framework": draw(st.sampled_from(frameworks)),
        "Compliance Status": draw(st.sampled_from(compliance_statuses)),
        "Validation Notes": draw(st.text(min_size=20, max_size=200))
    }
    
    return fields


@composite
def log_entry_strategy(draw):
    """Generate complete log entry parameters (log type + fields)."""
    log_type = draw(log_type_strategy())
    
    # Generate appropriate fields based on log type
    if log_type == "Data Decision":
        fields = draw(data_decision_fields_strategy())
    elif log_type == "Financial Decision":
        fields = draw(financial_decision_fields_strategy())
    elif log_type == "AI Drift Detected":
        fields = draw(drift_detection_fields_strategy())
    elif log_type == "Hallucination Flag":
        fields = draw(hallucination_fields_strategy())
    elif log_type == "Reasoning Review":
        fields = draw(reasoning_review_fields_strategy())
    elif log_type == "Framework Compliance":
        fields = draw(framework_compliance_fields_strategy())
    else:
        # Generic fields for unknown types
        fields = {
            "Field1": draw(st.text(min_size=5, max_size=100)),
            "Field2": draw(st.text(min_size=5, max_size=100))
        }
    
    return (log_type, fields)


# ============================================================================
# Property Tests
# ============================================================================

class TestTimestampFormat:
    """Test that timestamps are always in ISO 8601 format."""
    
    @settings(max_examples=100)
    @given(st.integers(min_value=0, max_value=1000))
    def test_timestamp_is_iso8601_format(self, _iteration):
        """
        Property: All generated timestamps must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).
        
        Feature: reasoning-context-framework, Property 4: Hook Log Entry Completeness
        """
        timestamp = get_iso8601_timestamp()
        
        # Verify ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
        iso8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
        assert re.match(iso8601_pattern, timestamp), \
            f"Timestamp '{timestamp}' does not match ISO 8601 format"
        
        # Verify it's a valid datetime
        try:
            parsed = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
            assert parsed is not None
        except ValueError as e:
            pytest.fail(f"Timestamp '{timestamp}' is not a valid datetime: {e}")
    
    @settings(max_examples=100)
    @given(log_entry_strategy())
    def test_log_entry_contains_timestamp(self, log_params):
        """
        Property: All log entries must contain a timestamp in the header.
        
        Feature: reasoning-context-framework, Property 4: Hook Log Entry Completeness
        """
        log_type, fields = log_params
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            entry = format_log_entry(log_type, fields, workspace_root)
            
            # Extract header line (first line starting with ##)
            header_match = re.search(r'^## (.+)$', entry, re.MULTILINE)
            assert header_match, "Log entry must have a header starting with ##"
            
            header = header_match.group(1)
            
            # Verify timestamp is in header
            iso8601_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'
            assert re.search(iso8601_pattern, header), \
                f"Log entry header must contain ISO 8601 timestamp: {header}"


class TestActiveSteeringFiles:
    """Test that log entries always include active steering files context."""
    
    @settings(max_examples=100)
    @given(log_entry_strategy())
    def test_log_entry_contains_context_field(self, log_params):
        """
        Property: All log entries must contain a Context field listing active steering files.
        
        Feature: reasoning-context-framework, Property 4: Hook Log Entry Completeness
        """
        log_type, fields = log_params
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            entry = format_log_entry(log_type, fields, workspace_root)
            
            # Verify Context field exists
            context_pattern = r'\*\*Context\*\*:'
            assert re.search(context_pattern, entry), \
                "Log entry must contain **Context**: field"
    
    @settings(max_examples=50)
    @given(
        log_entry_strategy(),
        st.lists(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N')) | st.just('-') | st.just('_')), min_size=0, max_size=5)
    )
    def test_context_field_lists_steering_files(self, log_params, steering_file_names):
        """
        Property: Context field must list all active steering files or indicate none are active.
        
        Feature: reasoning-context-framework, Property 4: Hook Log Entry Completeness
        """
        log_type, fields = log_params
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            steering_dir = workspace_root / ".kiro" / "steering"
            
            # Create steering files with sanitized names
            created_files = []
            for name in steering_file_names:
                # Sanitize name to avoid invalid path characters
                safe_name = name.replace('/', '_').replace('\\', '_').strip()
                if not safe_name:
                    continue
                    
                # Create a valid steering file path
                file_path = steering_dir / "test" / f"{safe_name}.md"
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("# Test Steering File\n\nContent here.")
                created_files.append(str(file_path.relative_to(workspace_root)).replace("\\", "/"))
            
            entry = format_log_entry(log_type, fields, workspace_root)
            
            # Extract context field value
            context_match = re.search(r'\*\*Context\*\*:\s*(.+)', entry)
            assert context_match, "Context field must have a value"
            
            context_value = context_match.group(1).strip()
            
            if created_files:
                # Verify all created files are mentioned in context
                for file_path in created_files:
                    assert file_path in context_value, \
                        f"Active steering file '{file_path}' must be listed in Context field"
            else:
                # Verify "No active steering files" message
                assert "No active steering files" in context_value, \
                    "Context field must indicate when no steering files are active"


class TestTypeSpecificFields:
    """Test that log entries contain all required type-specific fields."""
    
    @settings(max_examples=100)
    @given(data_decision_fields_strategy())
    def test_data_decision_required_fields(self, fields):
        """
        Property: Data Decision log entries must contain Operation, Impact, Rationale, and User Decision.
        
        Feature: reasoning-context-framework, Property 4: Hook Log Entry Completeness
        Validates: Requirements 8.3, 8.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            entry = format_log_entry("Data Decision", fields, workspace_root)
            
            # Verify required fields
            assert re.search(r'\*\*Operation\*\*:', entry), "Must contain Operation field"
            assert re.search(r'\*\*Impact\*\*:', entry), "Must contain Impact field"
            assert re.search(r'\*\*Rationale\*\*:', entry), "Must contain Rationale field"
            assert re.search(r'\*\*User Decision\*\*:', entry), "Must contain User Decision field"
            
            # If rejected, must have rejection reason
            if fields["User Decision"] == "Rejected":
                assert re.search(r'\*\*Rejection Reason\*\*:', entry), \
                    "Rejected decisions must contain Rejection Reason field"
    
    @settings(max_examples=100)
    @given(financial_decision_fields_strategy())
    def test_financial_decision_required_fields(self, fields):
        """
        Property: Financial Decision log entries must contain Operation, Amount, and User Decision.
        
        Feature: reasoning-context-framework, Property 4: Hook Log Entry Completeness
        Validates: Requirements 8.3, 8.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            entry = format_log_entry("Financial Decision", fields, workspace_root)
            
            # Verify required fields
            assert re.search(r'\*\*Operation\*\*:', entry), "Must contain Operation field"
            assert re.search(r'\*\*Amount\*\*:', entry), "Must contain Amount field"
            assert re.search(r'\*\*User Decision\*\*:', entry), "Must contain User Decision field"
            
            # If rejected, must have rejection reason
            if fields["User Decision"] == "Rejected":
                assert re.search(r'\*\*Rejection Reason\*\*:', entry), \
                    "Rejected decisions must contain Rejection Reason field"
    
    @settings(max_examples=100)
    @given(drift_detection_fields_strategy())
    def test_drift_detection_required_fields(self, fields):
        """
        Property: AI Drift log entries must contain Deviation Type, Score, Expected and Observed patterns.
        
        Feature: reasoning-context-framework, Property 4: Hook Log Entry Completeness
        Validates: Requirements 14.3, 14.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            entry = format_log_entry("AI Drift Detected", fields, workspace_root)
            
            # Verify required fields
            assert re.search(r'\*\*Deviation Type\*\*:', entry), "Must contain Deviation Type field"
            assert re.search(r'\*\*Deviation Score\*\*:', entry), "Must contain Deviation Score field"
            assert re.search(r'\*\*Expected Pattern\*\*:', entry), "Must contain Expected Pattern field"
            assert re.search(r'\*\*Observed Pattern\*\*:', entry), "Must contain Observed Pattern field"
    
    @settings(max_examples=100)
    @given(hallucination_fields_strategy())
    def test_hallucination_detection_required_fields(self, fields):
        """
        Property: Hallucination Flag log entries must contain Claim, Validation Result, and User Action.
        
        Feature: reasoning-context-framework, Property 4: Hook Log Entry Completeness
        Validates: Requirements 15.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            entry = format_log_entry("Hallucination Flag", fields, workspace_root)
            
            # Verify required fields
            assert re.search(r'\*\*Claim\*\*:', entry), "Must contain Claim field"
            assert re.search(r'\*\*Validation Result\*\*:', entry), "Must contain Validation Result field"
            assert re.search(r'\*\*User Action\*\*:', entry), "Must contain User Action field"
    
    @settings(max_examples=100)
    @given(reasoning_review_fields_strategy())
    def test_reasoning_review_required_fields(self, fields):
        """
        Property: Reasoning Review log entries must contain Review Type, Criteria, Results, Status, and Action.
        
        Feature: reasoning-context-framework, Property 4: Hook Log Entry Completeness
        Validates: Requirements 16.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            entry = format_log_entry("Reasoning Review", fields, workspace_root)
            
            # Verify required fields
            assert re.search(r'\*\*Review Type\*\*:', entry), "Must contain Review Type field"
            assert re.search(r'\*\*Criteria Applied\*\*:', entry), "Must contain Criteria Applied field"
            assert re.search(r'\*\*Results\*\*:', entry), "Must contain Results field"
            assert re.search(r'\*\*Overall Status\*\*:', entry), "Must contain Overall Status field"
            assert re.search(r'\*\*Action\*\*:', entry), "Must contain Action field"
            
            # If failed, must have failure reasons
            if fields["Overall Status"] == "Fail":
                assert re.search(r'\*\*Failure Reasons\*\*:', entry), \
                    "Failed reviews must contain Failure Reasons field"
    
    @settings(max_examples=100)
    @given(framework_compliance_fields_strategy())
    def test_framework_compliance_required_fields(self, fields):
        """
        Property: Framework Compliance log entries must contain Framework, Compliance Status, and Notes.
        
        Feature: reasoning-context-framework, Property 4: Hook Log Entry Completeness
        Validates: Requirements 17.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            entry = format_log_entry("Framework Compliance", fields, workspace_root)
            
            # Verify required fields
            assert re.search(r'\*\*Framework\*\*:', entry), "Must contain Framework field"
            assert re.search(r'\*\*Compliance Status\*\*:', entry), "Must contain Compliance Status field"
            assert re.search(r'\*\*Validation Notes\*\*:', entry), "Must contain Validation Notes field"


class TestLogEntryStructure:
    """Test overall log entry structure and format."""
    
    @settings(max_examples=100)
    @given(log_entry_strategy())
    def test_log_entry_has_markdown_header(self, log_params):
        """
        Property: All log entries must start with a markdown header (##).
        
        Feature: reasoning-context-framework, Property 4: Hook Log Entry Completeness
        """
        log_type, fields = log_params
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            entry = format_log_entry(log_type, fields, workspace_root)
            
            # Verify starts with ##
            assert entry.startswith("##"), "Log entry must start with markdown header (##)"
            
            # Verify log type is in header
            first_line = entry.split('\n')[0]
            assert log_type in first_line, f"Log type '{log_type}' must be in header"
    
    @settings(max_examples=100)
    @given(log_entry_strategy())
    def test_log_entry_ends_with_blank_line(self, log_params):
        """
        Property: All log entries must end with a blank line for separation.
        
        Feature: reasoning-context-framework, Property 4: Hook Log Entry Completeness
        """
        log_type, fields = log_params
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            entry = format_log_entry(log_type, fields, workspace_root)
            
            # Verify ends with newline
            assert entry.endswith('\n'), "Log entry must end with newline"
    
    @settings(max_examples=100)
    @given(log_entry_strategy())
    def test_log_entry_fields_use_bold_markdown(self, log_params):
        """
        Property: All field names in log entries must use bold markdown (**Field Name**:).
        
        Feature: reasoning-context-framework, Property 4: Hook Log Entry Completeness
        """
        log_type, fields = log_params
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            entry = format_log_entry(log_type, fields, workspace_root)
            
            # Verify Context field uses bold
            assert re.search(r'\*\*Context\*\*:', entry), "Context field must use bold markdown"
            
            # Verify all provided fields use bold
            for field_name in fields.keys():
                pattern = rf'\*\*{re.escape(field_name)}\*\*:'
                assert re.search(pattern, entry), \
                    f"Field '{field_name}' must use bold markdown (**{field_name}**:)"


class TestLogFileAppending:
    """Test that log entries are correctly appended to log files."""
    
    @settings(max_examples=50, deadline=None)
    @given(
        log_entry_strategy(),
        st.lists(log_entry_strategy(), min_size=1, max_size=5)
    )
    def test_multiple_entries_appended_correctly(self, first_entry, additional_entries):
        """
        Property: Multiple log entries appended to the same file must all be present and complete.
        
        Feature: reasoning-context-framework, Property 4: Hook Log Entry Completeness
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            log_file = workspace_root / ".kiro" / "logs" / "test.md"
            
            # Append first entry
            log_type, fields = first_entry
            append_log_entry(log_file, log_type, fields, workspace_root)
            
            # Append additional entries
            for log_type, fields in additional_entries:
                append_log_entry(log_file, log_type, fields, workspace_root)
            
            # Read log file
            content = log_file.read_text(encoding='utf-8')
            
            # Count headers (each entry should have one)
            header_count = len(re.findall(r'^##', content, re.MULTILINE))
            expected_count = 1 + len(additional_entries)
            
            assert header_count == expected_count, \
                f"Log file should contain {expected_count} entries, found {header_count}"
            
            # Verify each entry has required structure
            entries = re.split(r'^##', content, flags=re.MULTILINE)[1:]  # Skip empty first element
            
            for entry in entries:
                # Each entry should have Context field
                assert re.search(r'\*\*Context\*\*:', entry), \
                    "Each log entry must contain Context field"
                
                # Each entry should have timestamp in header
                first_line = entry.split('\n')[0]
                iso8601_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'
                assert re.search(iso8601_pattern, first_line), \
                    "Each log entry header must contain ISO 8601 timestamp"


# ============================================================================
# Integration Tests
# ============================================================================

class TestRealWorldScenarios:
    """Test log entry completeness in realistic scenarios."""
    
    def test_data_decision_with_rejection(self):
        """Test complete data decision log entry with rejection."""
        fields = {
            "Operation": "Delete user data",
            "Impact": "Deletion",
            "Rationale": "User requested account deletion",
            "User Decision": "Rejected",
            "Rejection Reason": "Need to verify user identity first"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            
            # Create some steering files
            steering_dir = workspace_root / ".kiro" / "steering" / "household"
            steering_dir.mkdir(parents=True)
            (steering_dir / "context.md").write_text("# Household Context\n")
            
            entry = format_log_entry("Data Decision", fields, workspace_root)
            
            # Verify all required elements
            assert re.search(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', entry.split('\n')[0].replace('## ', ''))
            assert "**Context**:" in entry
            assert "**Operation**: Delete user data" in entry
            assert "**Impact**: Deletion" in entry
            assert "**User Decision**: Rejected" in entry
            assert "**Rejection Reason**: Need to verify user identity first" in entry
            assert ".kiro/steering/household/context.md" in entry
    
    def test_reasoning_review_with_failures(self):
        """Test complete reasoning review log entry with failures."""
        fields = {
            "Review Type": "Domain-Specific",
            "Criteria Applied": "Factual Accuracy, Logical Consistency, Completeness, Context Alignment",
            "Results": "\n- Factual Accuracy: Fail - 3 unsupported claims\n- Logical Consistency: Pass - No contradictions\n- Completeness: Pass - All elements present\n- Context Alignment: Partial - Limited constraint acknowledgment",
            "Overall Status": "Fail",
            "Action": "Block",
            "Failure Reasons": "\n  - Factual Accuracy: 3 unsupported claims detected\n  - Context Alignment: Only 2/10 constraints acknowledged"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_root = Path(tmpdir)
            entry = format_log_entry("Reasoning Review", fields, workspace_root)
            
            # Verify all required elements
            assert "Reasoning Review" in entry
            assert "**Review Type**: Domain-Specific" in entry
            assert "**Criteria Applied**:" in entry
            assert "**Results**:" in entry
            assert "Factual Accuracy: Fail" in entry
            assert "**Overall Status**: Fail" in entry
            assert "**Action**: Block" in entry
            assert "**Failure Reasons**:" in entry


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
