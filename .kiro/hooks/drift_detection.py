"""
AI Drift Detection Hook

This hook detects deviations from baseline AI behavior patterns by comparing
current output characteristics against documented baseline patterns. It logs
significant deviations but does not block execution (non-blocking verification).

Requirements: 14.2, 14.3, 14.4
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

from log_utils import append_log_entry, get_active_steering_files


class DeviationType(Enum):
    """Types of deviations that can be detected."""
    RESPONSE_LENGTH = "Response Length"
    CODE_BLOCK_USAGE = "Code Block Usage"
    CITATION_FREQUENCY = "Citation Frequency"
    REASONING_PATTERN = "Reasoning Pattern"
    OUTPUT_FORMAT = "Output Format"
    TONE_STYLE = "Tone and Style"


class BaselinePatterns:
    """Container for baseline behavior patterns."""
    
    def __init__(self):
        # Response characteristics
        self.response_length_ranges = {
            'standard': (200, 500),
            'technical': (300, 800),
            'code_example': (10, 50),  # lines of code
            'simple': (20, 100)
        }
        
        # Code block expectations
        self.code_block_frequency = 0.80  # 80% of technical responses
        
        # Citation expectations
        self.min_citations_per_claim = 1
        
        # Reasoning patterns
        self.expected_patterns = [
            'step-by-step',
            'assumption_statement',
            'alternative_consideration'
        ]
        
        # Output format expectations
        self.format_conventions = {
            'file_paths': 'relative',
            'path_separator': '/',
            'command_completeness': True
        }
        
        # Deviation thresholds
        self.minor_threshold = 0.30  # 30% deviation
        self.significant_threshold = 0.50  # 50% deviation


def load_baseline_patterns(workspace_root: Path) -> BaselinePatterns:
    """
    Load baseline behavior patterns from framework steering files.
    
    Args:
        workspace_root: Path to workspace root
        
    Returns:
        BaselinePatterns object with loaded or default patterns
        
    Note:
        If baseline file is missing, returns default patterns and logs a warning.
        This allows drift detection to continue with reasonable defaults.
    """
    baseline_path = workspace_root / ".kiro" / "steering" / "framework" / "ai-behavior-baseline" / "baseline.md"
    
    patterns = BaselinePatterns()
    
    if not baseline_path.exists():
        # Log warning but continue with defaults
        print(f"WARNING: Baseline file not found at {baseline_path}")
        print("Using default baseline patterns. Create baseline.md to customize drift detection.")
        return patterns
    
    try:
        with open(baseline_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse response length ranges
        length_match = re.search(r'Standard Queries.*?(\d+)-(\d+)\s*words', content, re.IGNORECASE)
        if length_match:
            patterns.response_length_ranges['standard'] = (int(length_match.group(1)), int(length_match.group(2)))
        
        tech_match = re.search(r'Technical Explanations.*?(\d+)-(\d+)\s*words', content, re.IGNORECASE)
        if tech_match:
            patterns.response_length_ranges['technical'] = (int(tech_match.group(1)), int(tech_match.group(2)))
        
        # Parse code block frequency
        code_freq_match = re.search(r'(\d+)%\s*of technical responses', content, re.IGNORECASE)
        if code_freq_match:
            patterns.code_block_frequency = int(code_freq_match.group(1)) / 100.0
        
        # Parse citation frequency
        citation_match = re.search(r'at least\s+(\d+)\s+reference', content, re.IGNORECASE)
        if citation_match:
            patterns.min_citations_per_claim = int(citation_match.group(1))
        
    except Exception as e:
        # If parsing fails, use defaults and log warning
        print(f"WARNING: Failed to parse baseline file: {str(e)}")
        print("Using default baseline patterns.")
    
    return patterns


def classify_response_type(output: str) -> str:
    """
    Classify the response type based on content.
    
    Args:
        output: AI output to classify
        
    Returns:
        Response type: 'standard', 'technical', 'code_example', or 'simple'
    """
    word_count = len(output.split())
    has_code = bool(re.search(r'```', output))
    
    if word_count < 150:
        return 'simple'
    elif has_code:
        return 'code_example'
    elif any(term in output.lower() for term in ['function', 'class', 'method', 'algorithm', 'implementation']):
        return 'technical'
    else:
        return 'standard'


def check_response_length_deviation(
    output: str,
    patterns: BaselinePatterns
) -> Optional[Tuple[DeviationType, float, str]]:
    """
    Check for response length deviations from baseline.
    
    Args:
        output: AI output to check
        patterns: Baseline patterns
        
    Returns:
        Tuple of (deviation_type, deviation_score, description) if deviation detected, None otherwise
    """
    response_type = classify_response_type(output)
    expected_range = patterns.response_length_ranges.get(response_type, (200, 500))
    
    word_count = len(output.split())
    min_words, max_words = expected_range
    
    # Calculate deviation
    if word_count < min_words:
        deviation = (min_words - word_count) / min_words
        description = f"Response too short: {word_count} words (expected {min_words}-{max_words})"
    elif word_count > max_words:
        deviation = (word_count - max_words) / max_words
        description = f"Response too long: {word_count} words (expected {min_words}-{max_words})"
    else:
        return None  # Within expected range
    
    # Only report if deviation exceeds minor threshold
    if deviation >= patterns.minor_threshold:
        return (DeviationType.RESPONSE_LENGTH, deviation, description)
    
    return None


def check_code_block_usage_deviation(
    output: str,
    patterns: BaselinePatterns
) -> Optional[Tuple[DeviationType, float, str]]:
    """
    Check for code block usage deviations from baseline.
    
    Args:
        output: AI output to check
        patterns: Baseline patterns
        
    Returns:
        Tuple of (deviation_type, deviation_score, description) if deviation detected, None otherwise
    """
    response_type = classify_response_type(output)
    
    # Only check technical responses
    if response_type not in ['technical', 'code_example']:
        return None
    
    has_code_block = bool(re.search(r'```', output))
    expected_code_block = patterns.code_block_frequency >= 0.5
    
    if expected_code_block and not has_code_block:
        deviation = patterns.code_block_frequency
        description = f"Missing code block in technical response (expected in {patterns.code_block_frequency*100:.0f}% of cases)"
        return (DeviationType.CODE_BLOCK_USAGE, deviation, description)
    
    return None


def check_citation_frequency_deviation(
    output: str,
    patterns: BaselinePatterns
) -> Optional[Tuple[DeviationType, float, str]]:
    """
    Check for citation frequency deviations from baseline.
    
    Args:
        output: AI output to check
        patterns: Baseline patterns
        
    Returns:
        Tuple of (deviation_type, deviation_score, description) if deviation detected, None otherwise
    """
    # Count factual claims (simplified heuristic)
    claim_patterns = [
        r'\b(is|are|was|were|will be|has|have)\b',
        r'\b(must|should|shall|requires?)\b'
    ]
    
    claims = 0
    for pattern in claim_patterns:
        claims += len(re.findall(pattern, output, re.IGNORECASE))
    
    if claims == 0:
        return None  # No claims to cite
    
    # Count citations (references to files, sections, or explicit citations)
    citation_patterns = [
        r'\[\[.*?\]\]',  # Steering file references
        r'\[.*?\]\(.*?\)',  # Markdown links
        r'(?:see|refer to|according to|from)\s+[A-Z]',  # Explicit references
        r'section\s+\d+',  # Section references
    ]
    
    citations = 0
    for pattern in citation_patterns:
        citations += len(re.findall(pattern, output, re.IGNORECASE))
    
    citations_per_claim = citations / claims if claims > 0 else 0
    expected_rate = patterns.min_citations_per_claim
    
    if citations_per_claim < expected_rate * 0.5:  # Less than 50% of expected
        deviation = (expected_rate - citations_per_claim) / expected_rate
        description = f"Low citation frequency: {citations} citations for {claims} claims (expected ~{expected_rate} per claim)"
        
        if deviation >= patterns.minor_threshold:
            return (DeviationType.CITATION_FREQUENCY, deviation, description)
    
    return None


def check_reasoning_pattern_deviation(
    output: str,
    patterns: BaselinePatterns
) -> Optional[Tuple[DeviationType, float, str]]:
    """
    Check for reasoning pattern deviations from baseline.
    
    Args:
        output: AI output to check
        patterns: Baseline patterns
        
    Returns:
        Tuple of (deviation_type, deviation_score, description) if deviation detected, None otherwise
    """
    # Check for expected reasoning patterns
    pattern_checks = {
        'step-by-step': r'\b(step|first|second|then|next|finally|\d+\.)\b',
        'assumption_statement': r'\b(assum|suppose|given that|if we)\b',
        'alternative_consideration': r'\b(alternative|another option|could also|instead)\b'
    }
    
    present_patterns = []
    missing_patterns = []
    
    for pattern_name, regex in pattern_checks.items():
        if pattern_name in patterns.expected_patterns:
            if re.search(regex, output, re.IGNORECASE):
                present_patterns.append(pattern_name)
            else:
                missing_patterns.append(pattern_name)
    
    if not patterns.expected_patterns:
        return None
    
    present_rate = len(present_patterns) / len(patterns.expected_patterns)
    
    if present_rate < 0.5:  # Less than 50% of expected patterns
        deviation = 1.0 - present_rate
        description = f"Missing reasoning patterns: {', '.join(missing_patterns)}"
        
        if deviation >= patterns.minor_threshold:
            return (DeviationType.REASONING_PATTERN, deviation, description)
    
    return None


def check_output_format_deviation(
    output: str,
    patterns: BaselinePatterns
) -> Optional[Tuple[DeviationType, float, str]]:
    """
    Check for output format deviations from baseline.
    
    Args:
        output: AI output to check
        patterns: Baseline patterns
        
    Returns:
        Tuple of (deviation_type, deviation_score, description) if deviation detected, None otherwise
    """
    deviations = []
    
    # Check file path format
    file_paths = re.findall(r'[./\\][\w/\\.-]+\.\w+', output)
    if file_paths:
        absolute_paths = [p for p in file_paths if p.startswith('/') or re.match(r'[A-Z]:', p)]
        if absolute_paths and patterns.format_conventions.get('file_paths') == 'relative':
            deviations.append("Using absolute paths instead of relative paths")
        
        # Check path separator
        backslash_paths = [p for p in file_paths if '\\' in p]
        if backslash_paths and patterns.format_conventions.get('path_separator') == '/':
            deviations.append("Using backslashes in paths instead of forward slashes")
    
    # Check command completeness
    commands = re.findall(r'`([^`]+)`', output)
    if commands and patterns.format_conventions.get('command_completeness'):
        incomplete_commands = [c for c in commands if len(c.split()) == 1 and not c.startswith('-')]
        if len(incomplete_commands) > len(commands) * 0.3:  # More than 30% incomplete
            deviations.append("Commands missing required flags or arguments")
    
    if deviations:
        deviation_score = len(deviations) * 0.3  # Each deviation adds 30%
        description = "; ".join(deviations)
        return (DeviationType.OUTPUT_FORMAT, min(deviation_score, 1.0), description)
    
    return None


def detect_drift(
    output: str,
    workspace_root: Optional[Path] = None
) -> List[Tuple[DeviationType, float, str]]:
    """
    Detect all deviations from baseline behavior patterns.
    
    Args:
        output: AI output to analyze
        workspace_root: Path to workspace root
        
    Returns:
        List of (deviation_type, deviation_score, description) tuples
    """
    if workspace_root is None:
        workspace_root = Path.cwd()
    
    # Load baseline patterns
    patterns = load_baseline_patterns(workspace_root)
    
    # Run all deviation checks
    deviations = []
    
    checks = [
        check_response_length_deviation,
        check_code_block_usage_deviation,
        check_citation_frequency_deviation,
        check_reasoning_pattern_deviation,
        check_output_format_deviation
    ]
    
    for check_func in checks:
        result = check_func(output, patterns)
        if result:
            deviations.append(result)
    
    return deviations


def log_drift_detection(
    deviations: List[Tuple[DeviationType, float, str]],
    workspace_root: Path
) -> None:
    """
    Log detected deviations to drift log file.
    
    Args:
        deviations: List of detected deviations
        workspace_root: Path to workspace root
    """
    if not deviations:
        return  # Don't log if no deviations
    
    for deviation_type, deviation_score, description in deviations:
        # Determine severity
        if deviation_score >= 0.50:
            severity = "Significant"
        elif deviation_score >= 0.30:
            severity = "Moderate"
        else:
            severity = "Minor"
        
        # Create log entry fields
        fields = {
            "Deviation Type": deviation_type.value,
            "Severity": severity,
            "Deviation Score": f"{deviation_score:.2f}",
            "Expected Pattern": f"See baseline at .kiro/steering/framework/ai-behavior-baseline/baseline.md",
            "Observed Pattern": description
        }
        
        # Write log entry
        log_path = workspace_root / ".kiro" / "logs" / "ai-drift.md"
        append_log_entry(log_path, "AI Drift Detected", fields, workspace_root)


def drift_detection_hook(
    output: str,
    workspace_root: Optional[Path] = None
) -> List[Tuple[DeviationType, float, str]]:
    """
    Main hook entry point for AI drift detection.
    
    This is a non-blocking verification hook that logs deviations but
    does not prevent execution.
    
    Args:
        output: AI output to analyze
        workspace_root: Path to workspace root
        
    Returns:
        List of detected deviations (for informational purposes)
    """
    if workspace_root is None:
        workspace_root = Path.cwd()
    
    # Detect deviations
    deviations = detect_drift(output, workspace_root)
    
    # Log significant deviations
    significant_deviations = [
        (dtype, score, desc) for dtype, score, desc in deviations
        if score >= 0.30  # Only log moderate or significant deviations
    ]
    
    if significant_deviations:
        log_drift_detection(significant_deviations, workspace_root)
    
    return deviations


if __name__ == "__main__":
    # Example usage for testing
    test_output = """
    This is a very short response without much detail.
    """
    
    deviations = drift_detection_hook(test_output)
    
    if deviations:
        print(f"✓ Detected {len(deviations)} deviation(s):")
        for dtype, score, desc in deviations:
            print(f"  - {dtype.value} (score: {score:.2f}): {desc}")
    else:
        print("✓ No significant deviations detected")
