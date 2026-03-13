"""
Reasoning Review Hook

This hook applies structured review criteria to validate AI outputs systematically
before execution. It loads review criteria from the framework steering files and
evaluates outputs against factual accuracy, logical consistency, completeness,
and context alignment.

Requirements: 16.2, 16.3, 16.4, 16.5
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

from log_utils import append_log_entry, get_active_steering_files


class CriterionScore(Enum):
    """Scoring levels for review criteria."""
    PASS = "Pass"
    PARTIAL = "Partial"
    FAIL = "Fail"


class ReviewResult:
    """Container for review results."""
    
    def __init__(self):
        self.factual_accuracy: Tuple[CriterionScore, str] = (CriterionScore.PASS, "")
        self.logical_consistency: Tuple[CriterionScore, str] = (CriterionScore.PASS, "")
        self.completeness: Tuple[CriterionScore, str] = (CriterionScore.PASS, "")
        self.context_alignment: Tuple[CriterionScore, str] = (CriterionScore.PASS, "")
        self.domain_specific: Dict[str, Tuple[CriterionScore, str]] = {}
    
    def overall_pass(self) -> bool:
        """Check if all criteria passed."""
        base_criteria = [
            self.factual_accuracy[0],
            self.logical_consistency[0],
            self.completeness[0],
            self.context_alignment[0]
        ]
        
        # All base criteria must pass
        if any(score != CriterionScore.PASS for score in base_criteria):
            return False
        
        # All domain-specific criteria must pass
        if any(score != CriterionScore.PASS for score, _ in self.domain_specific.values()):
            return False
        
        return True
    
    def get_failure_reasons(self) -> List[str]:
        """Get list of failure reasons for failed criteria."""
        reasons = []
        
        if self.factual_accuracy[0] == CriterionScore.FAIL:
            reasons.append(f"Factual Accuracy: {self.factual_accuracy[1]}")
        
        if self.logical_consistency[0] == CriterionScore.FAIL:
            reasons.append(f"Logical Consistency: {self.logical_consistency[1]}")
        
        if self.completeness[0] == CriterionScore.FAIL:
            reasons.append(f"Completeness: {self.completeness[1]}")
        
        if self.context_alignment[0] == CriterionScore.FAIL:
            reasons.append(f"Context Alignment: {self.context_alignment[1]}")
        
        for criterion_name, (score, notes) in self.domain_specific.items():
            if score == CriterionScore.FAIL:
                reasons.append(f"{criterion_name}: {notes}")
        
        return reasons


def load_review_criteria(workspace_root: Path) -> Dict[str, Any]:
    """
    Load review criteria from framework steering files.
    
    Args:
        workspace_root: Path to workspace root
        
    Returns:
        Dict containing parsed review criteria
        
    Note:
        If criteria file is missing, prompts user and returns default criteria.
        This allows review to continue with base validation rules.
    """
    criteria_path = workspace_root / ".kiro" / "steering" / "framework" / "reasoning-review-process" / "criteria.md"
    
    if not criteria_path.exists():
        # In test mode (when PYTEST_CURRENT_TEST env var is set), auto-proceed with defaults
        import os
        is_test_mode = 'PYTEST_CURRENT_TEST' in os.environ
        
        if not is_test_mode:
            # Prompt user about missing criteria
            print(f"WARNING: Review criteria file not found at {criteria_path}")
            print("Using default review criteria (factual accuracy, logical consistency, completeness, context alignment).")
            print("Create criteria.md to customize reasoning review validation.")
            
            response = input("Proceed with default criteria? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                raise FileNotFoundError(
                    f"Review criteria file not found at {criteria_path}. "
                    f"Create the file or choose to proceed with defaults."
                )
        
        # Return default criteria
        return {
            "base_criteria": ["factual_accuracy", "logical_consistency", "completeness", "context_alignment"],
            "domain_specific": {}
        }
    
    # For now, return structure indicating criteria file exists
    # Full parsing would extract specific validation rules from the markdown
    return {
        "base_criteria": ["factual_accuracy", "logical_consistency", "completeness", "context_alignment"],
        "domain_specific": {},
        "criteria_file": str(criteria_path)
    }


def load_steering_content(workspace_root: Path) -> Dict[str, str]:
    """
    Load content from all active steering files for validation.
    
    Args:
        workspace_root: Path to workspace root
        
    Returns:
        Dict mapping file paths to their content
    """
    active_files = get_active_steering_files(workspace_root)
    content_map = {}
    
    for file_path in active_files:
        full_path = workspace_root / file_path
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content_map[file_path] = f.read()
            except Exception:
                # Skip files that can't be read
                continue
    
    return content_map


def validate_factual_accuracy(
    output: str,
    steering_content: Dict[str, str]
) -> Tuple[CriterionScore, str]:
    """
    Validate factual accuracy of output against steering files.
    
    Checks that factual claims are supported by steering file content
    or explicitly marked as inference/assumption.
    
    Args:
        output: AI output to validate
        steering_content: Content from active steering files
        
    Returns:
        Tuple of (score, notes)
    """
    # Extract potential factual claims (sentences with definitive statements)
    # This is a simplified heuristic - full implementation would use NLP
    claim_patterns = [
        r'\b(is|are|was|were|will be|has|have)\b',
        r'\b(must|should|shall|requires?)\b',
        r'\b\d+\s*(percent|%|dollars?|\$|years?|months?|days?)\b'
    ]
    
    claims = []
    for line in output.split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('-'):
            continue
        
        for pattern in claim_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                claims.append(line)
                break
    
    if not claims:
        return (CriterionScore.PASS, "No factual claims detected")
    
    # Check for inference markers
    inference_markers = ['assume', 'infer', 'likely', 'probably', 'may', 'might', 'could']
    unsupported_claims = []
    
    for claim in claims:
        # Check if claim has inference marker
        has_marker = any(marker in claim.lower() for marker in inference_markers)
        
        if not has_marker:
            # Check if claim content appears in steering files
            claim_words = set(claim.lower().split())
            supported = False
            
            for content in steering_content.values():
                content_words = set(content.lower().split())
                # If significant overlap, consider supported
                overlap = len(claim_words & content_words)
                if overlap > len(claim_words) * 0.3:  # 30% overlap threshold
                    supported = True
                    break
            
            if not supported:
                unsupported_claims.append(claim[:100])  # Truncate for logging
    
    if not unsupported_claims:
        return (CriterionScore.PASS, f"All {len(claims)} claims supported or marked as inference")
    
    unsupported_pct = len(unsupported_claims) / len(claims)
    
    if unsupported_pct < 0.2:  # Less than 20% unsupported
        return (CriterionScore.PASS, f"{len(unsupported_claims)} minor unsupported claims")
    elif unsupported_pct < 0.8:  # 20-80% unsupported
        return (CriterionScore.PARTIAL, f"{len(unsupported_claims)}/{len(claims)} claims unsupported")
    else:  # 80%+ unsupported
        examples = "; ".join(unsupported_claims[:3])
        return (CriterionScore.FAIL, f"{len(unsupported_claims)}/{len(claims)} unsupported claims. Examples: {examples}")


def validate_logical_consistency(output: str) -> Tuple[CriterionScore, str]:
    """
    Validate logical consistency of output.
    
    Checks for internal contradictions and invalid reasoning.
    
    Args:
        output: AI output to validate
        
    Returns:
        Tuple of (score, notes)
    """
    # Check for explicit contradictions
    contradiction_patterns = [
        (r'\b(not|never|no)\b.*\b(but|however|although)\b.*\b(is|are|will)\b', "Negation followed by affirmation"),
        (r'\b(always|must)\b.*\b(sometimes|may|might)\b', "Absolute followed by conditional"),
        (r'\b(impossible|cannot)\b.*\b(possible|can)\b', "Impossibility followed by possibility")
    ]
    
    contradictions = []
    for pattern, description in contradiction_patterns:
        matches = re.finditer(pattern, output, re.IGNORECASE | re.DOTALL)
        for match in matches:
            context = output[max(0, match.start()-50):min(len(output), match.end()+50)]
            contradictions.append(f"{description}: ...{context}...")
    
    if contradictions:
        if len(contradictions) == 1:
            return (CriterionScore.PARTIAL, f"Minor inconsistency detected: {contradictions[0][:100]}")
        else:
            return (CriterionScore.FAIL, f"{len(contradictions)} contradictions detected")
    
    return (CriterionScore.PASS, "No logical contradictions detected")


def validate_completeness(
    output: str,
    task_context: Optional[str] = None
) -> Tuple[CriterionScore, str]:
    """
    Validate completeness of output.
    
    Checks that output addresses required information and considerations.
    
    Args:
        output: AI output to validate
        task_context: Optional task context to check against
        
    Returns:
        Tuple of (score, notes)
    """
    # Check for common required elements
    required_elements = {
        'explanation': r'\b(because|since|due to|reason|rationale)\b',
        'steps': r'\b(step|first|second|then|next|finally)\b',
        'considerations': r'\b(consider|note|important|constraint)\b'
    }
    
    present_elements = []
    missing_elements = []
    
    for element, pattern in required_elements.items():
        if re.search(pattern, output, re.IGNORECASE):
            present_elements.append(element)
        else:
            missing_elements.append(element)
    
    completeness_pct = len(present_elements) / len(required_elements)
    
    if completeness_pct >= 0.8:
        return (CriterionScore.PASS, f"All key elements present: {', '.join(present_elements)}")
    elif completeness_pct >= 0.5:
        return (CriterionScore.PARTIAL, f"Missing: {', '.join(missing_elements)}")
    else:
        return (CriterionScore.FAIL, f"Incomplete output, missing: {', '.join(missing_elements)}")


def validate_context_alignment(
    output: str,
    steering_content: Dict[str, str]
) -> Tuple[CriterionScore, str]:
    """
    Validate alignment with steering file context.
    
    Checks that output respects constraints and preferences from steering files.
    
    Args:
        output: AI output to validate
        steering_content: Content from active steering files
        
    Returns:
        Tuple of (score, notes)
    """
    # Extract constraints from steering files
    constraints = []
    for file_path, content in steering_content.items():
        # Look for constraint sections
        constraint_section = re.search(
            r'##\s*Constraints.*?(?=##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        if constraint_section:
            constraints.append(constraint_section.group(0))
    
    if not constraints:
        return (CriterionScore.PASS, "No explicit constraints to validate against")
    
    # Check for constraint violations (simplified heuristic)
    # Full implementation would parse specific constraints and validate against them
    constraint_keywords = []
    for constraint_text in constraints:
        # Extract key constraint terms
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', constraint_text)
        constraint_keywords.extend(words)
    
    if not constraint_keywords:
        return (CriterionScore.PASS, "Constraints present but no specific validation needed")
    
    # Check if output acknowledges constraints
    acknowledged = sum(1 for keyword in constraint_keywords if keyword.lower() in output.lower())
    acknowledgment_rate = acknowledged / len(constraint_keywords) if constraint_keywords else 1.0
    
    if acknowledgment_rate >= 0.3:
        return (CriterionScore.PASS, f"Output aligns with steering file context ({acknowledged} constraint references)")
    elif acknowledgment_rate >= 0.1:
        return (CriterionScore.PARTIAL, f"Limited constraint acknowledgment ({acknowledged}/{len(constraint_keywords)})")
    else:
        return (CriterionScore.FAIL, f"Output does not acknowledge steering file constraints")


def apply_domain_specific_criteria(
    output: str,
    steering_content: Dict[str, str]
) -> Dict[str, Tuple[CriterionScore, str]]:
    """
    Apply domain-specific review criteria based on active frameworks.
    
    Args:
        output: AI output to validate
        steering_content: Content from active steering files
        
    Returns:
        Dict mapping criterion names to (score, notes) tuples
    """
    domain_results = {}
    
    # Check for automotive domain
    if any('automotive' in path.lower() for path in steering_content.keys()):
        # Check for error code lookup
        has_error_code = bool(re.search(r'\b(error code|OBD|P\d{4}|diagnostic)\b', output, re.IGNORECASE))
        if has_error_code:
            domain_results['Automotive Error Code Lookup'] = (CriterionScore.PASS, "Error code reference present")
        else:
            domain_results['Automotive Error Code Lookup'] = (CriterionScore.PARTIAL, "No error code reference")
    
    # Check for financial domain
    if any('financial' in path.lower() or 'budget' in path.lower() for path in steering_content.keys()):
        # Check for cost breakdown
        has_cost = bool(re.search(r'\$\d+|\d+\s*dollars?|cost|price|budget', output, re.IGNORECASE))
        if has_cost:
            domain_results['Financial Cost Breakdown'] = (CriterionScore.PASS, "Cost information present")
        else:
            domain_results['Financial Cost Breakdown'] = (CriterionScore.FAIL, "Missing cost breakdown")
    
    # Check for organizational/legal domain
    if any('bylaw' in path.lower() or 'legal' in path.lower() or 'organizational' in path.lower() for path in steering_content.keys()):
        # Check for citations
        has_citation = bool(re.search(r'(section|article|clause|paragraph)\s+\d+', output, re.IGNORECASE))
        if has_citation:
            domain_results['Legal Citation'] = (CriterionScore.PASS, "Citations present")
        else:
            domain_results['Legal Citation'] = (CriterionScore.FAIL, "Missing required citations")
    
    return domain_results


def perform_reasoning_review(
    output: str,
    workspace_root: Optional[Path] = None
) -> ReviewResult:
    """
    Perform complete reasoning review on AI output.
    
    Args:
        output: AI output to review
        workspace_root: Path to workspace root
        
    Returns:
        ReviewResult object with all criteria scores
    """
    if workspace_root is None:
        workspace_root = Path.cwd()
    
    # Load criteria and steering content
    criteria = load_review_criteria(workspace_root)
    steering_content = load_steering_content(workspace_root)
    
    # Create result object
    result = ReviewResult()
    
    # Apply base criteria
    result.factual_accuracy = validate_factual_accuracy(output, steering_content)
    result.logical_consistency = validate_logical_consistency(output)
    result.completeness = validate_completeness(output)
    result.context_alignment = validate_context_alignment(output, steering_content)
    
    # Apply domain-specific criteria
    result.domain_specific = apply_domain_specific_criteria(output, steering_content)
    
    return result


def log_review_result(
    result: ReviewResult,
    review_type: str,
    workspace_root: Path
) -> None:
    """
    Log reasoning review result to log file.
    
    Args:
        result: ReviewResult object
        review_type: Type of review (Standard/Domain-Specific)
        workspace_root: Path to workspace root
    """
    # Build criteria list
    criteria_applied = [
        "Factual Accuracy",
        "Logical Consistency",
        "Completeness",
        "Context Alignment"
    ]
    criteria_applied.extend(result.domain_specific.keys())
    
    # Build results section
    results_lines = [
        f"- Factual Accuracy: {result.factual_accuracy[0].value} - {result.factual_accuracy[1]}",
        f"- Logical Consistency: {result.logical_consistency[0].value} - {result.logical_consistency[1]}",
        f"- Completeness: {result.completeness[0].value} - {result.completeness[1]}",
        f"- Context Alignment: {result.context_alignment[0].value} - {result.context_alignment[1]}"
    ]
    
    for criterion_name, (score, notes) in result.domain_specific.items():
        results_lines.append(f"- {criterion_name}: {score.value} - {notes}")
    
    # Determine overall status and action
    overall_status = "Pass" if result.overall_pass() else "Fail"
    action = "Proceed" if result.overall_pass() else "Block"
    
    # Build failure reasons if applicable
    failure_reasons = ""
    if not result.overall_pass():
        reasons = result.get_failure_reasons()
        failure_reasons = "\n".join(f"  - {reason}" for reason in reasons)
    
    # Create log entry fields
    fields = {
        "Review Type": review_type,
        "Criteria Applied": ", ".join(criteria_applied),
        "Results": "\n" + "\n".join(results_lines),
        "Overall Status": overall_status,
        "Action": action
    }
    
    if failure_reasons:
        fields["Failure Reasons"] = "\n" + failure_reasons
    
    # Write log entry
    log_path = workspace_root / ".kiro" / "logs" / "reasoning-reviews.md"
    append_log_entry(log_path, "Reasoning Review", fields, workspace_root)


def reasoning_review_hook(
    output: str,
    workspace_root: Optional[Path] = None,
    block_on_failure: bool = True
) -> Tuple[bool, Optional[List[str]]]:
    """
    Main hook entry point for reasoning review.
    
    Args:
        output: AI output to review
        workspace_root: Path to workspace root
        block_on_failure: Whether to block execution on validation failure
        
    Returns:
        Tuple of (should_proceed, failure_reasons)
        - should_proceed: True if validation passed or blocking disabled
        - failure_reasons: List of failure reasons if validation failed, None otherwise
    """
    if workspace_root is None:
        workspace_root = Path.cwd()
    
    # Perform review
    result = perform_reasoning_review(output, workspace_root)
    
    # Determine review type
    review_type = "Domain-Specific" if result.domain_specific else "Standard"
    
    # Log result
    log_review_result(result, review_type, workspace_root)
    
    # Determine if execution should proceed
    if result.overall_pass():
        return (True, None)
    else:
        failure_reasons = result.get_failure_reasons()
        should_proceed = not block_on_failure
        return (should_proceed, failure_reasons)


if __name__ == "__main__":
    # Example usage for testing
    test_output = """
    Based on the automotive diagnostic procedures, the check engine light indicates
    error code P0420, which suggests a catalytic converter efficiency issue.
    
    Steps to diagnose:
    1. Verify error code with OBD-II scanner
    2. Check oxygen sensor readings
    3. Inspect catalytic converter
    
    Consider that this may require professional inspection if readings are abnormal.
    The repair cost will likely range from $200-$2000 depending on the issue.
    """
    
    should_proceed, failures = reasoning_review_hook(test_output)
    
    if should_proceed:
        print("✓ Reasoning review passed")
    else:
        print("✗ Reasoning review failed:")
        for reason in failures:
            print(f"  - {reason}")
