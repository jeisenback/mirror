# Reasoning Context Framework - Steering Files

## Overview

This directory contains steering files that provide hierarchical context management for Kiro across multiple life domains. The framework uses a five-layer hierarchy (framework, household, role, project, task) with cross-references to compose context for specific activities.

## Directory Structure

```
.kiro/steering/
├── framework/              # Stable reference knowledge (manuals, standards, procedures)
│   ├── ai-behavior-baseline/
│   │   └── baseline.md
│   ├── reasoning-review-process/
│   │   └── criteria.md
│   ├── reasoning-patterns/
│   │   └── .template/
│   │       └── pattern.md
│   └── {domain-name}/
│       └── *.md
├── household/              # Household member info, schedules, preferences
│   └── context.md
├── roles/                  # Role-specific responsibilities and constraints
│   └── {role-name}/
│       └── context.md
├── projects/               # Project goals, stakeholders, timelines
│   ├── .template/
│   │   └── context.md
│   └── {project-name}/
│       └── context.md
└── tasks/                  # Task objectives and success criteria
    ├── .template/
    │   └── context.md
    └── {task-name}/
        └── context.md
```

## Context Layer Hierarchy

### Layer 1: Framework Steering Files

**Purpose**: Store stable, reusable reference knowledge that doesn't change frequently.

**Location**: `.kiro/steering/framework/{domain-name}/`

**Content Examples**:
- Automotive repair manuals and service bulletins
- Organizational bylaws and procedures
- Legal regulations and compliance standards
- AI behavior baseline patterns
- Reasoning review processes
- Reasoning framework methodologies

**Referenceable From**: Any other layer (household, role, project, task)

**When to Create**:
- When you have stable reference material that applies across multiple tasks
- When documenting procedures, standards, or methodologies
- When establishing AI behavior baselines or review criteria

**When to Update**:
- When reference material changes (new versions, updates)
- When adding new domain-specific knowledge
- Quarterly review of AI behavior baselines

### Layer 2: Household Steering File

**Purpose**: Maintain household context including member information, schedules, preferences, and constraints.

**Location**: `.kiro/steering/household/context.md`

**Content**: Household members, schedules, preferences, constraints

**Referenceable From**: Role, project, and task steering files

**When to Create**: Once during initial setup

**When to Update**:
- When household composition changes
- When schedules or preferences change
- When new constraints emerge

### Layer 3: Role Steering Files

**Purpose**: Define role-specific responsibilities, relationships, decision authority, and constraints.

**Location**: `.kiro/steering/roles/{role-name}/context.md`

**Content**: Role responsibilities, relationships, decision authority, constraints

**References**: Household steering file (where relevant)

**Referenceable From**: Project and task steering files

**When to Create**: When taking on a new role or responsibility

**When to Update**:
- When role responsibilities change
- When relationships or stakeholders change
- When decision authority changes

### Layer 4: Project Steering Files

**Purpose**: Track project-specific goals, stakeholders, timelines, and constraints.

**Location**: `.kiro/steering/projects/{project-name}/context.md`

**Content**: Project goals, stakeholders, timelines, constraints

**References**: Associated role or household steering file, relevant framework files

**Referenceable From**: Task steering files

**When to Create**: When starting a new project

**When to Update**:
- When project goals or scope change
- When timelines shift
- When stakeholders or constraints change
- At project milestones

### Layer 5: Task Steering Files

**Purpose**: Define task objectives, success criteria, and constraints with full context composition.

**Location**: `.kiro/steering/tasks/{task-name}/context.md`

**Content**: Task objectives, success criteria, constraints

**References**: Parent project/role/household steering, relevant framework files, reasoning patterns

**Referenceable From**: None (leaf layer)

**When to Create**: When starting a specific task that requires context

**When to Update**:
- When task objectives change
- When new constraints emerge
- When task is complete (mark as archived)

## Context Composition Patterns

### Pattern 1: Task with Project Context

```markdown
# Task: Replace Car Battery

## Context References

- Project: [[../../projects/car-maintenance/context.md]]
- Framework: [[../../framework/automotive/battery-replacement-procedure.md]]
```

**Result**: Kiro receives task objectives + project goals + automotive procedure reference

### Pattern 2: Task with Role Context

```markdown
# Task: Prepare Board Meeting Agenda

## Context References

- Role: [[../../roles/non-profit-president/context.md]]
- Framework: [[../../framework/organizational/meeting-procedures.md]]
```

**Result**: Kiro receives task objectives + role responsibilities + meeting procedures

### Pattern 3: Task with Household Context

```markdown
# Task: Plan Family Vacation

## Context References

- Household: [[../../household/context.md]]
```

**Result**: Kiro receives task objectives + household member info + schedules + preferences

### Pattern 4: Task with Multiple Framework References

```markdown
# Task: Diagnose Check Engine Light

## Context References

- Project: [[../../projects/car-maintenance/context.md]]
- Framework: [[../../framework/automotive/diagnostic-procedures.md]]
- Framework: [[../../framework/automotive/error-code-reference.md]]
- Reasoning Framework: [[../../framework/reasoning-patterns/root-cause-analysis.md]]
```

**Result**: Kiro receives complete context including diagnostic procedures, error codes, and reasoning methodology

### Pattern 5: Reasoning Framework Application

```markdown
# Task: Investigate Budget Variance

## Context References

- Role: [[../../roles/non-profit-president/context.md]]
- Framework: [[../../framework/financial/budget-analysis-procedures.md]]
- Reasoning Framework: [[../../framework/reasoning-patterns/variance-analysis.md]]
```

**Result**: Kiro follows structured variance analysis methodology with role context and financial procedures

## Reference Syntax

### Relative Path References

All references between steering files use relative paths:

```markdown
## Context References

- Parent: [[../../projects/project-name/context.md]]
- Framework: [[../../framework/domain-name/file-name.md]]
```

### Reference Resolution

When you activate a task steering file in Kiro:
1. Kiro loads the task steering file
2. Kiro follows all references recursively
3. Kiro builds complete context from all referenced files
4. Kiro has access to all context layers for the task

### Circular Reference Prevention

References only flow down the hierarchy:
- Framework files cannot reference other layers
- Household files cannot reference roles, projects, or tasks
- Role files cannot reference projects or tasks
- Project files cannot reference tasks

This prevents circular reference chains (A→B→C→A).

## Naming Conventions

### Directory Names

Use kebab-case for all directory names:
- `non-profit-president` (not `NonProfitPresident` or `non_profit_president`)
- `car-maintenance` (not `CarMaintenance` or `car_maintenance`)
- `replace-car-battery` (not `ReplaceBattery` or `replace_battery`)

### File Names

- Context files: Always named `context.md`
- Framework files: Descriptive names in kebab-case (e.g., `battery-replacement-procedure.md`)
- Template files: Located in `.template/` subdirectories

### Domain Names

Framework domains should be descriptive and specific:
- `automotive` (for car repair procedures)
- `organizational` (for non-profit bylaws and procedures)
- `financial` (for financial analysis procedures)
- `ai-behavior-baseline` (for AI behavior patterns)
- `reasoning-patterns` (for reasoning methodologies)

## Framework Steering Usage

### When to Use Framework Steering

Use framework steering files for:
- **Stable Reference Knowledge**: Information that doesn't change frequently
- **Reusable Procedures**: Processes that apply across multiple tasks
- **Standards and Specifications**: Technical specifications, compliance requirements
- **AI Behavior Baselines**: Expected AI behavior patterns for drift detection
- **Reasoning Methodologies**: Structured approaches to analysis and decision-making

### When NOT to Use Framework Steering

Don't use framework steering for:
- **Dynamic Context**: Information that changes frequently (use household/role/project/task layers)
- **Personal Preferences**: Individual preferences (use household layer)
- **Temporary Information**: Short-term details (use task layer)

### Framework Steering Examples

**Automotive Domain**:
- `battery-replacement-procedure.md`: Step-by-step battery replacement
- `diagnostic-procedures.md`: General diagnostic methodology
- `error-code-reference.md`: OBD-II error code definitions
- `service-bulletins.md`: Manufacturer service bulletins

**Organizational Domain**:
- `bylaws.md`: Non-profit bylaws and governance rules
- `meeting-procedures.md`: Board meeting procedures
- `financial-policies.md`: Financial management policies

**AI Behavior Domain**:
- `baseline.md`: Expected AI behavior patterns
- `criteria.md`: Reasoning review criteria
- `{pattern-name}.md`: Specific reasoning patterns

## Hook Integration

### Quality Gate Hooks

Quality gate hooks intercept operations and log decisions:
- **Data Decisions**: Logged to `.kiro/logs/data-decisions.md`
- **Financial Decisions**: Logged to `.kiro/logs/financial-decisions.md`

Hooks have access to active steering files for context-aware validation.

### Verification Hooks

Verification hooks validate outputs against baselines and frameworks:
- **AI Drift Detection**: Compares outputs against `framework/ai-behavior-baseline/baseline.md`
- **Hallucination Detection**: Validates claims against active steering files
- **Reasoning Review**: Applies criteria from `framework/reasoning-review-process/criteria.md`
- **Framework Compliance**: Validates outputs follow referenced reasoning patterns

### Hook Configuration

Hooks are configured in `.kiro/hooks/config.json` with:
- Trigger patterns (when hooks execute)
- Log paths (where to write logs)
- Timeout values (maximum execution time)
- Threshold configurations (approval thresholds)

See `.kiro/hooks/README.md` for detailed hook documentation.

## Best Practices

### Creating New Steering Files

1. **Start with Templates**: Copy from `.template/` directories
2. **Fill Required Sections**: Complete all template sections
3. **Add References**: Link to parent and framework steering files
4. **Use Relative Paths**: Always use relative paths for references
5. **Commit to Version Control**: Track changes with git

### Updating Existing Steering Files

1. **Review Current Content**: Understand existing context
2. **Make Incremental Changes**: Update specific sections
3. **Verify References**: Ensure references still valid
4. **Update Timestamps**: Note when changes were made
5. **Commit with Clear Messages**: Describe what changed and why

### Activating Context for Tasks

1. **Identify Task**: Determine what task you're working on
2. **Activate Task Steering**: Load the task steering file in Kiro
3. **Verify Context**: Confirm Kiro has access to all referenced files
4. **Proceed with Task**: Kiro now has complete context

### Maintaining Framework Steering

1. **Quarterly Review**: Review AI behavior baselines quarterly
2. **Update on Changes**: Update framework files when reference material changes
3. **Version Control**: Track all changes to framework files
4. **Document Updates**: Note what changed and why in commit messages

## Troubleshooting

### Missing Reference Target

**Symptom**: Error message indicating a referenced file doesn't exist

**Solution**:
1. Check the reference path for typos
2. Verify the referenced file exists at the specified path
3. Create the missing file or remove the reference

### Circular Reference Detected

**Symptom**: Error message showing a circular reference chain (A→B→C→A)

**Solution**:
1. Review the reference chain shown in the error
2. Identify which reference creates the cycle
3. Refactor steering files to break the cycle (references should only flow down the hierarchy)

### Hook Execution Timeout

**Symptom**: Warning that a hook execution timed out

**Solution**:
1. Review the hook configuration timeout value
2. Simplify the hook logic if possible
3. Increase timeout value if necessary
4. Check hook logs for details

### Context Not Loading

**Symptom**: Kiro doesn't seem to have access to expected context

**Solution**:
1. Verify the task steering file is activated
2. Check that all references use correct relative paths
3. Confirm referenced files exist
4. Review Kiro's active steering files list

## Examples

See `.kiro/docs/reasoning-context-framework-guide.md` for complete examples of:
- Setting up steering files for different scenarios
- Creating context composition patterns
- Configuring hooks for quality gates
- Reviewing logs and maintaining the system

