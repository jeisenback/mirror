# Error Handling Implementation

This document describes the comprehensive error handling implemented for the Reasoning Context Framework hooks.

## Overview

Error handling has been implemented across four main categories:
1. Steering file reference errors
2. Hook execution errors
3. Verification hook errors
4. Quality gate errors

## 1. Steering File Reference Errors

**Module**: `reference_resolver.py`

### Custom Exceptions

- **`CircularReferenceError`**: Raised when circular reference chains are detected
  - Displays complete reference chain (A → B → C → A)
  - Helps user identify which reference creates the cycle

- **`MissingReferenceError`**: Raised when referenced file doesn't exist
  - Provides clear error message with source and target files
  - Suggests corrected paths when possible (case-insensitive matches, similar names)

- **`InvalidReferenceError`**: Raised when reference path is malformed
  - Detects absolute paths and suggests relative path format
  - Provides specific reason for invalidity

### Path Suggestion Algorithm

The `_suggest_corrected_path()` function:
- Checks for case-insensitive filename matches
- Looks for similar filenames in the same directory
- Suggests directory corrections if parent directory exists
- Returns `None` if no reasonable suggestion available

### Example Error Messages

```
Missing reference target: '../../household/context.md' referenced in '.kiro/steering/tasks/my-task/context.md'
Did you mean: '../../household/Context.md'?
```

```
Circular reference detected: /path/to/a.md → /path/to/b.md → /path/to/c.md → /path/to/a.md
```

```
Invalid reference in '.kiro/steering/tasks/my-task/context.md': '/absolute/path/to/file.md'
Reason: Reference paths must be relative, not absolute. Use relative paths like '../../household/context.md'
```

## 2. Hook Execution Errors

**Module**: `hook_executor.py`

### Custom Exceptions

- **`HookTimeoutError`**: Raised when hook execution exceeds timeout
  - Logs timeout event
  - Bypasses hook to prevent blocking user
  - Notifies user that validation was skipped

- **`HookConfigurationError`**: Raised when hook configuration is invalid
  - Validates required fields (log_path, timeout_seconds)
  - Checks value types and ranges
  - Provides specific reason for configuration error

- **`LogWriteError`**: Raised when log file write fails
  - Detects permission errors
  - Detects disk space issues
  - Suggests corrective actions

### Timeout Handling

The `hook_timeout()` context manager:
- Uses SIGALRM for timeout enforcement
- Automatically cancels alarm on completion
- Restores previous signal handler

### Safe Log Writing

The `safe_write_log()` function:
- Creates parent directories if needed
- Handles permission errors gracefully
- Detects disk space issues
- Provides actionable error messages

### Configuration Validation

The `validate_hook_config()` function:
- Checks for required fields
- Validates timeout is positive number
- Validates log_path is string
- Raises `HookConfigurationError` with specific reason

### Default Behavior

When configuration is missing or invalid:
- Loads conservative defaults
- Logs warning to user
- Continues execution with safe defaults

## 3. Verification Hook Errors

**Modules**: `drift_detection.py`, `reasoning_review.py`, `framework_compliance.py`

### Missing Baseline Files (Drift Detection)

When `baseline.md` is missing:
- Logs warning message
- Uses default baseline patterns
- Continues drift detection with reasonable defaults
- Suggests creating baseline.md for customization

**Default Patterns**:
- Response length: 200-500 words (standard), 300-800 words (technical)
- Code block frequency: 80% of technical responses
- Citation frequency: 1 reference per factual claim

### Missing Criteria Files (Reasoning Review)

When `criteria.md` is missing:
- Logs warning message
- Prompts user to proceed with defaults or halt
- Uses base criteria: factual accuracy, logical consistency, completeness, context alignment
- Suggests creating criteria.md for customization

**User Prompt**:
```
WARNING: Review criteria file not found at .kiro/steering/framework/reasoning-review-process/criteria.md
Using default review criteria (factual accuracy, logical consistency, completeness, context alignment).
Create criteria.md to customize reasoning review validation.
Proceed with default criteria? (yes/no):
```

### Missing Framework References (Framework Compliance)

When framework file is missing:
- Logs warning message
- Prompts user to proceed without validation or halt
- Returns `None` to indicate framework unavailable
- Allows caller to decide whether to continue

**User Prompt**:
```
WARNING: Framework file not found at .kiro/steering/framework/reasoning-patterns/my-pattern.md
Framework compliance validation cannot be performed.
Proceed without framework validation? (yes/no):
```

### Error Recovery Strategy

All verification hooks follow the same pattern:
1. Detect missing file
2. Log clear warning message
3. Prompt user for decision (when appropriate)
4. Use safe defaults or skip validation
5. Continue execution without blocking

## 4. Quality Gate Errors

**Module**: `quality_gate_errors.py`

### Custom Exceptions

- **`ApprovalTimeoutError`**: Raised when user approval times out
  - Defaults to blocking operation for safety
  - Logs timeout event
  - Notifies user of default blocking behavior

- **`MissingThresholdConfigError`**: Raised when threshold config missing
  - Uses conservative defaults (require approval for all operations)
  - Logs warning message
  - Continues with safe defaults

- **`ImpactSummaryError`**: Raised when impact summary generation fails
  - Falls back to generic warning
  - Includes available operation details
  - Still requires user approval

### Threshold Configuration

The `load_threshold_config()` function:
- Loads thresholds from config.json
- Handles missing file gracefully
- Handles invalid JSON gracefully
- Returns conservative defaults on error

**Default Thresholds**:
```json
{
  "financial_thresholds": {
    "auto_approve_max": 0,
    "require_review_min": 0,
    "currency": "USD"
  },
  "data_thresholds": {
    "require_approval_for_deletion": true,
    "require_approval_for_modification": true,
    "require_approval_for_sensitive": true
  },
  "approval_timeout_seconds": 300
}
```

### Impact Summary Generation

**Data Operations** (`generate_data_impact_summary()`):
- Formats operation details
- Flags sensitive data with privacy warning
- Provides impact assessment
- Falls back to generic summary on error

**Financial Operations** (`generate_financial_impact_summary()`):
- Formats monetary amount with proper formatting
- Flags high-value transactions (≥ $1000)
- Provides impact assessment
- Falls back to generic summary on error

**Generic Fallback** (`generate_generic_impact_summary()`):
- Used when detailed summary generation fails
- Includes warning about failed analysis
- Lists available operation details
- Recommends manual verification

### User Approval with Timeout

The `request_user_approval_with_timeout()` function:
- Presents formatted impact summary
- Shows timeout countdown
- Handles keyboard interrupt (Ctrl+C)
- Defaults to blocking on timeout or error
- Returns boolean approval decision

### Logging

The `log_approval_decision()` function:
- Logs all approval decisions
- Includes impact summary
- Records approval/rejection
- Includes rejection reason if provided
- Handles log write failures gracefully

## Error Handling Principles

All error handling follows these principles:

1. **Fail Safe**: Default to conservative behavior (block operations, require approval)
2. **Clear Messages**: Provide actionable error messages with context
3. **Graceful Degradation**: Continue with safe defaults when possible
4. **User Control**: Prompt user for decisions when appropriate
5. **Comprehensive Logging**: Log all errors and decisions for audit trail
6. **No Silent Failures**: Always notify user of errors or degraded functionality

## Testing

All error handling is tested in `test_error_handling.py`:
- Reference resolver errors
- Hook executor errors
- Quality gate errors
- Verification hook errors

Run tests with:
```bash
python .kiro/hooks/test_error_handling.py
```

## Requirements Coverage

This implementation satisfies the following requirements:

- **7.4, 7.5**: Steering file reference error handling
- **18.5**: Hook execution error handling (timeouts, configuration, log writes)
- **14.1, 16.1, 17.1**: Verification hook error handling (missing baselines, criteria, frameworks)
- **10.2**: Quality gate error handling (approval timeouts, missing thresholds, impact summary failures)

## Future Enhancements

Potential improvements:
1. Async timeout handling for better cross-platform support
2. More sophisticated path suggestion algorithm (fuzzy matching)
3. Configurable error recovery strategies
4. Error metrics and monitoring
5. Automated error recovery for common issues
