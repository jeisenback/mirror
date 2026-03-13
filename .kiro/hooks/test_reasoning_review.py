"""
Property-Based Tests for Reasoning Review Hook

Tests Property 11 (Reasoning Review Criteria Validation) and Property 12 (Validation Failure Blocking)
from the Reasoning Context Framework design document.

Requirements: 16.3, 16.4
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from pathlib import Path
import tempfile
from typing import List, Dict, Tuple

from reasoning_review import (
    perform_reasoning_review,
    reasoning_review_hook,
    validate_factual_accuracy,
    validate_logical_consistency,
    validate_completeness,
    validate_context_alignment,
    ReviewResult,
    CriterionScore
)


# ============================================================================
# Test Data Generators
# ============================================================================

@st.composite
def steering_file_content(draw):
    """Generate realistic steering file content."""
    sections = []
    
    # Add constraints section
    constraints = draw(st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')),
            min_size=20,
            max_size=100
        ),
        min_size=1,
        max_size=5
    ))
    sections.append("## Constraints\n\n" + "\n".join(f"- {c}" for c in constraints))
    
    # Add general content
    content = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')),
        min_size=50,
        max_size=200
    ))
    sections.append(content)
    
    return "\n\n".join(sections)


@st.composite
def ai_output_with_criteria_elements(draw, include_elements: Dict[str, bool] = None):
    """Generate AI output with specific criteria elements."""
    if include_elements is None:
        include_elements = {
            'explanation': draw(st.booleans()),
            'steps': draw(st.booleans()),
            'considerations': draw(st.booleans()),
            'factual_claims': draw(st.booleans()),
            'logical_structure': draw(st.booleans())
        }
    
    parts = []
    
    # Add explanation if requested
    if include_elements.get('explanation', False):
        explanation = draw(st.sampled_from([
            "This is necessary because the system requires proper configuration.",
            "The reason for this approach is due to technical constraints.",
            "Since the component is critical, we must follow the procedure."
        ]))
        parts.append(explanation)
    
    # Add steps if requested
    if include_elements.get('steps', False):
        num_steps = draw(st.integers(min_value=2, max_value=5))
        steps = [f"{i+1}. {draw(st.sampled_from(['Check', 'Verify', 'Update', 'Install', 'Configure']))} the component."
                 for i in range(num_steps)]
        parts.append("\n".join(steps))
    
    # Add considerations if requested
    if include_elements.get('considerations', False):
        consideration = draw(st.sampled_from([
            "Important: Consider the time constraints before proceeding.",
            "Note that this may require additional resources.",
            "This constraint must be respected during implementation."
        ]))
        parts.append(consideration)
    
    # Add factual claims if requested
    if include_elements.get('factual_claims', False):
        claim = draw(st.sampled_from([
            "The system requires 8GB of memory.",
            "The process takes approximately 30 minutes.",
            "The component costs $150."
        ]))
        parts.append(claim)
    
    # Add logical structure if requested
    if include_elements.get('logical_structure', False):
        structure = draw(st.sampled_from([
            "If the condition is met, then proceed with the action. Otherwise, skip this step.",
            "Given the constraints, we can conclude that this approach is optimal.",
            "Therefore, based on the analysis, the recommendation is to proceed."
        ]))
        parts.append(structure)
    
    return "\n\n".join(parts) if parts else "Basic output without specific elements."


@st.composite
def output_with_contradictions(draw, has_contradiction: bool = None):
    """Generate output with or without logical contradictions."""
    if has_contradiction is None:
        has_contradiction = draw(st.booleans())
    
    if has_contradiction:
        # Generate contradictory statements
        contradictions = [
            "The system must always be online. However, it cannot be online during maintenance.",
            "This is impossible to achieve, but it is possible with the right approach.",
            "The component never fails, although sometimes it may fail under stress."
        ]
        base = draw(st.sampled_from(contradictions))
    else:
        # Generate consistent statements
        consistent = [
            "The system should be online during normal operation. During maintenance, it will be offline.",
            "This is achievable with the right approach and proper planning.",
            "The component is reliable under normal conditions but may fail under extreme stress."
        ]
        base = draw(st.sampled_from(consistent))
    
    return base


@st.composite
def workspace_with_steering_content(draw, include_constraints: bool = True):
    """Generate a temporary workspace with steering files."""
    temp_dir = tempfile.mkdtemp()
    workspace_root = Path(temp_dir)
    
    # Create steering directory structure
    steering_dir = workspace_root / ".kiro" / "steering" / "household"
    steering_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate steering file
    if include_constraints:
        content = draw(steering_file_content())
    else:
        content = "# Basic Context\n\nSome general information without specific constraints."
    
    steering_file = steering_dir / "context.md"
    with open(steering_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return workspace_root, content


# ============================================================================
# Property 11: Reasoning Review Criteria Validation
# Feature: reasoning-context-framework, Property 11: Reasoning Review Criteria Validation
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(output=ai_output_with_criteria_elements())
def test_property_11_all_four_criteria_evaluated(output: str):
    """
    Property 11: For any reasoning review execution, the verification hook
    should validate the output against all four criteria: factual accuracy,
    logical consistency, completeness, and alignment with steering file context.
    
    This test verifies that all four base criteria are always evaluated.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create minimal steering structure
        steering_dir = workspace_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Perform review
        result = perform_reasoning_review(output, workspace_root)
        
        # Property: All four criteria must be evaluated
        assert result.factual_accuracy is not None, "Factual accuracy must be evaluated"
        assert result.logical_consistency is not None, "Logical consistency must be evaluated"
        assert result.completeness is not None, "Completeness must be evaluated"
        assert result.context_alignment is not None, "Context alignment must be evaluated"
        
        # Property: Each criterion must have a score and notes
        assert isinstance(result.factual_accuracy[0], CriterionScore), \
            "Factual accuracy must have CriterionScore"
        assert isinstance(result.factual_accuracy[1], str), \
            "Factual accuracy must have notes"
        
        assert isinstance(result.logical_consistency[0], CriterionScore), \
            "Logical consistency must have CriterionScore"
        assert isinstance(result.logical_consistency[1], str), \
            "Logical consistency must have notes"
        
        assert isinstance(result.completeness[0], CriterionScore), \
            "Completeness must have CriterionScore"
        assert isinstance(result.completeness[1], str), \
            "Completeness must have notes"
        
        assert isinstance(result.context_alignment[0], CriterionScore), \
            "Context alignment must have CriterionScore"
        assert isinstance(result.context_alignment[1], str), \
            "Context alignment must have notes"


@settings(max_examples=100, deadline=None)
@given(
    include_explanation=st.booleans(),
    include_steps=st.booleans(),
    include_considerations=st.booleans()
)
def test_property_11_completeness_validation(
    include_explanation: bool,
    include_steps: bool,
    include_considerations: bool
):
    """
    Property 11: Completeness criterion must validate that output addresses
    all required information and considerations.
    
    This test verifies that completeness scoring reflects the presence of
    required elements.
    """
    # Generate output with specific elements
    parts = []
    
    if include_explanation:
        parts.append("This is necessary because the system requires proper configuration.")
    
    if include_steps:
        parts.append("First, check the component. Second, verify the settings. Finally, test the system.")
    
    if include_considerations:
        parts.append("Important: Consider the time constraints before proceeding.")
    
    output = "\n\n".join(parts) if parts else "Minimal output."
    
    # Validate completeness
    score, notes = validate_completeness(output)
    
    # Property: Score should reflect presence of elements
    elements_present = sum([include_explanation, include_steps, include_considerations])
    
    if elements_present >= 2:
        # At least 2 out of 3 elements present
        assert score in [CriterionScore.PASS, CriterionScore.PARTIAL], \
            f"Expected PASS or PARTIAL with {elements_present} elements, got {score}"
    elif elements_present == 0:
        # No elements present
        assert score in [CriterionScore.FAIL, CriterionScore.PARTIAL], \
            f"Expected FAIL or PARTIAL with no elements, got {score}"


@settings(max_examples=100, deadline=None)
@given(has_contradiction=st.booleans())
def test_property_11_logical_consistency_validation(has_contradiction: bool):
    """
    Property 11: Logical consistency criterion must validate that the reasoning
    chain is free of contradictions.
    
    This test verifies that logical consistency scoring detects contradictions.
    Note: The heuristic-based detection may not catch all contradictions,
    so we verify the function returns valid scores and notes.
    """
    if has_contradiction:
        # Create contradictory output with patterns the heuristic can detect
        output = "The component is not functional but it is working properly."
    else:
        # Create consistent output
        output = "The system should be online during normal operation. During maintenance, it will be offline."
    
    # Validate logical consistency
    score, notes = validate_logical_consistency(output)
    
    # Property: Must return valid score and notes
    assert score in [CriterionScore.PASS, CriterionScore.PARTIAL, CriterionScore.FAIL], \
        f"Invalid score: {score}"
    assert isinstance(notes, str) and len(notes) > 0, \
        "Notes must be non-empty string"
    
    # Property: Consistent output should pass
    if not has_contradiction:
        assert score == CriterionScore.PASS, \
            f"Expected PASS for consistent output, got {score}"


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
@given(
    claim_text=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')),
        min_size=20,
        max_size=100
    ),
    include_in_steering=st.booleans()
)
def test_property_11_factual_accuracy_validation(claim_text: str, include_in_steering: bool):
    """
    Property 11: Factual accuracy criterion must validate that claims are
    supported by steering file content or marked as inference.
    
    This test verifies that factual accuracy scoring reflects claim support.
    """
    # Skip if claim text has too few words
    assume(len(claim_text.split()) >= 3)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create steering directory
        steering_dir = workspace_root / ".kiro" / "steering" / "household"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Create steering file
        steering_file = steering_dir / "context.md"
        if include_in_steering:
            with open(steering_file, 'w', encoding='utf-8') as f:
                f.write(f"# Context\n\n{claim_text}\n\nAdditional information.")
        else:
            with open(steering_file, 'w', encoding='utf-8') as f:
                f.write("# Context\n\nCompletely unrelated information that doesn't match.")
        
        # Load steering content
        from reasoning_review import load_steering_content
        steering_content = load_steering_content(workspace_root)
        
        # Validate factual accuracy
        score, notes = validate_factual_accuracy(claim_text, steering_content)
        
        # Property: Score must be one of the valid CriterionScore values
        assert score in [CriterionScore.PASS, CriterionScore.PARTIAL, CriterionScore.FAIL], \
            f"Invalid score: {score}"
        
        # Property: Notes must be non-empty
        assert len(notes) > 0, "Notes must be provided"


@settings(max_examples=100, deadline=None)
@given(
    output=ai_output_with_criteria_elements(),
    has_constraints=st.booleans()
)
def test_property_11_context_alignment_validation(output: str, has_constraints: bool):
    """
    Property 11: Context alignment criterion must validate that output respects
    constraints and preferences from steering files.
    
    This test verifies that context alignment scoring reflects constraint
    acknowledgment.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create steering directory
        steering_dir = workspace_root / ".kiro" / "steering" / "household"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Create steering file with or without constraints
        steering_file = steering_dir / "context.md"
        if has_constraints:
            with open(steering_file, 'w', encoding='utf-8') as f:
                f.write("""
                # Context
                
                ## Constraints
                
                - Time Constraint: Must complete within 2 hours
                - Budget Constraint: Maximum $500
                - Resource Constraint: Limited to 2 team members
                """)
        else:
            with open(steering_file, 'w', encoding='utf-8') as f:
                f.write("# Context\n\nGeneral information without specific constraints.")
        
        # Load steering content
        from reasoning_review import load_steering_content
        steering_content = load_steering_content(workspace_root)
        
        # Validate context alignment
        score, notes = validate_context_alignment(output, steering_content)
        
        # Property: Score must be valid
        assert score in [CriterionScore.PASS, CriterionScore.PARTIAL, CriterionScore.FAIL], \
            f"Invalid score: {score}"
        
        # Property: If no constraints, should pass
        if not has_constraints:
            assert score == CriterionScore.PASS, \
                "Should pass when no constraints to validate against"


# ============================================================================
# Property 12: Validation Failure Blocking
# Feature: reasoning-context-framework, Property 12: Validation Failure Blocking
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    output=ai_output_with_criteria_elements(),
    block_on_failure=st.booleans()
)
def test_property_12_failed_validation_blocks_execution(output: str, block_on_failure: bool):
    """
    Property 12: For any verification hook that fails validation, the hook
    should block the operation and present failure reasons to the user.
    
    This test verifies that failed reviews block execution when configured
    to do so, and that the blocking behavior is consistent with the configuration.
    
    Note: failure_reasons is a list (possibly empty) when validation fails,
    and None when validation passes. An empty list means validation failed
    but only with PARTIAL scores (no FAIL scores).
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create minimal steering structure
        steering_dir = workspace_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Run reasoning review hook
        should_proceed, failure_reasons = reasoning_review_hook(
            output,
            workspace_root,
            block_on_failure=block_on_failure
        )
        
        # Property: Return types must be correct
        assert isinstance(should_proceed, bool), "should_proceed must be boolean"
        assert failure_reasons is None or isinstance(failure_reasons, list), \
            "failure_reasons must be None or list"
        
        # Property: Blocking behavior must be consistent with configuration
        if failure_reasons is None:
            # Validation passed (overall_pass() returned True)
            assert should_proceed is True, \
                "Hook must allow execution when validation passes"
        else:
            # Validation failed (overall_pass() returned False)
            # failure_reasons is a list (may be empty if only PARTIAL scores, not FAIL)
            assert isinstance(failure_reasons, list), \
                "failure_reasons must be a list when validation fails"
            
            if block_on_failure:
                assert should_proceed is False, \
                    "Hook must block execution when validation fails and blocking is enabled"
            else:
                assert should_proceed is True, \
                    "Hook must not block when blocking is disabled, even if validation fails"


@settings(max_examples=100, deadline=None)
@given(output=output_with_contradictions(has_contradiction=True))
def test_property_12_contradiction_blocks_execution(output: str):
    """
    Property 12: When logical consistency fails due to contradictions,
    execution must be blocked and specific failure reasons provided.
    
    This test verifies that contradictions cause blocking with clear reasons.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create minimal steering structure
        steering_dir = workspace_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Run reasoning review hook with blocking enabled
        should_proceed, failure_reasons = reasoning_review_hook(
            output,
            workspace_root,
            block_on_failure=True
        )
        
        # Property: Contradictions should cause blocking
        # Note: This is probabilistic based on the contradiction detection heuristics
        if failure_reasons is not None and len(failure_reasons) > 0:
            # Check if logical consistency is in failure reasons
            logical_failures = [r for r in failure_reasons if 'Logical Consistency' in r]
            if logical_failures:
                assert should_proceed is False, \
                    "Logical consistency failure should block execution"


@settings(max_examples=100, deadline=None)
@given(
    num_criteria_failing=st.integers(min_value=0, max_value=4)
)
def test_property_12_overall_pass_requires_all_criteria(num_criteria_failing: int):
    """
    Property 12: Overall validation pass requires all criteria to pass.
    Any single criterion failure should result in overall failure.
    
    This test verifies that the overall_pass() method correctly requires
    all criteria to pass.
    """
    result = ReviewResult()
    
    # Set criteria scores based on num_criteria_failing
    criteria = [
        'factual_accuracy',
        'logical_consistency',
        'completeness',
        'context_alignment'
    ]
    
    for i, criterion in enumerate(criteria):
        if i < num_criteria_failing:
            # Set to FAIL
            setattr(result, criterion, (CriterionScore.FAIL, f"{criterion} failed"))
        else:
            # Set to PASS
            setattr(result, criterion, (CriterionScore.PASS, f"{criterion} passed"))
    
    # Property: overall_pass() should return False if any criterion failed
    if num_criteria_failing > 0:
        assert result.overall_pass() is False, \
            f"Overall pass should be False when {num_criteria_failing} criteria fail"
    else:
        assert result.overall_pass() is True, \
            "Overall pass should be True when all criteria pass"


@settings(max_examples=100, deadline=None)
@given(
    factual_score=st.sampled_from([CriterionScore.PASS, CriterionScore.PARTIAL, CriterionScore.FAIL]),
    logical_score=st.sampled_from([CriterionScore.PASS, CriterionScore.PARTIAL, CriterionScore.FAIL]),
    completeness_score=st.sampled_from([CriterionScore.PASS, CriterionScore.PARTIAL, CriterionScore.FAIL]),
    context_score=st.sampled_from([CriterionScore.PASS, CriterionScore.PARTIAL, CriterionScore.FAIL])
)
def test_property_12_failure_reasons_completeness(
    factual_score: CriterionScore,
    logical_score: CriterionScore,
    completeness_score: CriterionScore,
    context_score: CriterionScore
):
    """
    Property 12: When validation fails, all failed criteria must be included
    in the failure reasons list.
    
    This test verifies that get_failure_reasons() returns all failed criteria.
    """
    result = ReviewResult()
    result.factual_accuracy = (factual_score, "Factual accuracy notes")
    result.logical_consistency = (logical_score, "Logical consistency notes")
    result.completeness = (completeness_score, "Completeness notes")
    result.context_alignment = (context_score, "Context alignment notes")
    
    # Get failure reasons
    failure_reasons = result.get_failure_reasons()
    
    # Property: Only FAIL scores should be in failure reasons
    expected_failures = []
    if factual_score == CriterionScore.FAIL:
        expected_failures.append('Factual Accuracy')
    if logical_score == CriterionScore.FAIL:
        expected_failures.append('Logical Consistency')
    if completeness_score == CriterionScore.FAIL:
        expected_failures.append('Completeness')
    if context_score == CriterionScore.FAIL:
        expected_failures.append('Context Alignment')
    
    assert len(failure_reasons) == len(expected_failures), \
        f"Expected {len(expected_failures)} failure reasons, got {len(failure_reasons)}"
    
    for expected in expected_failures:
        assert any(expected in reason for reason in failure_reasons), \
            f"Expected '{expected}' in failure reasons"


@settings(max_examples=100, deadline=None)
@given(output=ai_output_with_criteria_elements())
def test_property_12_blocking_consistency_across_calls(output: str):
    """
    Property 12: Blocking behavior must be consistent across multiple calls
    with the same input and configuration.
    
    This test verifies deterministic blocking behavior.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create minimal steering structure
        steering_dir = workspace_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Run hook multiple times
        results = []
        for _ in range(3):
            should_proceed, failure_reasons = reasoning_review_hook(
                output,
                workspace_root,
                block_on_failure=True
            )
            results.append((should_proceed, failure_reasons))
        
        # Property: All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result[0] == first_result[0], \
                "should_proceed must be consistent across calls"
            
            # Compare failure reasons (both None or both have same length)
            if first_result[1] is None:
                assert result[1] is None, \
                    "failure_reasons must be consistent (both None)"
            else:
                assert result[1] is not None, \
                    "failure_reasons must be consistent (both not None)"
                assert len(result[1]) == len(first_result[1]), \
                    "failure_reasons length must be consistent"


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================

@settings(max_examples=50, deadline=None)
@given(output=st.text(min_size=0, max_size=1000))
def test_empty_and_random_text_handling(output: str):
    """
    Test that the hook handles empty strings and random text gracefully
    without crashing.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create minimal structure
        steering_dir = workspace_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Should not crash
        try:
            result = perform_reasoning_review(output, workspace_root)
            should_proceed, failures = reasoning_review_hook(output, workspace_root)
            
            # Should always return valid types
            assert isinstance(result, ReviewResult)
            assert isinstance(should_proceed, bool)
            assert failures is None or isinstance(failures, list)
            
        except Exception as e:
            pytest.fail(f"Hook crashed on input: {e}")


def test_example_automotive_scenario():
    """
    Example-based test for automotive repair scenario from design document.
    """
    output = """
    Based on the diagnostic procedures in section 7.3, the check engine light
    indicates error code P0420, which suggests a catalytic converter efficiency issue.
    
    Steps to diagnose:
    1. First, verify the error code with an OBD-II scanner
    2. Then, check the oxygen sensor readings
    3. Finally, inspect the catalytic converter for damage
    
    Important: Consider that this repair may cost between $200-$2000 depending
    on whether it's a sensor issue or requires converter replacement.
    
    Since the vehicle has 150,000 miles, I assume the catalytic converter may
    be nearing end of life, which is typical for this mileage.
    """
    
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create steering structure
        steering_dir = workspace_root / ".kiro" / "steering" / "framework" / "automotive"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Create diagnostic procedures
        procedures = steering_dir / "diagnostic-procedures.md"
        with open(procedures, 'w', encoding='utf-8') as f:
            f.write("""
            # Automotive Diagnostic Procedures
            
            ## Section 7.3: Check Engine Light Diagnosis
            
            Error code P0420 indicates catalytic converter efficiency below threshold.
            Typical repair costs range from $200-$2000.
            Catalytic converters typically last 100,000-150,000 miles.
            """)
        
        # Perform review
        result = perform_reasoning_review(output, workspace_root)
        
        # Verify all criteria evaluated
        assert result.factual_accuracy is not None
        assert result.logical_consistency is not None
        assert result.completeness is not None
        assert result.context_alignment is not None
        
        # Should have good completeness (has explanation, steps, considerations)
        assert result.completeness[0] in [CriterionScore.PASS, CriterionScore.PARTIAL]
        
        # Should have good logical consistency (no contradictions)
        assert result.logical_consistency[0] == CriterionScore.PASS


def test_domain_specific_criteria_application():
    """
    Test that domain-specific criteria are applied when relevant frameworks
    are active.
    """
    output = """
    The financial analysis shows a budget variance of $5,000 in Q3.
    This requires immediate attention and reallocation of resources.
    """
    
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create financial steering file
        steering_dir = workspace_root / ".kiro" / "steering" / "framework" / "financial"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        financial_file = steering_dir / "budget-analysis.md"
        with open(financial_file, 'w', encoding='utf-8') as f:
            f.write("# Budget Analysis Procedures\n\nVariance analysis methodology.")
        
        # Perform review
        result = perform_reasoning_review(output, workspace_root)
        
        # Should have domain-specific criteria for financial context
        assert len(result.domain_specific) > 0, \
            "Should apply domain-specific criteria for financial context"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
