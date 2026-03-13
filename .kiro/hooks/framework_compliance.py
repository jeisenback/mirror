"""
Reasoning Framework Compliance Hook

This hook validates that AI outputs follow documented reasoning framework
methodologies when frameworks are referenced in active steering files.
It checks for framework structure adherence and logs compliance status.

Requirements: 17.3, 17.4, 17.5
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any
from enum import Enum

from log_utils import append_log_entry, get_active_steering_files


class ComplianceStatus(Enum):
    """Compliance status levels."""
    COMPLIANT = "Compliant"
    PARTIAL = "Partial Compliance"
    NON_COMPLIANT = "Non-Compliant"
    NO_FRAMEWORK = "No Framework Active"


class FrameworkStep:
    """Container for a framework step definition."""
    
    def __init__(self, step_number: int, step_name: str, objective: str, required_actions: List[str]):
        self.step_number = step_number
        self.step_name = step_name
        self.objective = objective
        self.required_actions = required_actions
        self.found_in_output = False
        self.evidence: List[str] = []


class ReasoningFramework:
    """Container for a reasoning framework definition."""
    
    def __init__(self, name: str, file_path: str):
        self.name = name
        self.file_path = file_path
        self.purpose = ""
        self.applicable_contexts: List[str] = []
        self.steps: List[FrameworkStep] = []
        self.validation_criteria: List[str] = []


def get_framework_references(workspace_root: Path) -> List[str]:
    """
    Identify active reasoning frameworks from task/project steering references.
    
    Args:
        workspace_root: Path to workspace root
        
    Returns:
        List of framework file paths referenced in active steering files
    """
    active_files = get_active_steering_files(workspace_root)
    framework_refs = []
    
    # Pattern to match framework references
    framework_pattern = r'\[\[.*?framework/reasoning-patterns/([^\]]+\.md)\]\]'
    
    for file_path in active_files:
        # Focus on task and project steering files
        if not ('tasks/' in file_path or 'projects/' in file_path):
            continue
        
        full_path = workspace_root / file_path
        if not full_path.exists():
            continue
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find framework references
            matches = re.findall(framework_pattern, content, re.IGNORECASE)
            for match in matches:
                framework_path = f".kiro/steering/framework/reasoning-patterns/{match}"
                if framework_path not in framework_refs:
                    framework_refs.append(framework_path)
        
        except Exception:
            continue
    
    return framework_refs


def load_framework_structure(framework_path: Path) -> Optional[ReasoningFramework]:
    """
    Load framework structure from a framework steering file.
    
    Args:
        framework_path: Path to framework file
        
    Returns:
        ReasoningFramework object or None if file doesn't exist
        
    Note:
        If framework file is missing, prompts user and returns None.
        This allows the caller to decide whether to proceed without framework validation.
    """
    if not framework_path.exists():
        print(f"WARNING: Framework file not found at {framework_path}")
        print("Framework compliance validation cannot be performed.")
        
        response = input("Proceed without framework validation? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            raise FileNotFoundError(
                f"Framework file not found at {framework_path}. "
                f"Create the framework file or choose to proceed without validation."
            )
        
        return None
    
    try:
        with open(framework_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"WARNING: Failed to read framework file: {str(e)}")
        print("Framework compliance validation cannot be performed.")
        
        response = input("Proceed without framework validation? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            raise IOError(f"Failed to read framework file: {str(e)}")
        
        return None
    
    # Extract framework name from file
    name_match = re.search(r'#\s*Reasoning Pattern:\s*(.+)', content)
    framework_name = name_match.group(1).strip() if name_match else framework_path.stem
    
    framework = ReasoningFramework(framework_name, str(framework_path))
    
    # Extract purpose
    purpose_match = re.search(r'\*\*Purpose\*\*:\s*(.+?)(?:\n|$)', content)
    if purpose_match:
        framework.purpose = purpose_match.group(1).strip()
    
    # Extract applicable contexts
    contexts_match = re.search(r'\*\*Applicable Contexts\*\*:\s*(.+?)(?:\n|$)', content)
    if contexts_match:
        framework.applicable_contexts = [ctx.strip() for ctx in contexts_match.group(1).split(',')]
    
    # Extract steps
    step_pattern = r'###\s*Step\s+(\d+):\s*(.+?)\n\n\*\*Objective\*\*:\s*(.+?)\n\n\*\*Actions\*\*:\s*\n((?:- .+?\n)+)'
    step_matches = re.finditer(step_pattern, content, re.DOTALL)
    
    for match in step_matches:
        step_num = int(match.group(1))
        step_name = match.group(2).strip()
        objective = match.group(3).strip()
        actions_text = match.group(4).strip()
        
        # Parse actions
        actions = [line.strip('- ').strip() for line in actions_text.split('\n') if line.strip().startswith('-')]
        
        step = FrameworkStep(step_num, step_name, objective, actions)
        framework.steps.append(step)
    
    # Extract validation criteria
    validation_section = re.search(
        r'##\s*Validation Criteria.*?###\s*Structure Compliance\s*\n((?:- \[.\] .+?\n)+)',
        content,
        re.DOTALL
    )
    if validation_section:
        criteria_text = validation_section.group(1)
        framework.validation_criteria = [
            line.strip('- [ ] ').strip() 
            for line in criteria_text.split('\n') 
            if line.strip().startswith('- [')
        ]
    
    return framework


def validate_framework_compliance(
    output: str,
    framework: ReasoningFramework
) -> Tuple[ComplianceStatus, Dict[str, Any]]:
    """
    Validate that output follows framework structure and steps.
    
    Args:
        output: AI output to validate
        framework: ReasoningFramework to validate against
        
    Returns:
        Tuple of (compliance_status, details_dict)
    """
    details = {
        'framework_name': framework.name,
        'total_steps': len(framework.steps),
        'steps_found': 0,
        'missing_steps': [],
        'step_evidence': {}
    }
    
    if not framework.steps:
        return (ComplianceStatus.NO_FRAMEWORK, details)
    
    # Check for each framework step in the output
    for step in framework.steps:
        # Look for step indicators
        step_patterns = [
            rf'\b{step.step_number}\.',  # Numbered step
            rf'\bstep\s+{step.step_number}\b',  # "Step N"
            rf'\b{re.escape(step.step_name)}\b',  # Step name
        ]
        
        found = False
        evidence = []
        
        for pattern in step_patterns:
            matches = re.finditer(pattern, output, re.IGNORECASE)
            for match in matches:
                found = True
                # Extract context around match
                start = max(0, match.start() - 50)
                end = min(len(output), match.end() + 100)
                context = output[start:end].strip()
                evidence.append(context)
        
        # Check for action keywords from the step
        if not found and step.required_actions:
            # Extract key action verbs
            action_keywords = []
            for action in step.required_actions:
                # Extract first verb or key noun
                words = re.findall(r'\b[A-Za-z]+\b', action)
                if words:
                    action_keywords.append(words[0].lower())
            
            # Check if action keywords appear in output
            for keyword in action_keywords:
                if keyword in output.lower():
                    found = True
                    evidence.append(f"Action keyword '{keyword}' found")
                    break
        
        if found:
            step.found_in_output = True
            step.evidence = evidence
            details['steps_found'] += 1
            details['step_evidence'][f"Step {step.step_number}"] = evidence
        else:
            details['missing_steps'].append(f"Step {step.step_number}: {step.step_name}")
    
    # Determine compliance status
    compliance_rate = details['steps_found'] / details['total_steps']
    
    if compliance_rate >= 0.9:  # 90%+ steps present
        status = ComplianceStatus.COMPLIANT
    elif compliance_rate >= 0.6:  # 60-89% steps present
        status = ComplianceStatus.PARTIAL
    else:  # <60% steps present
        status = ComplianceStatus.NON_COMPLIANT
    
    details['compliance_rate'] = f"{compliance_rate:.0%}"
    
    return (status, details)


def check_framework_compliance(
    output: str,
    workspace_root: Optional[Path] = None
) -> List[Tuple[ReasoningFramework, ComplianceStatus, Dict[str, Any]]]:
    """
    Check compliance for all active reasoning frameworks.
    
    Args:
        output: AI output to validate
        workspace_root: Path to workspace root
        
    Returns:
        List of (framework, status, details) tuples
    """
    if workspace_root is None:
        workspace_root = Path.cwd()
    
    # Get framework references
    framework_refs = get_framework_references(workspace_root)
    
    if not framework_refs:
        return []
    
    results = []
    
    for ref in framework_refs:
        framework_path = workspace_root / ref
        framework = load_framework_structure(framework_path)
        
        if framework is None:
            continue
        
        status, details = validate_framework_compliance(output, framework)
        results.append((framework, status, details))
    
    return results


def log_compliance_results(
    results: List[Tuple[ReasoningFramework, ComplianceStatus, Dict[str, Any]]],
    workspace_root: Path
) -> None:
    """
    Log framework compliance results to log file.
    
    Args:
        results: List of compliance check results
        workspace_root: Path to workspace root
    """
    for framework, status, details in results:
        # Build evidence section
        evidence_lines = []
        for step_name, evidence_list in details.get('step_evidence', {}).items():
            evidence_lines.append(f"  {step_name}:")
            for evidence in evidence_list[:2]:  # Limit to 2 pieces of evidence per step
                evidence_lines.append(f"    - {evidence[:100]}...")
        
        evidence_text = "\n".join(evidence_lines) if evidence_lines else "No evidence found"
        
        # Build missing steps section
        missing_steps = details.get('missing_steps', [])
        missing_text = "\n  - ".join(missing_steps) if missing_steps else "None"
        
        # Create log entry fields
        fields = {
            "Framework": framework.name,
            "Framework File": framework.file_path,
            "Compliance Status": status.value,
            "Compliance Rate": details.get('compliance_rate', 'N/A'),
            "Steps Found": f"{details.get('steps_found', 0)}/{details.get('total_steps', 0)}",
            "Missing Steps": missing_text if missing_steps else "None",
            "Evidence": "\n" + evidence_text
        }
        
        # Write log entry
        log_path = workspace_root / ".kiro" / "logs" / "framework-compliance.md"
        append_log_entry(log_path, "Framework Compliance Check", fields, workspace_root)


def format_compliance_message(
    results: List[Tuple[ReasoningFramework, ComplianceStatus, Dict[str, Any]]]
) -> Optional[str]:
    """
    Format compliance results into a user-friendly message.
    
    Args:
        results: List of compliance check results
        
    Returns:
        Formatted message string or None if all compliant
    """
    non_compliant = [
        (fw, status, details) for fw, status, details in results
        if status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIAL]
    ]
    
    if not non_compliant:
        return None
    
    lines = [
        "⚠️  Reasoning framework compliance issues detected:",
        ""
    ]
    
    for framework, status, details in non_compliant:
        lines.append(f"Framework: {framework.name}")
        lines.append(f"Status: {status.value} ({details.get('compliance_rate', 'N/A')})")
        lines.append(f"Steps found: {details.get('steps_found', 0)}/{details.get('total_steps', 0)}")
        
        missing = details.get('missing_steps', [])
        if missing:
            lines.append("Missing steps:")
            for step in missing[:3]:  # Show first 3 missing steps
                lines.append(f"  - {step}")
            if len(missing) > 3:
                lines.append(f"  ... and {len(missing) - 3} more")
        
        lines.append("")
    
    lines.extend([
        "The output does not fully follow the referenced reasoning framework(s).",
        "Please review and ensure all framework steps are addressed.",
        ""
    ])
    
    return "\n".join(lines)


def framework_compliance_hook(
    output: str,
    workspace_root: Optional[Path] = None,
    flag_non_compliance: bool = True
) -> Tuple[bool, Optional[str], List[Tuple[ReasoningFramework, ComplianceStatus, Dict[str, Any]]]]:
    """
    Main hook entry point for reasoning framework compliance checking.
    
    Args:
        output: AI output to validate
        workspace_root: Path to workspace root
        flag_non_compliance: Whether to flag non-compliance to user
        
    Returns:
        Tuple of (is_compliant, message, results)
        - is_compliant: True if all frameworks compliant or no frameworks active
        - message: Message to present to user (None if compliant)
        - results: List of compliance check results
    """
    if workspace_root is None:
        workspace_root = Path.cwd()
    
    # Check compliance
    results = check_framework_compliance(output, workspace_root)
    
    if not results:
        # No frameworks active, consider compliant
        return (True, None, [])
    
    # Log all results
    log_compliance_results(results, workspace_root)
    
    # Check if any frameworks are non-compliant
    has_issues = any(
        status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIAL]
        for _, status, _ in results
    )
    
    if has_issues and flag_non_compliance:
        message = format_compliance_message(results)
        return (False, message, results)
    
    return (True, None, results)


if __name__ == "__main__":
    # Example usage for testing
    test_output = """
    To diagnose the check engine light issue, I'll follow a systematic approach:
    
    Step 1: Verify Error Code
    First, I'll connect the OBD-II scanner to retrieve the diagnostic trouble code.
    The code P0420 indicates a catalytic converter efficiency issue.
    
    Step 2: Check Oxygen Sensor Readings
    Next, I'll examine the upstream and downstream oxygen sensor data to determine
    if the sensors are functioning correctly.
    
    Step 3: Inspect Catalytic Converter
    Finally, I'll perform a visual inspection of the catalytic converter for
    physical damage or excessive heat discoloration.
    
    Based on this analysis, the most likely cause is catalytic converter degradation.
    """
    
    is_compliant, message, results = framework_compliance_hook(test_output)
    
    if is_compliant:
        print("✓ Framework compliance check passed")
        if results:
            for fw, status, details in results:
                print(f"  - {fw.name}: {status.value} ({details.get('compliance_rate', 'N/A')})")
    else:
        print("✗ Framework compliance issues detected:")
        if message:
            print(message)
