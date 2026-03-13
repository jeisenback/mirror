# AI Behavior Baseline

## Overview

This framework steering file documents expected AI behavior patterns to enable drift detection. The baseline serves as a reference for verifying that AI outputs remain consistent and predictable over time.

## Response Characteristics

<!-- Document typical response patterns and formats -->

### Response Length

- **Standard Queries**: 200-500 words
- **Technical Explanations**: 300-800 words
- **Code Examples**: Include 10-50 lines of code with explanations
- **Simple Confirmations**: 20-100 words

### Code Block Usage

- **Frequency**: Present in 80% of technical responses
- **Format**: Use markdown code blocks with language specification
- **Comments**: Include inline comments for complex logic

### Citation Frequency

- **Factual Claims**: At least one reference per factual claim
- **Technical Information**: Reference documentation or steering files
- **Assumptions**: Explicitly state when making assumptions

## Reasoning Patterns

<!-- Document expected reasoning approaches and structures -->

### Step-by-Step Analysis

- **Multi-Step Problems**: Break into numbered steps
- **Complex Decisions**: Show decision tree or analysis flow
- **Troubleshooting**: Follow systematic diagnostic approach

### Assumption Statements

- **Explicit Assumptions**: State assumptions before conclusions
- **Context Gaps**: Acknowledge when information is incomplete
- **Inference Marking**: Clearly mark inferences vs. facts

### Alternative Consideration

- **Decision Points**: Consider at least two alternatives
- **Trade-offs**: Discuss pros and cons of options
- **Recommendations**: Justify why one option is preferred

## Output Formats

<!-- Document expected formatting conventions -->

### File Paths

- **Format**: Always use relative paths from workspace root
- **Separators**: Use forward slashes (/) for cross-platform compatibility
- **Examples**: `.kiro/steering/household/context.md`

### Command Syntax

- **Completeness**: Include full command with all required flags
- **Platform**: Adapt to user's operating system
- **Examples**: Provide working examples with expected output

### Error Messages

- **Components**: Include error code, description, and suggested resolution
- **Context**: Reference relevant steering files or documentation
- **Actionability**: Provide clear next steps for resolution

## Tone and Style

<!-- Document expected communication style -->

### Professional Tone

- **Clarity**: Use clear, concise language
- **Respect**: Maintain professional and respectful tone
- **Helpfulness**: Focus on solving user's problem

### Technical Accuracy

- **Precision**: Use correct technical terminology
- **Verification**: Verify facts against steering files
- **Corrections**: Acknowledge and correct errors promptly

## Deviation Thresholds

<!-- Document when deviations should be flagged -->

### Response Length Deviation

- **Minor**: ±30% from expected range
- **Significant**: ±50% from expected range (flag for review)

### Pattern Deviation

- **Minor**: Occasional variation in structure
- **Significant**: Consistent departure from expected patterns (flag for review)

### Format Deviation

- **Minor**: Small formatting inconsistencies
- **Significant**: Major format changes or missing required elements (flag for review)

## Notes

This baseline should be reviewed and updated quarterly to reflect evolving expectations and use patterns.

