# Reasoning Context Framework - User Guide

## Introduction

The Reasoning Context Framework is a configuration pattern that uses Kiro's existing features (steering files, hooks, and chat history) to create a hierarchical context management system for life activities. This guide walks you through setting up and using the framework to manage household tasks, organizational roles, projects, and critical decisions.

### What This Framework Provides

- **Hierarchical Context Management**: Organize information across household, role, project, and task layers
- **Quality Gates**: Automated review of data and financial decisions before execution
- **AI Risk Mitigation**: Protection against AI drift, hallucination, and reasoning errors
- **Audit Trail**: Complete logging of decisions and AI behavior for review

### What You'll Need

- Kiro IDE installed and configured
- Basic familiarity with markdown files
- Python 3.8+ (for hooks)
- 30-60 minutes for initial setup

## Quick Start

### Step 1: Initialize Directory Structure

Create the base directory structure for steering files and logs:

```bash
# Create steering directories
mkdir -p .kiro/steering/framework
mkdir -p .kiro/steering/household
mkdir -p .kiro/steering/roles
mkdir -p .kiro/steering/projects
mkdir -p .kiro/steering/tasks

# Create logs directory
mkdir -p .kiro/logs

# Create hooks directory
mkdir -p .kiro/hooks

# Create docs directory
mkdir -p .kiro/docs
```

### Step 2: Copy Template Files

Copy the template steering files to get started quickly:

```bash
# Copy household template
cp .kiro/steering/household/context.md.template .kiro/steering/household/context.md

# Copy role template
mkdir -p .kiro/steering/roles/my-role
cp .kiro/steering/roles/.template/context.md .kiro/steering/roles/my-role/context.md
```

### Step 3: Configure Hooks

Copy the hook configuration file:

```bash
cp .kiro/hooks/config.json.template .kiro/hooks/config.json
```

Edit `config.json` to enable the hooks you want to use.

### Step 4: Create Your First Task

Create a task steering file:

```bash
mkdir -p .kiro/steering/tasks/my-first-task
cp .kiro/steering/tasks/.template/context.md .kiro/steering/tasks/my-first-task/context.md
```

Edit the task file to add your task details and references.

### Step 5: Activate Context in Kiro

In Kiro, reference your task steering file using the `#` context key:

```
#.kiro/steering/tasks/my-first-task/context.md
```

Kiro will load the task context and all referenced parent files.


## Detailed Setup Guide

### Setting Up Household Context

The household steering file contains information about household members, schedules, preferences, and constraints.

**File Location**: `.kiro/steering/household/context.md`

**What to Include**:
1. Household member information (names, ages, roles)
2. Weekly schedules and availability patterns
3. Preferences (activities, communication, etc.)
4. Constraints (time, resources, physical limitations)

**Example**:
```markdown
# Household Context

## Household Members

| Name | Age | Role | Notes |
|------|-----|------|-------|
| Alex | 42 | Parent | Works Mon-Fri 9-5 |
| Jordan | 40 | Parent | Works from home |
| Sam | 12 | Child | School Mon-Fri 8-3 |

## Weekly Schedule

- **Monday-Friday**: Work/school days, limited availability
- **Saturday**: Errands and household tasks (morning)
- **Sunday**: Family time, minimal commitments

## Preferences

### Activity Preferences
- Outdoor activities: Hiking, biking on weekends
- Indoor activities: Board games, cooking together

## Constraints

### Time Constraints
- Weekday evenings: 2-3 hours available after dinner
- Weekend mornings: 3-4 hours available for tasks

### Resource Constraints
- Monthly household budget: $500 for maintenance and repairs
- Tools: Basic tool set, no specialized equipment
```

**When to Update**:
- Household composition changes
- Schedules shift
- New constraints emerge
- Quarterly review


### Setting Up Role Context

Role steering files define responsibilities, relationships, decision authority, and constraints for specific roles you hold.

**File Location**: `.kiro/steering/roles/{role-name}/context.md`

**What to Include**:
1. Role responsibilities and duties
2. Key relationships and stakeholders
3. Decision-making authority and limits
4. Role-specific constraints
5. Reference to household context (if relevant)

**Example** (Non-Profit President):
```markdown
# Role: Non-Profit President

## Context References

- Household: [[../../household/context.md]]

## Role Responsibilities

### Strategic Leadership
- Set organizational vision and strategic direction
- Lead board meetings and strategic planning sessions

### Board Relations
- Maintain communication with 9 board members
- Prepare board meeting materials and agendas

### Financial Oversight
- Review monthly financial reports
- Approve expenditures over $5,000 (board approval required for >$25,000)

## Key Relationships

### Board Members
- Board Chair: Monthly 1-on-1 meetings
- Treasurer: Weekly financial check-ins
- Committee Chairs: As needed for committee work

## Decision-Making Authority

### Independent Decision Authority
- Operational decisions: Up to $5,000
- Staff management: Hiring/firing with board notification
- Program adjustments: Within approved budget

### Board Approval Required
- Expenditures over $25,000
- Strategic plan changes
- Bylaw amendments

## Constraints

### Time Constraints
- Board meetings: 2nd Tuesday each month, 6-8 PM
- Committee meetings: Various, typically 1-2 per month
- Available time: 10-15 hours per week (volunteer role)
```

**When to Update**:
- Role responsibilities change
- New stakeholders or relationships
- Decision authority changes
- Annual review


### Setting Up Project Context

Project steering files track project-specific goals, stakeholders, timelines, and constraints.

**File Location**: `.kiro/steering/projects/{project-name}/context.md`

**What to Include**:
1. Project goals and success criteria
2. Stakeholders and their interests
3. Timeline and milestones
4. Project constraints
5. References to parent role or household context
6. References to relevant framework files

**Example** (Car Maintenance):
```markdown
# Project: Car Maintenance

## Context References

- Household: [[../../household/context.md]]
- Framework: [[../../framework/automotive/battery-replacement-procedure.md]]

## Project Goals

### Primary Objectives

- **Maintain Vehicle Reliability**: Keep vehicle in good working condition
  - Success Criteria: No unexpected breakdowns
  - Success Criteria: All scheduled maintenance completed on time

- **Extend Vehicle Lifespan**: Perform preventive maintenance
  - Success Criteria: Vehicle operates reliably for 200,000+ miles

## Vehicle Information

- **Make/Model/Year**: Honda Civic 2015
- **Mileage**: 85,000 miles
- **Known Issues**: Battery showing signs of age

## Timeline

### Key Milestones
- **Battery Replacement**: Target within 2 weeks
- **Next Oil Change**: Due in 3 months
- **Annual Inspection**: Due in 6 months

## Constraints

### Budget Constraints
- Monthly Budget: $100-150 for routine maintenance
- Annual Budget: $1,500-2,000 for all maintenance
- Cost Approval: Expenses over $200 require household budget review

### Time Constraints
- Weekend Work: Most maintenance on weekends
- Weather Dependent: Outdoor work limited by conditions
```

**When to Update**:
- Project goals or scope change
- Timelines shift
- New stakeholders or constraints
- At project milestones


### Setting Up Task Context

Task steering files define specific task objectives, success criteria, and constraints with complete context composition.

**File Location**: `.kiro/steering/tasks/{task-name}/context.md`

**What to Include**:
1. Task objectives (primary and secondary)
2. Success criteria (measurable)
3. Prerequisites and dependencies
4. Task-specific constraints
5. References to parent project/role/household
6. References to relevant framework files
7. References to reasoning frameworks (if applicable)

**Example** (Replace Car Battery):
```markdown
# Task: Replace Car Battery

## Context References

- Project: [[../../projects/car-maintenance/context.md]]
- Household: [[../../household/context.md]]
- Framework: [[../../framework/automotive/battery-replacement-procedure.md]]

## Task Objectives

### Primary Objective

Replace the aging car battery before winter weather arrives to ensure reliable vehicle starting.

### Secondary Objectives

- Learn DIY battery replacement for future tasks
- Save $50-100 by performing replacement myself
- Ensure old battery is recycled properly

## Success Criteria

- **Battery Installed Correctly**: Proper polarity, tight connections, secure hold-down
  - Measurable: Vehicle starts normally, no warning lights

- **Cost Within Budget**: Total cost ≤ $150
  - Measurable: Receipt total ≤ $150

## Vehicle-Specific Details

### Battery Specifications
- **Group Size**: 51R (Honda/Acura standard)
- **CCA Required**: 410 CCA minimum
- **CCA Target**: 500+ CCA (for cold weather reliability)

## Prerequisites

- Battery purchased with correct specifications
- Tools gathered (10mm and 13mm wrenches, wire brush, safety gear)
- Weather suitable (dry, above 40°F)
- Time available (1-2 hours without interruption)

## Constraints

### Time Constraints
- Completion Deadline: Within 2 weeks
- Work Window: Weekend morning (Saturday or Sunday, 9 AM - 12 PM)

### Budget Constraints
- Total Budget: $120-150 (battery + supplies)

### Resource Constraints
- Workspace: Driveway only (no garage)
- Assistance: Solo work (no helper available)
```

**When to Update**:
- Task objectives change
- New constraints emerge
- Task is complete (mark as archived)


### Setting Up Framework Steering Files

Framework steering files contain stable, reusable reference knowledge that applies across multiple tasks.

**File Location**: `.kiro/steering/framework/{domain-name}/{file-name}.md`

**What to Include**:
1. Stable reference knowledge (procedures, standards, specifications)
2. Domain-specific information (repair manuals, bylaws, regulations)
3. AI behavior baselines (expected patterns)
4. Reasoning review criteria
5. Reasoning framework methodologies

**Example Domains**:
- **automotive**: Car repair procedures, diagnostic guides, service bulletins
- **organizational**: Non-profit bylaws, meeting procedures, financial policies
- **ai-behavior-baseline**: Expected AI behavior patterns for drift detection
- **reasoning-review-process**: Review criteria for validating AI outputs
- **reasoning-patterns**: Structured reasoning methodologies (root cause analysis, decision trees)

**Example** (Battery Replacement Procedure):
```markdown
# Automotive Framework: Battery Replacement Procedure

## Overview

This framework steering file provides the standard procedure for replacing a car battery.

## Safety Procedures

### Before Starting
- Park on level ground
- Turn off engine
- Wear safety glasses and gloves
- Work in well-ventilated area

### Hazard Warnings
- Battery acid: Contains sulfuric acid
- Hydrogen gas: Batteries emit explosive gas
- Heavy weight: Batteries weigh 30-50 lbs

## Required Tools
- 10mm and 13mm wrenches
- Battery terminal cleaner
- Safety glasses and gloves

## Replacement Procedure

### Step 1: Disconnect Old Battery
**CRITICAL: Always disconnect negative terminal first**

1. Loosen negative (-) terminal clamp bolt
2. Lift clamp off terminal
3. Loosen positive (+) terminal clamp bolt
4. Lift clamp off terminal

### Step 2: Remove Old Battery
1. Remove hold-down clamp
2. Lift battery carefully using proper technique
3. Inspect battery tray for corrosion

[... additional steps ...]

## Usage Guidelines

Reference this framework from task steering files when performing battery replacement.
```

**When to Update**:
- Reference material changes (new versions, updates)
- New domain-specific knowledge added
- Quarterly review of AI baselines


## Using the Framework

### Activating Context for a Task

When working on a task in Kiro, activate the task steering file to provide complete context:

1. **In Kiro Chat**: Use the `#` context key to reference the task file:
   ```
   #.kiro/steering/tasks/replace-car-battery/context.md
   
   I'm ready to replace the car battery. Can you walk me through the procedure?
   ```

2. **Kiro Loads Context**: Kiro automatically loads:
   - The task steering file
   - All referenced parent files (project, household)
   - All referenced framework files
   - Complete context chain

3. **Work with Full Context**: Kiro now has access to:
   - Task objectives and success criteria
   - Project goals and constraints
   - Household schedules and preferences
   - Framework procedures and reference knowledge

### Context Composition Patterns

#### Pattern 1: Task → Project → Household → Framework

```
Task: Replace Car Battery
  ↓ references
Project: Car Maintenance
  ↓ references
Household: Household Context
  ↓ references
Framework: Battery Replacement Procedure
```

**Result**: Kiro has task details + project goals + household constraints + procedure reference

#### Pattern 2: Task → Role → Household → Framework

```
Task: Prepare Board Meeting Agenda
  ↓ references
Role: Non-Profit President
  ↓ references
Household: Household Context
  ↓ references
Framework: Meeting Procedures
```

**Result**: Kiro has task details + role responsibilities + household constraints + meeting procedures

#### Pattern 3: Task → Multiple Frameworks

```
Task: Diagnose Check Engine Light
  ↓ references
Project: Car Maintenance
Framework: Diagnostic Procedures
Framework: Error Code Reference
Reasoning Framework: Root Cause Analysis
```

**Result**: Kiro has complete diagnostic context with structured reasoning methodology


### Working with Quality Gate Hooks

Quality gate hooks review critical decisions before execution.

#### Data Decision Quality Gate

**Triggers When**: Kiro proposes to delete or modify data

**What It Does**:
1. Detects data operation type (deletion, modification, sensitive data)
2. Generates impact summary
3. Requests your approval
4. Logs your decision
5. Blocks execution if you reject

**Example Interaction**:
```
======================================================================
DATA DECISION QUALITY GATE
======================================================================

A data operation requires your approval:

Operation Type: delete
Affected File: old-credentials/api_keys.json
Impact Classification: Deletion, Sensitive Data
⚠️  WARNING: This operation will permanently delete data
🔒 PRIVACY: This operation involves sensitive data

----------------------------------------------------------------------

Approve this operation? (yes/no): yes
```

**Best Practices**:
- Review the impact summary carefully
- Verify you have backups before approving deletions
- Reject if unsure and investigate further
- Check logs regularly to review past decisions

#### Financial Decision Quality Gate

**Triggers When**: Kiro proposes an operation with monetary impact

**What It Does**:
1. Calculates monetary impact
2. Compares against configured threshold
3. Auto-approves if below threshold
4. Requests approval if above threshold
5. Logs decision
6. Blocks execution if you reject

**Threshold Configuration** (in `.kiro/hooks/config.json`):
```json
"thresholds": {
  "auto_approve_max": 50,
  "require_review_min": 50,
  "currency": "USD"
}
```

**Example Interaction**:
```
======================================================================
FINANCIAL DECISION QUALITY GATE
======================================================================

A financial decision requires your approval:

Operation Type: purchase
Item: Car battery (Group 51R, 500 CCA)
Cost: $125.00 USD
Budget: $150.00 available
Remaining: $25.00 after purchase
Threshold: $50.00 (exceeded)

----------------------------------------------------------------------

Approve this operation? (yes/no): yes
```

**Best Practices**:
- Set thresholds appropriate for your budget
- Review budget constraints in project/household context
- Track spending through log files
- Adjust thresholds as needed


### Working with Verification Hooks

Verification hooks validate AI outputs against baseline patterns and framework references.

#### AI Drift Detection

**Triggers When**: After Kiro generates any output

**What It Does**:
1. Loads baseline behavior patterns
2. Compares current output against baseline
3. Calculates deviation scores
4. Logs significant deviations (non-blocking)
5. Continues execution regardless

**Deviation Types Detected**:
- Response length outside expected range
- Missing code blocks in technical responses
- Insufficient citations for factual claims
- Missing expected reasoning patterns
- Incorrect output formatting

**Example Log Entry** (`.kiro/logs/ai-drift.md`):
```markdown
## 2026-02-25T14:40:00Z AI Drift Detected

**Deviation Type**: Response Length
**Severity**: Significant
**Deviation Score**: 0.65
**Expected Pattern**: 200-500 words for standard queries
**Observed Pattern**: Response too short: 120 words (expected 200-500)
```

**Best Practices**:
- Review drift logs monthly to identify trends
- Update baseline patterns quarterly
- Investigate significant deviations
- Use drift data to refine expectations

#### Hallucination Detection

**Triggers When**: Kiro makes factual claims in output

**What It Does**:
1. Extracts factual claims from output
2. Validates claims against active steering files
3. Flags unsupported claims
4. Requires your confirmation for flagged outputs
5. Logs potential hallucinations
6. Blocks execution if you reject

**Claim Types**:
- Factual statements (is, are, was, were)
- Procedural claims (must, should, requires)
- Numerical claims (specific numbers, percentages)
- Reference claims (section numbers, codes)

**Example Interaction**:
```
⚠️  Potential hallucination detected - unsupported factual claims found:

1. The battery requires 500 CCA minimum for this vehicle
   Status: Unsupported
   Issue: No supporting evidence found in active steering files

2. The replacement cost will be approximately $150
   Status: Citation Required
   Issue: Citation required for critical decision context

Please review these claims and:
- Confirm if they are correct (will proceed with execution)
- Reject if they are incorrect (will block execution)
- Update steering files with correct information if needed
```

**Best Practices**:
- Review flagged claims carefully
- Update steering files with correct information
- Use citations in critical contexts (data/financial decisions)
- Mark inferences explicitly (assume, likely, probably)

#### Reasoning Review

**Triggers When**: Before executing critical operations (data/financial decisions)

**What It Does**:
1. Loads review criteria from framework
2. Applies base criteria (factual accuracy, logical consistency, completeness, context alignment)
3. Applies domain-specific criteria
4. Calculates scores for each criterion
5. Logs results
6. Blocks execution if validation fails

**Review Criteria**:
- **Factual Accuracy**: Claims supported or marked as inference
- **Logical Consistency**: No contradictions in reasoning
- **Completeness**: All required information present
- **Context Alignment**: Respects steering file constraints

**Example Failure**:
```
✗ Reasoning review failed:
  - Factual Accuracy: 8/12 unsupported claims. Examples: The battery requires...
  - Completeness: Missing: considerations
```

**Best Practices**:
- Ensure outputs address all task objectives
- Provide supporting evidence for claims
- Follow logical reasoning chains
- Respect constraints from steering files

#### Framework Compliance

**Triggers When**: Reasoning framework is referenced in task/project steering

**What It Does**:
1. Identifies active reasoning frameworks
2. Loads framework structure
3. Validates output follows framework steps
4. Logs compliance status
5. Flags non-compliance to user

**Example Frameworks**:
- Root cause analysis (5 Whys, Fishbone)
- Decision trees
- Risk assessment matrices
- Troubleshooting procedures

**Example Interaction**:
```
⚠️  Reasoning framework compliance issues detected:

Framework: Automotive Diagnostic Procedure
Status: Partial Compliance (67%)
Steps found: 2/3
Missing steps:
  - Step 3: Inspect Catalytic Converter

The output does not fully follow the referenced reasoning framework(s).
Please review and ensure all framework steps are addressed.
```

**Best Practices**:
- Reference appropriate frameworks in task steering
- Follow framework steps in order
- Document completion of each step
- Use frameworks for recurring analysis patterns


## Log Review and Maintenance

### Understanding Log Files

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

### Regular Log Review

**Weekly Review** (15-30 minutes):
1. Review quality gate logs (data-decisions.md, financial-decisions.md)
   - Check for patterns in approvals/rejections
   - Verify decisions align with goals
   - Identify areas for improved guidance

2. Review verification logs (hallucination-flags.md, reasoning-reviews.md)
   - Check for recurring issues
   - Update steering files with missing information
   - Refine review criteria if needed

**Monthly Review** (30-60 minutes):
1. Review drift detection logs (ai-drift.md)
   - Identify trends in AI behavior changes
   - Update baseline patterns if expectations have evolved
   - Investigate significant deviations

2. Review framework compliance logs (framework-compliance.md)
   - Check framework adherence rates
   - Refine framework definitions if needed
   - Add new frameworks for recurring patterns

**Quarterly Review** (1-2 hours):
1. Update AI behavior baseline
   - Review drift logs for the quarter
   - Adjust expected patterns based on actual usage
   - Update deviation thresholds if needed

2. Refine review criteria
   - Review reasoning-reviews.md for the quarter
   - Add domain-specific criteria for new contexts
   - Adjust scoring thresholds based on experience

3. Archive old logs
   - Move logs older than 90 days to `.kiro/logs/archive/`
   - Maintain recent logs for quick reference
   - Keep archived logs for long-term analysis

### Log Maintenance Commands

```bash
# Create archive directory
mkdir -p .kiro/logs/archive

# Archive logs older than 90 days (example for data-decisions.md)
# Manual process: review log file, copy old entries to archive, remove from main file

# Check log file sizes
ls -lh .kiro/logs/*.md

# Count log entries
grep -c "^## " .kiro/logs/data-decisions.md
```

### Using Logs for Improvement

**Identify Patterns**:
- Frequent rejections of certain operation types
- Recurring hallucinations about specific topics
- Consistent drift in particular dimensions
- Framework compliance issues with specific patterns

**Take Action**:
- Update steering files with missing information
- Adjust quality gate thresholds
- Refine baseline patterns
- Create new framework files for recurring methodologies
- Add domain-specific review criteria

**Example**: If hallucination logs show frequent unsupported claims about battery specifications:
1. Add battery specification details to project or framework steering file
2. Include references to manufacturer documentation
3. Future outputs will validate against this information


## Best Practices

### Context Composition

**Do**:
- Reference parent contexts from child contexts (task → project → household)
- Reference framework files from any context layer
- Use relative paths for all references
- Keep framework files stable and reusable
- Document context composition in README files

**Don't**:
- Create circular references (A → B → A)
- Use absolute paths in references
- Mix dynamic context in framework files
- Reference tasks from projects (references flow down only)

### Steering File Management

**Creating New Files**:
1. Start with template files
2. Fill all required sections
3. Add references to parent contexts
4. Use kebab-case for directory names
5. Commit to version control

**Updating Existing Files**:
1. Review current content first
2. Make incremental changes
3. Verify references still valid
4. Update timestamps or notes
5. Commit with clear messages

**Version Control**:
- Track all steering files in git
- Write descriptive commit messages
- Review changes before committing
- Use branches for major restructuring
- Tag important milestones

### Hook Configuration

**Enabling Hooks**:
- Start with quality gate hooks (data, financial)
- Add verification hooks gradually
- Test hooks individually before enabling all
- Monitor logs to verify hook behavior
- Adjust thresholds based on experience

**Threshold Settings**:
- Start conservative (lower thresholds, more approvals)
- Adjust based on log review
- Balance safety with usability
- Document threshold rationale
- Review quarterly

**Performance Tuning**:
- Set appropriate timeouts (30-60 seconds)
- Optimize steering file loading
- Cache baseline patterns if possible
- Monitor hook execution times
- Disable hooks that cause issues

### Working with Kiro

**Activating Context**:
- Always activate task steering file for task work
- Verify Kiro loaded all referenced files
- Check active steering files list in Kiro
- Update steering files before starting work

**Providing Feedback**:
- Approve/reject quality gate decisions thoughtfully
- Confirm/reject flagged hallucinations carefully
- Review reasoning review failures
- Update steering files based on feedback

**Iterating on Context**:
- Start with minimal context
- Add details as needed
- Refine based on Kiro's outputs
- Remove outdated information
- Keep context current and relevant


## Common Scenarios

### Scenario 1: Household Task with Budget Constraint

**Goal**: Plan and execute a household repair with budget awareness

**Setup**:
1. Create household context with budget constraints
2. Create project for home maintenance
3. Create task for specific repair
4. Reference framework for repair procedures (if available)

**Steering Files**:
```
.kiro/steering/household/context.md (budget: $500/month for maintenance)
.kiro/steering/projects/home-maintenance/context.md
.kiro/steering/tasks/fix-leaky-faucet/context.md
```

**Task References**:
```markdown
- Project: [[../../projects/home-maintenance/context.md]]
- Household: [[../../household/context.md]]
```

**Kiro Interaction**:
```
#.kiro/steering/tasks/fix-leaky-faucet/context.md

I need to fix a leaky faucet in the kitchen. Can you help me plan this repair?
```

**Expected Behavior**:
- Kiro considers household budget constraints
- Financial decision hook triggers if cost exceeds threshold
- Kiro provides cost-effective solutions
- Decision logged for budget tracking

### Scenario 2: Organizational Decision with Bylaws

**Goal**: Make an organizational decision that complies with bylaws

**Setup**:
1. Create role context for organizational position
2. Create framework file with bylaws
3. Create project for organizational initiative
4. Create task for specific decision

**Steering Files**:
```
.kiro/steering/roles/non-profit-president/context.md
.kiro/steering/framework/organizational/bylaws.md
.kiro/steering/projects/fundraising-campaign/context.md
.kiro/steering/tasks/approve-campaign-budget/context.md
```

**Task References**:
```markdown
- Project: [[../../projects/fundraising-campaign/context.md]]
- Role: [[../../roles/non-profit-president/context.md]]
- Framework: [[../../framework/organizational/bylaws.md]]
```

**Expected Behavior**:
- Kiro checks decision authority from role context
- Reasoning review validates against bylaws
- Hallucination detection requires citations to bylaw sections
- Decision logged with bylaw references

### Scenario 3: Technical Task with Diagnostic Framework

**Goal**: Diagnose and fix a technical issue using structured methodology

**Setup**:
1. Create project for system maintenance
2. Create framework file with diagnostic procedure
3. Create reasoning framework for troubleshooting
4. Create task for specific issue

**Steering Files**:
```
.kiro/steering/projects/car-maintenance/context.md
.kiro/steering/framework/automotive/diagnostic-procedures.md
.kiro/steering/framework/reasoning-patterns/root-cause-analysis.md
.kiro/steering/tasks/diagnose-check-engine-light/context.md
```

**Task References**:
```markdown
- Project: [[../../projects/car-maintenance/context.md]]
- Framework: [[../../framework/automotive/diagnostic-procedures.md]]
- Reasoning Framework: [[../../framework/reasoning-patterns/root-cause-analysis.md]]
```

**Expected Behavior**:
- Kiro follows diagnostic procedure steps
- Framework compliance hook validates step completion
- Reasoning review checks for systematic approach
- Output includes error codes and diagnostic data


## Troubleshooting

### Issue: Circular Reference Detected

**Symptoms**: Error message showing circular reference chain (A→B→C→A)

**Cause**: Steering files reference each other in a cycle

**Solution**:
1. Review the reference chain in the error message
2. Identify which reference creates the cycle
3. Refactor steering files to break the cycle
4. Remember: references should only flow down the hierarchy
   - Framework files cannot reference other layers
   - Household cannot reference roles/projects/tasks
   - Roles cannot reference projects/tasks
   - Projects cannot reference tasks

**Example Fix**:
```
Before (circular):
Task A → Project B → Task A (CIRCULAR!)

After (corrected):
Task A → Project B → Household C
```

### Issue: Hook Not Executing

**Symptoms**: Expected hook doesn't run

**Possible Causes**:
- Hook disabled in config.json
- Trigger conditions not met
- Hook script has errors

**Solutions**:
1. Check config.json: `"enabled": true`
2. Verify trigger conditions match your operation
3. Test hook directly:
   ```bash
   python .kiro/hooks/hook_name.py
   ```
4. Check hook logs for errors

### Issue: Baseline File Missing

**Symptoms**: Warning that baseline file not found

**Cause**: AI behavior baseline not created yet

**Solution**:
1. Create baseline file:
   ```bash
   mkdir -p .kiro/steering/framework/ai-behavior-baseline
   cp .kiro/steering/framework/ai-behavior-baseline/.template/baseline.md \
      .kiro/steering/framework/ai-behavior-baseline/baseline.md
   ```
2. Edit baseline.md with your expected patterns
3. Drift detection will use your baseline

### Issue: Too Many Hallucination Flags

**Symptoms**: Frequent unsupported claim flags

**Cause**: Steering files missing information that Kiro needs

**Solution**:
1. Review hallucination logs to identify common unsupported claims
2. Add missing information to appropriate steering files:
   - Factual data → Framework files
   - Project details → Project context
   - Constraints → Household/role context
3. Include references to source documentation
4. Future outputs will validate against updated information

### Issue: Framework Compliance Failures

**Symptoms**: Outputs consistently fail framework compliance

**Possible Causes**:
- Framework steps too rigid
- Output doesn't explicitly show steps
- Framework file poorly structured

**Solutions**:
1. Review framework file structure
2. Ensure framework steps are clear and achievable
3. Provide examples in framework file
4. Consider if framework is appropriate for the task
5. Refine framework based on compliance logs

### Issue: Quality Gate Blocking Too Often

**Symptoms**: Frequent approval requests for minor operations

**Cause**: Thresholds set too low

**Solution**:
1. Review quality gate logs to identify patterns
2. Adjust thresholds in config.json:
   ```json
   "thresholds": {
     "auto_approve_max": 100,  // Increased from 50
     "require_review_min": 100,
     "currency": "USD"
   }
   ```
3. Balance safety with usability
4. Monitor logs after adjustment


## Advanced Topics

### Creating Custom Reasoning Frameworks

Reasoning frameworks provide structured methodologies for analysis and decision-making.

**When to Create**:
- You have a recurring analysis pattern
- A specific methodology applies to multiple tasks
- You want to ensure consistent reasoning approach

**Steps**:
1. Create framework file:
   ```bash
   mkdir -p .kiro/steering/framework/reasoning-patterns
   cp .kiro/steering/framework/reasoning-patterns/.template/pattern.md \
      .kiro/steering/framework/reasoning-patterns/my-framework.md
   ```

2. Define framework structure:
   ```markdown
   # Reasoning Pattern: Root Cause Analysis
   
   ## Pattern Structure
   
   ### Step 1: Identify the Problem
   **Objective**: Clearly define what is wrong
   **Actions**:
   - State the observed symptom
   - Quantify the impact
   - Establish timeline
   
   ### Step 2: Gather Data
   **Objective**: Collect relevant information
   **Actions**:
   - Review error logs
   - Check system status
   - Interview stakeholders
   
   ### Step 3: Identify Possible Causes
   **Objective**: Brainstorm potential root causes
   **Actions**:
   - Use 5 Whys technique
   - Create fishbone diagram
   - Consider all factors
   
   [... additional steps ...]
   ```

3. Reference from task steering:
   ```markdown
   - Reasoning Framework: [[../../framework/reasoning-patterns/root-cause-analysis.md]]
   ```

4. Framework compliance hook validates output follows steps

### Domain-Specific Review Criteria

Add custom review criteria for specialized contexts.

**Example** (Automotive Domain):
```markdown
# Reasoning Review Process

## Domain-Specific Criteria

### Automotive Repair Context

When framework steering files reference automotive repair procedures:

- **Error Code Lookup**: Must include error code lookup in diagnostic procedures
- **Safety Procedures**: Must reference safety procedures from service bulletins
- **Torque Specifications**: Must include torque specifications from repair manuals
- **Part Numbers**: Must verify part numbers against service documentation
```

**How It Works**:
- Reasoning review hook detects automotive framework references
- Applies automotive-specific criteria in addition to base criteria
- Validates output includes required elements
- Logs domain-specific validation results

### Multi-Level Context Hierarchies

For complex scenarios, create deeper context hierarchies.

**Example** (Department → Team → Project → Task):
```
.kiro/steering/roles/department-head/context.md
  ↓ references
.kiro/steering/roles/team-lead/context.md
  ↓ references
.kiro/steering/projects/team-project/context.md
  ↓ references
.kiro/steering/tasks/specific-task/context.md
```

**Best Practices**:
- Keep hierarchies manageable (3-4 levels max)
- Each level should add meaningful context
- Avoid redundant information across levels
- Use framework files for shared knowledge

### Integrating External Documentation

Reference external documentation in framework files.

**Example**:
```markdown
# Automotive Framework: Service Bulletins

## Overview

This framework references manufacturer service bulletins for vehicle-specific procedures.

## Service Bulletin References

### Honda Civic 2015

- **Battery Replacement**: TSB 15-042 (Memory retention procedure)
- **Check Engine Light**: TSB 15-089 (Common P0420 causes)
- **Oil Change**: TSB 15-012 (Oil specification requirements)

## External Links

- Honda Service Information: https://techinfo.honda.com
- NHTSA Recalls: https://www.nhtsa.gov/recalls

## Usage

Reference specific TSB numbers in task steering files when applicable.
```

**Benefits**:
- Centralized reference documentation
- Easy updates when documentation changes
- Hallucination detection validates against references
- Audit trail of information sources


## Appendix

### Directory Structure Reference

Complete directory structure for the Reasoning Context Framework:

```
.kiro/
├── steering/
│   ├── README.md                          # Framework documentation
│   ├── framework/                         # Stable reference knowledge
│   │   ├── ai-behavior-baseline/
│   │   │   └── baseline.md               # AI behavior patterns
│   │   ├── reasoning-review-process/
│   │   │   └── criteria.md               # Review criteria
│   │   ├── reasoning-patterns/
│   │   │   ├── .template/
│   │   │   │   └── pattern.md            # Framework template
│   │   │   └── {pattern-name}.md         # Specific frameworks
│   │   └── {domain-name}/
│   │       └── {file-name}.md            # Domain-specific knowledge
│   ├── household/
│   │   └── context.md                    # Household context
│   ├── roles/
│   │   └── {role-name}/
│   │       └── context.md                # Role-specific context
│   ├── projects/
│   │   ├── .template/
│   │   │   └── context.md                # Project template
│   │   └── {project-name}/
│   │       └── context.md                # Project-specific context
│   └── tasks/
│       ├── .template/
│       │   └── context.md                # Task template
│       └── {task-name}/
│           └── context.md                # Task-specific context
├── hooks/
│   ├── README.md                          # Hook documentation
│   ├── config.json                        # Hook configuration
│   ├── data_decision_gate.py             # Data quality gate
│   ├── financial_decision_gate.py        # Financial quality gate
│   ├── drift_detection.py                # AI drift detection
│   ├── hallucination_detection.py        # Hallucination detection
│   ├── reasoning_review.py               # Reasoning review
│   ├── framework_compliance.py           # Framework compliance
│   ├── log_utils.py                      # Logging utilities
│   ├── reference_resolver.py             # Reference resolution
│   ├── context_loader.py                 # Context loading
│   ├── orchestrator.py                   # Hook orchestration
│   ├── register_hooks.py                 # Hook registration
│   └── test_hooks.py                     # Hook testing utility
├── logs/
│   ├── data-decisions.md                 # Data decision log
│   ├── financial-decisions.md            # Financial decision log
│   ├── ai-drift.md                       # AI drift log
│   ├── hallucination-flags.md            # Hallucination log
│   ├── reasoning-reviews.md              # Reasoning review log
│   ├── framework-compliance.md           # Framework compliance log
│   └── archive/                          # Archived logs (90+ days)
└── docs/
    └── reasoning-context-framework-guide.md  # This guide
```

### File Naming Conventions

- **Directories**: kebab-case (e.g., `car-maintenance`, `non-profit-president`)
- **Context Files**: Always named `context.md`
- **Framework Files**: Descriptive kebab-case (e.g., `battery-replacement-procedure.md`)
- **Template Directories**: Named `.template`
- **Log Files**: kebab-case with `.md` extension (e.g., `data-decisions.md`)

### Reference Syntax

**Steering File References**:
```markdown
[[../../path/to/file.md]]
```

**Relative Path Rules**:
- Always use relative paths from the current file
- Use `../` to go up one directory level
- Use forward slashes `/` for cross-platform compatibility

**Example Reference Chain**:
```markdown
# Task file: .kiro/steering/tasks/my-task/context.md
- Project: [[../../projects/my-project/context.md]]
- Household: [[../../household/context.md]]
- Framework: [[../../framework/automotive/procedure.md]]
```

### Hook Configuration Reference

**Complete Hook Configuration Example**:
```json
{
  "hooks": {
    "data_decision_gate": {
      "enabled": true,
      "script": ".kiro/hooks/data_decision_gate.py",
      "trigger": "before_file_operation",
      "conditions": [
        "operation_type in ['delete', 'modify']"
      ],
      "action": "require_user_approval",
      "log_path": ".kiro/logs/data-decisions.md",
      "timeout_seconds": 30
    }
  },
  "global_settings": {
    "default_timeout_seconds": 30,
    "log_timestamp_format": "ISO8601",
    "enable_context_tracking": true,
    "hook_failure_default_action": "block"
  }
}
```

### Useful Commands

**Setup Commands**:
```bash
# Initialize directory structure
mkdir -p .kiro/{steering/{framework,household,roles,projects,tasks},hooks,logs,docs}

# Copy templates
cp -r .kiro/steering/.templates/* .kiro/steering/

# Register hooks
python .kiro/hooks/register_hooks.py
```

**Maintenance Commands**:
```bash
# Check log file sizes
ls -lh .kiro/logs/*.md

# Count log entries
grep -c "^## " .kiro/logs/data-decisions.md

# Archive old logs
mkdir -p .kiro/logs/archive
# (manually move old entries)

# Test hooks
python .kiro/hooks/test_hooks.py --all

# Run property tests
pytest .kiro/hooks/test_*.py
```

**Git Commands**:
```bash
# Track steering files
git add .kiro/steering/

# Commit changes
git commit -m "Update task context for battery replacement"

# View history
git log --oneline .kiro/steering/tasks/replace-car-battery/context.md
```

### Additional Resources

- **Steering Files README**: `.kiro/steering/README.md`
- **Hooks README**: `.kiro/hooks/README.md`
- **Example Steering Files**: `.kiro/steering/tasks/replace-car-battery/context.md`
- **Hook Test Documentation**: `.kiro/hooks/TEST_README.md`
- **Error Handling Guide**: `.kiro/hooks/ERROR_HANDLING.md`

### Getting Help

If you encounter issues:

1. Review this guide and troubleshooting section
2. Check log files for error details (`.kiro/logs/`)
3. Test hooks individually using command-line interfaces
4. Review property-based test results
5. Check steering file references for circular dependencies
6. Verify hook configuration in `config.json`

### Version Information

- **Framework Version**: 1.0.0
- **Last Updated**: 2026-02-25
- **Compatibility**: Kiro IDE (current version)
- **Python Requirements**: 3.8+

---

**End of User Guide**
