"""
Hallucination Detection Hook

This hook validates factual claims in AI outputs against active steering files
and framework references. It flags unsupported claims and requires user confirmation
before proceeding with execution.

Requirements: 15.1, 15.2, 15.3, 15.4, 15.6
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum

from log_utils import append_log_entry, get_active_steering_files


class ClaimValidation(Enum):
    """Validation status for factual claims."""
    SUPPORTED = "Supported"
    UNSUPPORTED = "Unsupported"
    INFERENCE = "Inference"
    CITATION_REQUIRED = "Citation Required"


class FactualClaim:
    """Container for a factual claim and its validation status."""
    
    def __init__(self, claim_text: str, claim_type: str):
        self.claim_text = claim_text
        self.claim_type = claim_type  # 'factual', 'procedural', 'numerical', 'reference'
        self.validation_status = ClaimValidation.UNSUPPORTED
        self.supporting_evidence: List[str] = []
        self.confidence_score = 0.0
    
    def __repr__(self):
        return f"FactualClaim('{self.claim_text[:50]}...', {self.validation_status.value})"


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


def extract_factual_claims(output: str) -> List[FactualClaim]:
    """
    Extract factual claims from AI output.
    
    Identifies statements that make factual assertions, procedural claims,
    numerical claims, or reference claims.
    
    Args:
        output: AI output to analyze
        
    Returns:
        List of FactualClaim objects
    """
    claims = []
    
    # Split into sentences
    sentences = re.split(r'[.!?]\s+', output)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or len(sentence) < 10:
            continue
        
        # Skip questions and commands
        if sentence.endswith('?') or sentence.startswith(('Please', 'Try', 'Consider', 'Note')):
            continue
        
        # Check for inference markers (these are explicitly marked, so not hallucinations)
        inference_markers = [
            'assume', 'suppose', 'likely', 'probably', 'may', 'might', 
            'could', 'possibly', 'perhaps', 'seems', 'appears'
        ]
        has_inference_marker = any(marker in sentence.lower() for marker in inference_markers)
        
        if has_inference_marker:
            claim = FactualClaim(sentence, 'inference')
            claim.validation_status = ClaimValidation.INFERENCE
            claims.append(claim)
            continue
        
        # Identify claim types
        
        # Numerical claims (specific numbers, percentages, measurements)
        if re.search(r'\b\d+\s*(?:percent|%|dollars?|\$|years?|months?|days?|hours?|minutes?|kg|lbs?|meters?|feet)\b', sentence, re.IGNORECASE):
            claims.append(FactualClaim(sentence, 'numerical'))
            continue
        
        # Procedural claims (steps, instructions, requirements)
        if re.search(r'\b(must|should|shall|requires?|needs?|step|procedure|process)\b', sentence, re.IGNORECASE):
            claims.append(FactualClaim(sentence, 'procedural'))
            continue
        
        # Reference claims (mentions specific documents, sections, codes)
        if re.search(r'\b(section|article|clause|paragraph|code|standard|regulation|bylaw)\s+\d+', sentence, re.IGNORECASE):
            claims.append(FactualClaim(sentence, 'reference'))
            continue
        
        # Factual assertions (definitive statements)
        if re.search(r'\b(is|are|was|were|will be|has|have|had|does|do|did)\b', sentence, re.IGNORECASE):
            # Exclude common non-factual patterns
            if not re.search(r'\b(if|when|where|how|why|what|which)\b', sentence, re.IGNORECASE):
                claims.append(FactualClaim(sentence, 'factual'))
    
    return claims


def validate_claim_against_content(
    claim: FactualClaim,
    steering_content: Dict[str, str]
) -> None:
    """
    Validate a factual claim against steering file content.
    
    Updates the claim's validation_status, supporting_evidence, and confidence_score.
    
    Args:
        claim: FactualClaim to validate
        steering_content: Content from active steering files
    """
    # Extract key terms from claim (nouns, verbs, numbers)
    claim_lower = claim.claim_text.lower()
    
    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were'}
    claim_words = set(re.findall(r'\b\w+\b', claim_lower)) - stop_words
    
    # Extract numbers and specific terms
    claim_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', claim.claim_text))
    claim_specific_terms = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', claim.claim_text))
    
    best_match_score = 0.0
    best_match_source = None
    
    for file_path, content in steering_content.items():
        content_lower = content.lower()
        content_words = set(re.findall(r'\b\w+\b', content_lower)) - stop_words
        
        # Calculate word overlap
        word_overlap = len(claim_words & content_words)
        word_overlap_ratio = word_overlap / len(claim_words) if claim_words else 0
        
        # Check for number matches
        content_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', content))
        number_matches = len(claim_numbers & content_numbers)
        number_match_ratio = number_matches / len(claim_numbers) if claim_numbers else 0
        
        # Check for specific term matches
        term_matches = sum(1 for term in claim_specific_terms if term in content)
        term_match_ratio = term_matches / len(claim_specific_terms) if claim_specific_terms else 0
        
        # Calculate overall match score
        match_score = (
            word_overlap_ratio * 0.4 +
            number_match_ratio * 0.3 +
            term_match_ratio * 0.3
        )
        
        if match_score > best_match_score:
            best_match_score = match_score
            best_match_source = file_path
    
    # Update claim validation status based on match score
    claim.confidence_score = best_match_score
    
    if best_match_score >= 0.5:  # Strong match
        claim.validation_status = ClaimValidation.SUPPORTED
        if best_match_source:
            claim.supporting_evidence.append(best_match_source)
    elif best_match_score >= 0.3:  # Moderate match
        claim.validation_status = ClaimValidation.SUPPORTED
        if best_match_source:
            claim.supporting_evidence.append(f"{best_match_source} (partial match)")
    else:  # Weak or no match
        claim.validation_status = ClaimValidation.UNSUPPORTED


def check_citation_requirements(
    claims: List[FactualClaim],
    output: str,
    is_critical_context: bool
) -> None:
    """
    Check if claims in critical contexts have required citations.
    
    For data decisions and financial decisions, factual claims require
    explicit citations to steering file sections.
    
    Args:
        claims: List of FactualClaim objects
        output: Full AI output
        is_critical_context: Whether this is a data or financial decision context
    """
    if not is_critical_context:
        return
    
    # Find all citations in output
    citation_patterns = [
        r'\[\[([^\]]+)\]\]',  # Steering file references
        r'\[([^\]]+)\]\(([^)]+)\)',  # Markdown links
        r'(?:see|refer to|according to|from)\s+([A-Z][^.!?]+)',  # Explicit references
        r'section\s+(\d+)',  # Section references
    ]
    
    citations = []
    for pattern in citation_patterns:
        citations.extend(re.findall(pattern, output, re.IGNORECASE))
    
    # Flatten citations (some patterns return tuples)
    citations = [c if isinstance(c, str) else c[0] for c in citations]
    
    # Check each claim for nearby citations
    for claim in claims:
        if claim.validation_status == ClaimValidation.INFERENCE:
            continue  # Inferences don't need citations
        
        # Find claim position in output
        claim_pos = output.find(claim.claim_text)
        if claim_pos == -1:
            continue
        
        # Check for citations within 200 characters before or after claim
        nearby_text = output[max(0, claim_pos-200):min(len(output), claim_pos+len(claim.claim_text)+200)]
        
        has_nearby_citation = any(citation in nearby_text for citation in citations)
        
        if not has_nearby_citation and claim.validation_status == ClaimValidation.SUPPORTED:
            # Claim is supported but lacks explicit citation in critical context
            claim.validation_status = ClaimValidation.CITATION_REQUIRED


def detect_hallucinations(
    output: str,
    workspace_root: Optional[Path] = None,
    is_critical_context: bool = False
) -> Tuple[List[FactualClaim], List[FactualClaim]]:
    """
    Detect potential hallucinations in AI output.
    
    Args:
        output: AI output to analyze
        workspace_root: Path to workspace root
        is_critical_context: Whether this is a data or financial decision context
        
    Returns:
        Tuple of (all_claims, flagged_claims)
        - all_claims: All factual claims found
        - flagged_claims: Claims that are unsupported or need citations
    """
    if workspace_root is None:
        workspace_root = Path.cwd()
    
    # Load steering content
    steering_content = load_steering_content(workspace_root)
    
    # Extract claims
    claims = extract_factual_claims(output)
    
    # Validate each claim
    for claim in claims:
        if claim.validation_status != ClaimValidation.INFERENCE:
            validate_claim_against_content(claim, steering_content)
    
    # Check citation requirements for critical contexts
    check_citation_requirements(claims, output, is_critical_context)
    
    # Identify flagged claims
    flagged_claims = [
        claim for claim in claims
        if claim.validation_status in [ClaimValidation.UNSUPPORTED, ClaimValidation.CITATION_REQUIRED]
    ]
    
    return claims, flagged_claims


def log_hallucination_flags(
    flagged_claims: List[FactualClaim],
    user_action: str,
    workspace_root: Path
) -> None:
    """
    Log flagged claims to hallucination log file.
    
    Args:
        flagged_claims: List of flagged FactualClaim objects
        user_action: User's action (Confirmed/Rejected/Updated Steering)
        workspace_root: Path to workspace root
    """
    for claim in flagged_claims:
        # Create log entry fields
        fields = {
            "Claim": claim.claim_text,
            "Claim Type": claim.claim_type.capitalize(),
            "Validation Result": claim.validation_status.value,
            "Confidence Score": f"{claim.confidence_score:.2f}",
            "Supporting Evidence": ", ".join(claim.supporting_evidence) if claim.supporting_evidence else "None found",
            "User Action": user_action
        }
        
        # Write log entry
        log_path = workspace_root / ".kiro" / "logs" / "hallucination-flags.md"
        append_log_entry(log_path, "Hallucination Flag", fields, workspace_root)


def format_flagged_claims_message(flagged_claims: List[FactualClaim]) -> str:
    """
    Format flagged claims into a user-friendly message.
    
    Args:
        flagged_claims: List of flagged FactualClaim objects
        
    Returns:
        Formatted message string
    """
    if not flagged_claims:
        return ""
    
    lines = [
        "⚠️  Potential hallucination detected - unsupported factual claims found:",
        ""
    ]
    
    for i, claim in enumerate(flagged_claims, 1):
        lines.append(f"{i}. {claim.claim_text}")
        lines.append(f"   Status: {claim.validation_status.value}")
        
        if claim.validation_status == ClaimValidation.UNSUPPORTED:
            lines.append(f"   Issue: No supporting evidence found in active steering files")
        elif claim.validation_status == ClaimValidation.CITATION_REQUIRED:
            lines.append(f"   Issue: Citation required for critical decision context")
        
        if claim.supporting_evidence:
            lines.append(f"   Evidence: {', '.join(claim.supporting_evidence)}")
        
        lines.append("")
    
    lines.extend([
        "Please review these claims and:",
        "- Confirm if they are correct (will proceed with execution)",
        "- Reject if they are incorrect (will block execution)",
        "- Update steering files with correct information if needed",
        ""
    ])
    
    return "\n".join(lines)


def hallucination_detection_hook(
    output: str,
    workspace_root: Optional[Path] = None,
    is_critical_context: bool = False,
    require_user_confirmation: bool = True
) -> Tuple[bool, Optional[str], List[FactualClaim]]:
    """
    Main hook entry point for hallucination detection.
    
    Args:
        output: AI output to analyze
        workspace_root: Path to workspace root
        is_critical_context: Whether this is a data or financial decision context
        require_user_confirmation: Whether to require user confirmation for flagged claims
        
    Returns:
        Tuple of (should_proceed, message, flagged_claims)
        - should_proceed: True if no flags or user confirmed, False if user rejected
        - message: Message to present to user (None if no flags)
        - flagged_claims: List of flagged claims for logging
    """
    if workspace_root is None:
        workspace_root = Path.cwd()
    
    # Detect hallucinations
    all_claims, flagged_claims = detect_hallucinations(output, workspace_root, is_critical_context)
    
    if not flagged_claims:
        # No hallucinations detected, proceed
        return (True, None, [])
    
    # Format message for user
    message = format_flagged_claims_message(flagged_claims)
    
    if not require_user_confirmation:
        # Log but don't block
        log_hallucination_flags(flagged_claims, "Auto-Confirmed (non-blocking mode)", workspace_root)
        return (True, message, flagged_claims)
    
    # In a real implementation, this would prompt the user for confirmation
    # For now, we return the message and let the calling code handle user interaction
    return (False, message, flagged_claims)


def handle_user_response(
    user_action: str,
    flagged_claims: List[FactualClaim],
    workspace_root: Path
) -> bool:
    """
    Handle user's response to flagged claims.
    
    Args:
        user_action: User's action (Confirmed/Rejected/Updated)
        flagged_claims: List of flagged claims
        workspace_root: Path to workspace root
        
    Returns:
        True if execution should proceed, False if blocked
    """
    # Log the user's action
    log_hallucination_flags(flagged_claims, user_action, workspace_root)
    
    # Determine if execution should proceed
    if user_action.lower() in ['confirmed', 'updated', 'updated steering']:
        return True
    elif user_action.lower() == 'rejected':
        return False
    else:
        # Unknown action, default to blocking for safety
        return False


if __name__ == "__main__":
    # Example usage for testing
    test_output = """
    The catalytic converter efficiency is below 95% threshold according to OBD-II standards.
    This requires immediate replacement which will cost approximately $1,200.
    
    The repair procedure is documented in section 7.3 of the service manual.
    You should schedule the repair within the next week to avoid further damage.
    
    Based on the symptoms, I assume the oxygen sensors are functioning correctly.
    """
    
    should_proceed, message, flagged = hallucination_detection_hook(
        test_output,
        is_critical_context=True
    )
    
    if message:
        print(message)
        print(f"\nShould proceed: {should_proceed}")
        print(f"Flagged claims: {len(flagged)}")
    else:
        print("✓ No hallucinations detected")
