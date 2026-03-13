# Hook Property-Based Tests

This directory contains property-based tests for the Reasoning Context Framework hooks.

## Setup

Install test dependencies:

```bash
pip install -r test_requirements.txt
```

## Running Tests

### Run all property tests for log entry completeness:

```bash
cd .kiro/hooks
python -m pytest test_log_entry_completeness.py -v
```

### Run with coverage:

```bash
python -m pytest test_log_entry_completeness.py --cov=log_utils --cov-report=html
```

### Run specific test class:

```bash
python -m pytest test_log_entry_completeness.py::TestTimestampFormat -v
```

### Run with more examples (default is 100):

```bash
python -m pytest test_log_entry_completeness.py --hypothesis-show-statistics
```

## Test Structure

### test_reference_resolution.py

Property-based tests for reference resolution utilities.

**Properties Tested:**
- Property 1: Hierarchical Reference Resolution
- Property 2: Relative Path References  
- Property 3: Circular Reference Detection

**Validates Requirements:** 1.4, 2.4, 3.4, 4.3, 4.4, 5.3, 6.4, 7.4

**Test Cases:**
- `test_property_hierarchical_reference_resolution`: Validates that references between valid hierarchy layers resolve correctly
- `test_property_relative_path_references`: Validates that absolute paths are rejected
- `test_property_relative_path_references_valid`: Validates that relative paths are accepted
- `test_property_circular_reference_detection`: Validates that circular references don't cause infinite loops in resolve_all_references
- `test_property_circular_reference_detection_acyclic`: Validates that acyclic graphs work correctly
- `test_property_hierarchical_reference_resolution_dag`: Validates that DAG structures (multiple files referencing same target) work
- `test_property_circular_reference_detection_self_reference`: Validates that self-references are handled gracefully
- `test_property_circular_reference_detection_direct_cycle`: Validates cycle detection with shared visited set

**Running the tests:**

```bash
cd .kiro/hooks
python -m pytest test_reference_resolution.py -v
```

### test_log_entry_completeness.py

The test file `test_log_entry_completeness.py` validates **Property 4: Hook Log Entry Completeness** from the design document.

### Test Classes

1. **TestTimestampFormat**: Validates ISO 8601 timestamp format
2. **TestActiveSteeringFiles**: Validates Context field with active steering files
3. **TestTypeSpecificFields**: Validates required fields for each hook type
   - Data Decision logs
   - Financial Decision logs
   - AI Drift Detection logs
   - Hallucination Flag logs
   - Reasoning Review logs
   - Framework Compliance logs
4. **TestLogEntryStructure**: Validates overall markdown structure
5. **TestLogFileAppending**: Validates multiple entries append correctly
6. **TestRealWorldScenarios**: Integration tests with realistic data

### Property-Based Testing

The tests use Hypothesis to generate random test cases, ensuring the log entry format is correct across a wide range of inputs:

- **100+ iterations per test** (configurable)
- **Random field values** generated for each hook type
- **Random combinations** of steering files
- **Edge cases** automatically discovered

### Validated Requirements

- **8.3, 8.4**: Quality gate hook logging with timestamps and context
- **14.3, 14.4**: AI drift detection logging
- **15.4**: Hallucination detection logging
- **16.5**: Reasoning review logging
- **17.5**: Framework compliance logging

## Example Output

```
test_log_entry_completeness.py::TestTimestampFormat::test_timestamp_is_iso8601_format PASSED
test_log_entry_completeness.py::TestTimestampFormat::test_log_entry_contains_timestamp PASSED
test_log_entry_completeness.py::TestActiveSteeringFiles::test_log_entry_contains_context_field PASSED
test_log_entry_completeness.py::TestActiveSteeringFiles::test_context_field_lists_steering_files PASSED
test_log_entry_completeness.py::TestTypeSpecificFields::test_data_decision_required_fields PASSED
test_log_entry_completeness.py::TestTypeSpecificFields::test_financial_decision_required_fields PASSED
test_log_entry_completeness.py::TestTypeSpecificFields::test_drift_detection_required_fields PASSED
test_log_entry_completeness.py::TestTypeSpecificFields::test_hallucination_detection_required_fields PASSED
test_log_entry_completeness.py::TestTypeSpecificFields::test_reasoning_review_required_fields PASSED
test_log_entry_completeness.py::TestTypeSpecificFields::test_framework_compliance_required_fields PASSED
test_log_entry_completeness.py::TestLogEntryStructure::test_log_entry_has_markdown_header PASSED
test_log_entry_completeness.py::TestLogEntryStructure::test_log_entry_ends_with_blank_line PASSED
test_log_entry_completeness.py::TestLogEntryStructure::test_log_entry_fields_use_bold_markdown PASSED
test_log_entry_completeness.py::TestLogFileAppending::test_multiple_entries_appended_correctly PASSED
test_log_entry_completeness.py::TestRealWorldScenarios::test_data_decision_with_rejection PASSED
test_log_entry_completeness.py::TestRealWorldScenarios::test_reasoning_review_with_failures PASSED
```

## Troubleshooting

### Hypothesis not installed

If you see "Hypothesis not installed", run:

```bash
pip install hypothesis
```

### Import errors

Make sure you're running tests from the `.kiro/hooks` directory so Python can find the modules:

```bash
cd .kiro/hooks
python -m pytest test_log_entry_completeness.py
```

### Test failures

If tests fail, check:
1. The `log_utils.py` module is in the same directory
2. All required functions are implemented
3. The log entry format matches the expected structure

## Adding New Tests

To add tests for new hook types:

1. Create a new field strategy function (e.g., `new_hook_fields_strategy`)
2. Add the hook type to `log_type_strategy`
3. Update `log_entry_strategy` to handle the new type
4. Add a test method in `TestTypeSpecificFields` for the new hook type

Example:

```python
@composite
def new_hook_fields_strategy(draw):
    """Generate fields for new hook log entries."""
    return {
        "Field1": draw(st.text(min_size=10, max_size=100)),
        "Field2": draw(st.sampled_from(["Option1", "Option2"]))
    }

@settings(max_examples=100)
@given(new_hook_fields_strategy())
def test_new_hook_required_fields(self, fields):
    """Property: New Hook log entries must contain Field1 and Field2."""
    # Test implementation
```
