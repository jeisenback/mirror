# Reasoning Review Process

## Overview

This framework steering file defines the criteria and procedures for validating AI outputs systematically before execution. The reasoning review process ensures outputs meet quality standards for factual accuracy, logical consistency, completeness, and context alignment.

## Review Criteria

### 1. Factual Accuracy

**Definition**: All factual claims must be supported by steering file content or explicitly marked as inference/assumption.

**Validation Steps**:
- Identify all factual claims in the output
- Verify each claim against active steering files and framework references
- Check that unsupported claims are marked as inference or assumption
- Validate that citations reference correct sections of steering files

**Scoring**:
- **Pass**: All claims supported or properly marked
- **Partial**: 80-99% of claims supported or properly marked
- **Fail**: <80% of claims supported or properly marked

**Failure Actions**:
- List unsupported claims
- Request citations or mark as inference
- Block execution until corrected

### 2. Logical Consistency

**Definition**: The reasoning chain must be free of contradictions and follow valid logical structure.

**Validation Steps**:
- Check for internal contradictions in the output
- Verify that conclusions follow from premises
- Validate that recommendations align with stated constraints
- Check for consistency with active steering file constraints

**Scoring**:
- **Pass**: No logical contradictions detected
- **Partial**: Minor inconsistencies that don't affect core conclusions
- **Fail**: Significant contradictions or invalid reasoning

**Failure Actions**:
- Identify specific contradictions
- Request clarification or correction
- Block execution until resolved

### 3. Completeness

**Definition**: The output must address all required information and considerations for the task.

**Validation Steps**:
- Verify all task objectives are addressed
- Check that all constraints from steering files are considered
- Validate that required sections or components are present
- Ensure success criteria are measurable and clear

**Scoring**:
- **Pass**: All required information present
- **Partial**: 80-99% of required information present
- **Fail**: <80% of required information present

**Failure Actions**:
- List missing information or considerations
- Request completion of missing elements
- Block execution until complete

### 4. Context Alignment

**Definition**: The output must align with constraints, preferences, and requirements from active steering files.

**Validation Steps**:
- Verify output respects all constraints from active steering files
- Check that recommendations align with stated preferences
- Validate that approach follows referenced framework methodologies
- Ensure output is appropriate for the context layer (household/role/project/task)

**Scoring**:
- **Pass**: Full alignment with steering file context
- **Partial**: Minor deviations that don't violate hard constraints
- **Fail**: Significant misalignment or constraint violations

**Failure Actions**:
- Identify specific misalignments
- Reference violated constraints from steering files
- Request revision to align with context
- Block execution until aligned

## Domain-Specific Criteria

### Automotive Repair Context

When framework steering files reference automotive repair procedures:
- **Error Code Lookup**: Must include error code lookup in diagnostic procedures
- **Safety Procedures**: Must reference safety procedures from service bulletins
- **Torque Specifications**: Must include torque specifications from repair manuals
- **Part Numbers**: Must verify part numbers against service documentation

### Financial Decision Context

When task involves financial decisions:
- **Cost Breakdown**: Must provide itemized cost breakdown
- **Budget Alignment**: Must verify alignment with budget constraints from steering files
- **Approval Authority**: Must respect decision authority limits from role steering
- **Impact Analysis**: Must include financial impact summary

### Legal/Compliance Context

When organizational bylaws or regulations are referenced:
- **Citation Required**: Must cite specific bylaw or regulation sections
- **Compliance Check**: Must verify compliance with all applicable rules
- **Authority Verification**: Must confirm decision authority per bylaws
- **Documentation**: Must document compliance rationale

## Review Process

### Execution Flow

1. **Trigger**: Review executes before operations, especially for data and financial decisions
2. **Load Criteria**: Load base criteria and domain-specific criteria from framework references
3. **Apply Criteria**: Evaluate output against all applicable criteria
4. **Calculate Scores**: Determine pass/partial/fail for each criterion
5. **Determine Overall Status**: Overall pass requires all criteria to pass
6. **Log Results**: Write review results to `.kiro/logs/reasoning-reviews.md`
7. **Present Failures**: If any criterion fails, present failure reasons to user
8. **Block or Proceed**: Block execution on failure, proceed on pass

### Log Entry Format

```markdown
## [Timestamp] Reasoning Review

**Context**: [Active steering files]
**Review Type**: [Standard/Domain-Specific]
**Criteria Applied**: [List of criteria]

**Results**:
- Factual Accuracy: [Pass/Partial/Fail] - [Score/Notes]
- Logical Consistency: [Pass/Partial/Fail] - [Score/Notes]
- Completeness: [Pass/Partial/Fail] - [Score/Notes]
- Context Alignment: [Pass/Partial/Fail] - [Score/Notes]
- [Domain-Specific Criteria]: [Pass/Partial/Fail] - [Score/Notes]

**Overall Status**: [Pass/Fail]
**Action**: [Proceed/Block]
**Failure Reasons**: [If failed, list specific issues]
```

## Configuration

### Threshold Settings

- **Pass Threshold**: All criteria must pass for overall pass
- **Partial Handling**: Partial scores trigger warning but may proceed based on context
- **Fail Handling**: Any fail score blocks execution

### Timeout Settings

- **Review Timeout**: 30 seconds maximum for review execution
- **Timeout Action**: On timeout, log warning and proceed (fail-open for availability)

## Notes

Review criteria should be updated as new patterns emerge or domain-specific needs are identified. Monthly review of logged failures helps identify areas for criteria refinement.

