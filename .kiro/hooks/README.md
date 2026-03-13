# Reasoning Context Framework - Hooks Documentation

## Overview

This directory contains hook implementations for the Reasoning Context Framework. Hooks provide automated quality gates and verification for AI outputs, ensuring data integrity, financial safety, behavioral consistency, and reasoning quality.

Hooks execute at specific lifecycle points (before file operations, after output generation, etc.) and can log decisions, request user approval, or block execution based on validation results.

## Hook Categories

### Quality Gate Hooks

Quality gate hooks intercept operations before execution and require user approval for high-impact decisions.

- **data_decision_gate.py**: Reviews data operations affecting integrity, privacy, or persistence
- **financial_decision_gate.py**: Reviews financial decisions with monetary implications

### Verification Hooks

Verification hooks validate AI outputs against baseline patterns, framework references, and reasoning criteria.

- **drift_detection.py**: Detects deviations from baseline AI behavior patterns
- **hallucination_detection.py**: Validates factual claims against steering file content
- **reasoning_review.py**: Applies structured review criteria to validate outputs
- **framework_compliance.py**: Validates outputs follow documented reasoning frameworks

### Utility Modules

- **log_utils.py**: Shared utilities for log entry formatting and timestamp generation
- **reference_resolver.py**: Resolves steering file references and detects circular references
- **context_loader.py**: Loads task steering files and all referenced parents
- **orchestrator.py**: Coordinates hook execution order and context passing
- **register_hooks.py**: Registers hooks with Kiro's hook system

## Hook Configuration

Hooks are configured in `config.json` with the following structure:

```json
{
  "hooks": {
    "hook_name": {
      "enabled": true,
      "script": ".kiro/hooks/script_name.py",
      "trigger": "lifecycle_event",
      "conditions": ["condition1", "condition2"],
      "action": "action_type",
      "log_path": ".kiro/logs/log-file.md",
      "timeout_seconds": 30
    }
  }
}
```

### Configuration Fields

- **enabled**: Whether the hook is active (true/false)
- **script**: Path to the hook script
- **trigger**: Lifecycle event that triggers the hook
- **conditions**: List of conditions that must be met for hook to execute
- **action**: Hook behavior (require_user_approval, log_only, block_on_failure, etc.)
- **log_path**: Where to write log entries
- **timeout_seconds**: Maximum execution time before hook is bypassed

### Trigger Points

- **before_file_operation**: Before file create, modify, or delete operations
- **before_command_execution**: Before shell commands are executed
- **before_financial_operation**: Before operations with monetary impact
- **after_output_generation**: After AI generates output, before presenting to user
- **before_operation_execution**: Before executing any operation (final quality gate)

## Individual Hook Documentation

### Data Decision Quality Gate

**Purpose**: Protect data integrity and privacy by reviewing data operations before execution.

**Script**: `data_decision_gate.py`

**Trigger**: `before_file_operation`

**Conditions**:
- Operation type is delete or modify
- File contains sensitive data OR is bulk operation

**Behavior**:
1. Detects data operation type (deletion, modification, sensitive data, bulk)
2. Generates impact summary with affected files and warnings
3. Requests explicit user approval
4. Logs decision with timestamp and context
5. Blocks execution if user rejects

**Impact Classifications**:
- **Deletion**: Permanent data removal
- **Modification**: Changes to existing data
- **Sensitive Data**: Operations involving credentials, keys, passwords, PII
- **Bulk Operation**: Operations affecting multiple files

**Example Log Entry**:
```markdown
## 2026-02-25T14:30:00Z Data Decision

**Operation**: delete
**Impact**: Deletion, Sensitive Data
**Affected Files**: credentials/api_keys.json
**Impact Summary**: 
Operation Type: delete
Affected File: credentials/api_keys.json
Impact Classification: Deletion, Sensitive Data
⚠️  WARNING: This operation will permanently delete data
🔒 PRIVACY: This operation involves sensitive data
**User Decision**: Approved
**Active Steering Files**: .kiro/steering/tasks/cleanup-old-credentials/context.md
```

**Command-Line Testing**:
```bash
python .kiro/hooks/data_decision_gate.py delete credentials/api_keys.json --sensitive
```

**Error Handling**:
- Log write failure: Continues with user's approval decision, notifies user
- User approval timeout: Defaults to blocking after 5 minutes
- Missing impact summary: Presents generic warning, still requires approval

---

### Financial Decision Quality Gate

**Purpose**: Prevent unintended monetary impacts by reviewing financial decisions before execution.

**Script**: `financial_decision_gate.py`

**Trigger**: `before_financial_operation`

**Conditions**:
- Operation has monetary impact

**Behavior**:
1. Detects financial operation and calculates monetary impact
2. Compares against configured thresholds
3. Auto-approves if below threshold, requests approval if above
4. Generates impact summary with cost breakdown
5. Logs decision with timestamp and context
6. Blocks execution if user rejects

**Threshold Configuration** (in config.json):
```json
"thresholds": {
  "auto_approve_max": 50,
  "require_review_min": 50,
  "currency": "USD"
}
```

**Example Log Entry**:
```markdown
## 2026-02-25T14:35:00Z Financial Decision

**Operation**: purchase
**Monetary Impact**: $125.00 USD
**Threshold**: $50.00 (exceeded)
**Impact Summary**:
Operation Type: purchase
Item: Car battery (Group 51R, 500 CCA)
Cost: $125.00
Budget: $150.00 available
Remaining: $25.00 after purchase
**User Decision**: Approved
**Active Steering Files**: .kiro/steering/tasks/replace-car-battery/context.md, .kiro/steering/projects/car-maintenance/context.md
```

**Error Handling**:
- Missing threshold configuration: Defaults to requiring approval for all financial decisions
- User approval timeout: Defaults to blocking after 5 minutes
- Impact summary generation failure: Presents generic warning, still requires approval

---

### AI Drift Detection

**Purpose**: Detect and log deviations from baseline AI behavior patterns to maintain consistency.

**Script**: `drift_detection.py`

**Trigger**: `after_output_generation`

**Conditions**: None (runs on all outputs)

**Behavior**:
1. Loads baseline behavior patterns from framework steering files
2. Compares current output characteristics against baseline
3. Calculates deviation scores for multiple dimensions
4. Logs significant deviations (non-blocking)
5. Continues execution regardless of deviations

**Deviation Types**:
- **Response Length**: Word count outside expected range
- **Code Block Usage**: Missing code blocks in technical responses
- **Citation Frequency**: Insufficient citations for factual claims
- **Reasoning Pattern**: Missing expected reasoning structures
- **Output Format**: Incorrect file paths, command syntax, or formatting

**Baseline Patterns** (from `.kiro/steering/framework/ai-behavior-baseline/baseline.md`):
- Standard queries: 200-500 words
- Technical explanations: 300-800 words
- Code blocks: Present in 80% of technical responses
- Citations: At least 1 reference per factual claim

**Deviation Thresholds**:
- **Minor**: 30% deviation (logged but not flagged)
- **Significant**: 50% deviation (flagged for review)

**Example Log Entry**:
```markdown
## 2026-02-25T14:40:00Z AI Drift Detected

**Deviation Type**: Response Length
**Severity**: Significant
**Deviation Score**: 0.65
**Expected Pattern**: 200-500 words for standard queries
**Observed Pattern**: Response too short: 120 words (expected 200-500)
**Active Steering Files**: .kiro/steering/tasks/replace-car-battery/context.md
```

**Error Handling**:
- Baseline file missing: Uses default patterns, logs warning
- Baseline parsing failure: Uses default patterns, logs warning
- Timeout: Skips drift detection, logs timeout

---

### Hallucination Detection

**Purpose**: Validate factual claims against steering file content to prevent false information.

**Script**: `hallucination_detection.py`

**Trigger**: `after_output_generation`

**Conditions**:
- Output contains factual claims

**Behavior**:
1. Extracts factual claims from output
2. Validates claims against active steering files
3. Flags unsupported claims or claims missing citations
4. Requires user confirmation for flagged outputs
5. Logs potential hallucinations
6. Blocks execution if user rejects flagged output

**Claim Types**:
- **Factual**: Definitive statements (is, are, was, were)
- **Procedural**: Steps, instructions, requirements
- **Numerical**: Specific numbers, percentages, measurements
- **Reference**: Mentions of documents, sections, codes
- **Inference**: Explicitly marked assumptions (assume, likely, probably)

**Validation Status**:
- **Supported**: Claim backed by steering file content
- **Unsupported**: No supporting evidence found
- **Inference**: Explicitly marked as assumption (acceptable)
- **Citation Required**: Supported but lacks explicit citation in critical context

**Critical Contexts** (require citations):
- Data decisions
- Financial decisions

**Example Log Entry**:
```markdown
## 2026-02-25T14:45:00Z Hallucination Flag

**Claim**: The battery requires 500 CCA minimum for this vehicle
**Claim Type**: Numerical
**Validation Result**: Unsupported
**Confidence Score**: 0.25
**Supporting Evidence**: None found
**User Action**: Rejected
**Active Steering Files**: .kiro/steering/tasks/replace-car-battery/context.md
```

**Error Handling**:
- Steering content load failure: Skips validation for that file
- User confirmation timeout: Defaults to blocking
- Log write failure: Continues with user's decision, notifies user

---

### Reasoning Review

**Purpose**: Apply structured review criteria to validate AI outputs systematically.

**Script**: `reasoning_review.py`

**Trigger**: `before_operation_execution`

**Conditions**:
- Is critical decision (data or financial)

**Behavior**:
1. Loads review criteria from framework steering files
2. Applies base criteria: factual accuracy, logical consistency, completeness, context alignment
3. Applies domain-specific criteria based on active frameworks
4. Calculates scores for each criterion
5. Logs results with pass/fail status
6. Presents failure reasons if validation fails
7. Blocks execution on failure

**Base Criteria**:
- **Factual Accuracy**: Claims supported or marked as inference
- **Logical Consistency**: No contradictions in reasoning
- **Completeness**: All required information present
- **Context Alignment**: Respects steering file constraints

**Domain-Specific Criteria**:
- **Automotive**: Error code lookup, safety procedures, torque specs
- **Financial**: Cost breakdown, budget alignment, approval authority
- **Legal/Compliance**: Citations, compliance check, authority verification

**Scoring**:
- **Pass**: Criterion fully satisfied
- **Partial**: 80-99% satisfied (warning but may proceed)
- **Fail**: <80% satisfied (blocks execution)

**Example Log Entry**:
```markdown
## 2026-02-25T14:50:00Z Reasoning Review

**Review Type**: Domain-Specific
**Criteria Applied**: Factual Accuracy, Logical Consistency, Completeness, Context Alignment, Automotive Error Code Lookup
**Results**:
- Factual Accuracy: Pass - All 12 claims supported or marked as inference
- Logical Consistency: Pass - No logical contradictions detected
- Completeness: Pass - All key elements present: explanation, steps, considerations
- Context Alignment: Pass - Output aligns with steering file context (8 constraint references)
- Automotive Error Code Lookup: Pass - Error code reference present
**Overall Status**: Pass
**Action**: Proceed
**Active Steering Files**: .kiro/steering/tasks/replace-car-battery/context.md, .kiro/steering/framework/automotive/battery-replacement-procedure.md
```

**Error Handling**:
- Criteria file missing: Prompts user, uses defaults if approved
- Validation timeout: Defaults to fail-open (proceed with warning)
- Log write failure: Continues with validation result, notifies user

---

### Framework Compliance

**Purpose**: Ensure AI analysis follows documented reasoning framework methodologies.

**Script**: `framework_compliance.py`

**Trigger**: `after_output_generation`

**Conditions**:
- Active reasoning framework exists (referenced in task/project steering)

**Behavior**:
1. Identifies active reasoning frameworks from steering file references
2. Loads framework structure from framework steering files
3. Validates output follows framework steps and structure
4. Logs compliance status
5. Flags non-compliance to user

**Compliance Status**:
- **Compliant**: 90%+ framework steps present
- **Partial Compliance**: 60-89% framework steps present
- **Non-Compliant**: <60% framework steps present
- **No Framework**: No framework active (skips validation)

**Framework Examples**:
- Root cause analysis (5 Whys, Fishbone)
- Decision trees
- Risk assessment matrices
- Troubleshooting procedures
- Financial planning methodologies

**Example Log Entry**:
```markdown
## 2026-02-25T14:55:00Z Framework Compliance Check

**Framework**: Automotive Diagnostic Procedure
**Framework File**: .kiro/steering/framework/reasoning-patterns/automotive-diagnostics.md
**Compliance Status**: Compliant
**Compliance Rate**: 100%
**Steps Found**: 3/3
**Missing Steps**: None
**Evidence**:
  Step 1:
    - Step 1: Verify Error Code First, I'll connect the OBD-II scanner...
  Step 2:
    - Step 2: Check Oxygen Sensor Readings Next, I'll examine the upstream...
  Step 3:
    - Step 3: Inspect Catalytic Converter Finally, I'll perform a visual...
**Active Steering Files**: .kiro/steering/tasks/diagnose-check-engine-light/context.md
```

**Error Handling**:
- Framework file missing: Prompts user, skips validation if approved
- Framework parsing failure: Prompts user, skips validation if approved
- Timeout: Skips compliance check, logs timeout

---

## Utility Modules

### log_utils.py

Shared utilities for log entry formatting and timestamp generation.

**Functions**:
- `format_timestamp()`: Generate ISO 8601 timestamp
- `get_active_steering_files(workspace_root)`: List all active steering files
- `format_log_entry(title, fields, workspace_root)`: Format log entry with timestamp and context
- `append_log_entry(log_path, title, fields, workspace_root)`: Append formatted entry to log file

**Usage Example**:
```python
from log_utils import append_log_entry

fields = {
    "Operation": "delete",
    "Impact": "Deletion",
    "User Decision": "Approved"
}

append_log_entry(
    Path(".kiro/logs/data-decisions.md"),
    "Data Decision",
    fields,
    Path.cwd()
)
```

---

### reference_resolver.py

Resolves steering file references and detects circular references.

**Functions**:
- `parse_references(file_path)`: Extract reference paths from steering file
- `resolve_reference(reference, source_file)`: Resolve relative reference path
- `detect_circular_references(file_path, workspace_root)`: Check for circular reference chains
- `load_referenced_files(file_path, workspace_root)`: Load file and all referenced parents

**Usage Example**:
```python
from reference_resolver import detect_circular_references

try:
    detect_circular_references(
        Path(".kiro/steering/tasks/my-task/context.md"),
        Path.cwd()
    )
    print("✓ No circular references")
except ValueError as e:
    print(f"✗ Circular reference detected: {e}")
```

---

### context_loader.py

Loads task steering files and all referenced parents to build complete context.

**Functions**:
- `load_task_context(task_file, workspace_root)`: Load task and all referenced files
- `get_context_chain(task_file, workspace_root)`: Get ordered list of context files

**Usage Example**:
```python
from context_loader import load_task_context

context = load_task_context(
    Path(".kiro/steering/tasks/replace-car-battery/context.md"),
    Path.cwd()
)

print(f"Loaded {len(context)} context files:")
for file_path, content in context.items():
    print(f"  - {file_path}")
```

---

### orchestrator.py

Coordinates hook execution order and context passing.

**Functions**:
- `execute_quality_gates(operation, workspace_root)`: Run quality gate hooks
- `execute_verification_hooks(output, workspace_root)`: Run verification hooks
- `execute_hook_chain(hooks, context, workspace_root)`: Execute hooks in sequence

**Execution Order**:
1. Quality gate hooks (before operation)
2. Verification hooks (after output generation)
3. Final review (before execution)

**Usage Example**:
```python
from orchestrator import execute_quality_gates

operation = {
    'operation_type': 'delete',
    'file_path': 'data/important.json'
}

approved = execute_quality_gates(operation, Path.cwd())
if approved:
    # Proceed with operation
    pass
else:
    # Operation blocked
    pass
```

---

### register_hooks.py

Registers hooks with Kiro's hook system based on config.json.

**Functions**:
- `load_hook_config(config_path)`: Load hook configuration
- `register_hook(hook_name, hook_config)`: Register individual hook
- `register_all_hooks(workspace_root)`: Register all enabled hooks

**Usage Example**:
```bash
# Register all hooks
python .kiro/hooks/register_hooks.py

# Register specific hook
python .kiro/hooks/register_hooks.py --hook data_decision_gate
```

---

## Testing Hooks

### Command-Line Testing

Most hooks include command-line interfaces for testing:

```bash
# Test data decision gate
python .kiro/hooks/data_decision_gate.py delete credentials/api_keys.json --sensitive

# Test drift detection
python .kiro/hooks/drift_detection.py

# Test hallucination detection
python .kiro/hooks/hallucination_detection.py

# Test reasoning review
python .kiro/hooks/reasoning_review.py

# Test framework compliance
python .kiro/hooks/framework_compliance.py
```

### Test Utility

Use `test_hooks.py` for interactive testing:

```bash
# Test all hooks
python .kiro/hooks/test_hooks.py --all

# Test specific hook
python .kiro/hooks/test_hooks.py --hook data_decision_gate

# Test with custom operation
python .kiro/hooks/test_hooks.py --hook data_decision_gate --operation delete --file test.json
```

### Property-Based Tests

Run property-based tests to validate universal correctness properties:

```bash
# Run all property tests
pytest .kiro/hooks/test_*.py

# Run specific property test
pytest .kiro/hooks/test_reference_resolution.py
pytest .kiro/hooks/test_log_entry_completeness.py
pytest .kiro/hooks/test_hallucination_detection.py
```

---

## Log Files

All hooks write to log files in `.kiro/logs/`:

- **data-decisions.md**: Data operation proposals and approvals
- **financial-decisions.md**: Financial decision proposals and approvals
- **ai-drift.md**: Detected deviations from baseline behavior
- **hallucination-flags.md**: Unsupported factual claims
- **reasoning-reviews.md**: Structured review results
- **framework-compliance.md**: Reasoning framework adherence tracking

### Log Entry Format

All log entries follow a consistent structure:

```markdown
## [ISO 8601 Timestamp] [Log Type]

**Field Name**: Field value
**Another Field**: Another value
**Active Steering Files**: List of active context files at time of log
```

### Log Maintenance

- **Review Frequency**: Review logs weekly for patterns and issues
- **Retention**: Keep logs for at least 90 days
- **Archival**: Archive old logs to `.kiro/logs/archive/` after 90 days
- **Analysis**: Use log data to refine baselines, criteria, and thresholds

---

## Troubleshooting

### Hook Not Executing

**Symptoms**: Hook doesn't run when expected

**Possible Causes**:
- Hook disabled in config.json
- Trigger conditions not met
- Hook script has syntax errors

**Solutions**:
1. Check `config.json` - ensure `"enabled": true`
2. Verify trigger conditions match your operation
3. Run hook script directly to check for errors:
   ```bash
   python .kiro/hooks/hook_name.py
   ```

### Hook Timeout

**Symptoms**: Warning that hook execution timed out

**Possible Causes**:
- Hook logic too complex
- Timeout value too low
- Steering files too large

**Solutions**:
1. Increase timeout in config.json:
   ```json
   "timeout_seconds": 60
   ```
2. Simplify hook logic if possible
3. Optimize steering file loading

### Log Write Failure

**Symptoms**: Error message about log file write failure

**Possible Causes**:
- Log directory doesn't exist
- Permission denied
- Disk full

**Solutions**:
1. Create log directory:
   ```bash
   mkdir -p .kiro/logs
   ```
2. Check file permissions:
   ```bash
   chmod 755 .kiro/logs
   ```
3. Check disk space:
   ```bash
   df -h
   ```

### Baseline File Missing

**Symptoms**: Warning that baseline file not found

**Possible Causes**:
- Baseline file not created yet
- Incorrect file path

**Solutions**:
1. Create baseline file at `.kiro/steering/framework/ai-behavior-baseline/baseline.md`
2. Use template from `.kiro/steering/framework/ai-behavior-baseline/.template/`
3. Verify path in config.json matches actual file location

### Framework File Missing

**Symptoms**: Warning that framework file not found

**Possible Causes**:
- Framework file not created yet
- Incorrect reference path in steering file

**Solutions**:
1. Create framework file at referenced path
2. Use template from `.kiro/steering/framework/reasoning-patterns/.template/`
3. Verify reference path in task/project steering file is correct

### Circular Reference Detected

**Symptoms**: Error message showing circular reference chain

**Possible Causes**:
- Steering files reference each other in a cycle

**Solutions**:
1. Review the reference chain shown in error message
2. Identify which reference creates the cycle
3. Refactor steering files to break the cycle
4. Remember: references should only flow down the hierarchy

---

## Best Practices

### Hook Configuration

- **Enable Selectively**: Only enable hooks you need
- **Set Appropriate Timeouts**: Balance thoroughness with responsiveness
- **Review Logs Regularly**: Use log data to refine hook behavior
- **Test Before Deploying**: Test hooks with sample operations before enabling

### Quality Gates

- **Set Reasonable Thresholds**: Balance safety with usability
- **Provide Clear Summaries**: Help users make informed decisions
- **Log All Decisions**: Track approvals and rejections for audit trail
- **Handle Timeouts Gracefully**: Default to safe behavior (blocking)

### Verification Hooks

- **Keep Baselines Updated**: Review and update baselines quarterly
- **Refine Criteria**: Use log data to identify areas for improvement
- **Balance Strictness**: Avoid false positives that frustrate users
- **Provide Actionable Feedback**: Help users understand and fix issues

### Error Handling

- **Fail Gracefully**: Don't crash on errors, provide clear messages
- **Default to Safe**: When in doubt, block rather than proceed
- **Log Errors**: Track errors for debugging and improvement
- **Notify Users**: Keep users informed of issues and workarounds

---

## Integration with Kiro

Hooks integrate with Kiro at specific lifecycle points. The exact integration mechanism depends on Kiro's hook system implementation.

### Expected Integration Points

1. **Before File Operations**: Kiro calls quality gate hooks before file create/modify/delete
2. **After Output Generation**: Kiro calls verification hooks after generating output
3. **Before Execution**: Kiro calls final review hooks before executing operations

### Hook Return Values

Hooks return boolean values indicating whether to proceed:
- `True`: Proceed with operation
- `False`: Block operation

Hooks may also return additional data (messages, failure reasons) for user presentation.

### Context Passing

Kiro passes context to hooks including:
- Active steering files
- Current operation details
- User preferences
- Workspace root path

---

## Future Enhancements

Potential improvements for future versions:

- **Machine Learning**: Use ML to improve drift detection and hallucination detection
- **Custom Criteria**: Allow users to define custom review criteria per project
- **Hook Chaining**: Support complex hook dependencies and conditional execution
- **Performance Optimization**: Cache steering file content, optimize validation algorithms
- **User Preferences**: Allow users to customize thresholds and behavior per hook
- **Analytics Dashboard**: Visualize log data to identify trends and patterns

---

## Support and Feedback

For issues, questions, or suggestions:

1. Review this documentation and troubleshooting section
2. Check log files for error details
3. Test hooks individually using command-line interfaces
4. Review property-based test results for validation issues

---

## Version History

- **v1.0.0** (2026-02-25): Initial implementation
  - Data decision quality gate
  - Financial decision quality gate
  - AI drift detection
  - Hallucination detection
  - Reasoning review
  - Framework compliance
  - Utility modules and orchestration
