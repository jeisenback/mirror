"""
Property-Based Tests for Hallucination Detection Hook

Tests Property 10 (Factual Claim Validation) and Property 12 (Validation Failure Blocking)
from the Reasoning Context Framework design document.

Requirements: 15.2, 15.3
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, example
from pathlib import Path
import tempfile
import shutil
from typing import List, Dict

from hallucination_detection import (
    detect_hallucinations,
    hallucination_detection_hook,
    extract_factual_claims,
    validate_claim_against_content,
    FactualClaim,
    ClaimValidation,
    handle_user_response
)


# ============================================================================
# Test Data Generators
# ============================================================================

@st.composite
def steering_file_content(draw):
    """Generate realistic steering file content."""
    sections = draw(st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')),
            min_size=20,
            max_size=200
        ),
        min_size=1,
        max_size=5
    ))
    return "\n\n".join(sections)


@st.composite
def factual_claim_text(draw, claim_type: str = 'factual'):
    """Generate factual claim text based on type."""
    if claim_type == 'numerical':
        number = draw(st.integers(min_value=1, max_value=10000))
        unit = draw(st.sampled_from(['percent', 'dollars', 'years', 'months', 'kg', 'meters']))
        template = draw(st.sampled_from([
            f"The value is {number} {unit}.",
            f"This costs {number} {unit}.",
            f"The measurement is {number} {unit}."
        ]))
        return template
    
    elif claim_type == 'procedural':
        action = draw(st.sampled_from(['must', 'should', 'requires', 'needs']))
        verb = draw(st.sampled_from(['replace', 'check', 'verify', 'update', 'install']))
        object_name = draw(st.sampled_from(['component', 'system', 'module', 'part']))
        return f"The system {action} {verb} the {object_name}."
    
    elif claim_type == 'reference':
        section_num = draw(st.integers(min_value=1, max_value=20))
        doc_type = draw(st.sampled_from(['section', 'article', 'clause', 'paragraph']))
        return f"According to {doc_type} {section_num}, this is required."
    
    elif claim_type == 'inference':
        marker = draw(st.sampled_from(['assume', 'likely', 'probably', 'may', 'might', 'possibly']))
        statement = draw(st.sampled_from([
            'the component is functioning',
            'this will resolve the issue',
            'the system is operational'
        ]))
        return f"I {marker} that {statement}."
    
    else:  # factual
        subject = draw(st.sampled_from(['The system', 'The component', 'The module', 'The device']))
        verb = draw(st.sampled_from(['is', 'has', 'does', 'will']))
        predicate = draw(st.sampled_from([
            'functioning correctly',
            'operational status',
            'proper configuration',
            'expected behavior'
        ]))
        return f"{subject} {verb} {predicate}."


@st.composite
def ai_output_with_claims(draw, num_claims: int = None, claim_types: List[str] = None):
    """Generate AI output containing various types of claims."""
    if num_claims is None:
        num_claims = draw(st.integers(min_value=1, max_value=10))
    
    if claim_types is None:
        claim_types = ['factual', 'numerical', 'procedural', 'reference', 'inference']
    
    claims = []
    for _ in range(num_claims):
        claim_type = draw(st.sampled_from(claim_types))
        claim = draw(factual_claim_text(claim_type=claim_type))
        claims.append(claim)
    
    # Join claims with some connecting text
    output_parts = []
    for i, claim in enumerate(claims):
        output_parts.append(claim)
        if i < len(claims) - 1:
            connector = draw(st.sampled_from([
                ' Additionally, ',
                ' Furthermore, ',
                ' Moreover, ',
                '\n\n'
            ]))
            output_parts.append(connector)
    
    return ''.join(output_parts)


@st.composite
def workspace_with_steering_files(draw):
    """Generate a temporary workspace with steering files."""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    workspace_root = Path(temp_dir)
    
    # Create steering directory structure
    steering_dir = workspace_root / ".kiro" / "steering"
    steering_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate steering files
    num_files = draw(st.integers(min_value=1, max_value=5))
    file_paths = []
    
    for i in range(num_files):
        subdir = draw(st.sampled_from(['household', 'roles', 'projects', 'tasks', 'framework']))
        file_dir = steering_dir / subdir
        file_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = file_dir / f"context_{i}.md"
        content = draw(steering_file_content())
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        file_paths.append(file_path.relative_to(workspace_root))
    
    return workspace_root, file_paths


# ============================================================================
# Property 10: Factual Claim Validation
# Feature: reasoning-context-framework, Property 10: Factual Claim Validation
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(output=ai_output_with_claims())
def test_property_10_all_claims_validated(output: str):
    """
    Property 10: For any factual claim in AI output, the verification hook
    should validate that the claim is either supported by content in active
    steering files or explicitly marked as inference/assumption.
    
    This test verifies that every claim extracted from output receives a
    validation status (SUPPORTED, UNSUPPORTED, or INFERENCE).
    """
    # Create temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create minimal steering structure
        steering_dir = workspace_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect hallucinations
        all_claims, flagged_claims = detect_hallucinations(output, workspace_root)
        
        # Property: Every claim must have a validation status
        for claim in all_claims:
            assert claim.validation_status in [
                ClaimValidation.SUPPORTED,
                ClaimValidation.UNSUPPORTED,
                ClaimValidation.INFERENCE,
                ClaimValidation.CITATION_REQUIRED
            ], f"Claim has invalid validation status: {claim.validation_status}"
        
        # Property: Claims marked as INFERENCE should contain inference markers
        for claim in all_claims:
            if claim.validation_status == ClaimValidation.INFERENCE:
                inference_markers = [
                    'assume', 'suppose', 'likely', 'probably', 'may', 'might',
                    'could', 'possibly', 'perhaps', 'seems', 'appears'
                ]
                assert any(marker in claim.claim_text.lower() for marker in inference_markers), \
                    f"Claim marked as INFERENCE but lacks inference marker: {claim.claim_text}"


@settings(max_examples=100, deadline=None)
@given(
    claim_text=factual_claim_text(claim_type='factual'),
    include_in_steering=st.booleans()
)
def test_property_10_supported_claims_have_evidence(claim_text: str, include_in_steering: bool):
    """
    Property 10: Claims validated as SUPPORTED must have supporting evidence
    from steering files.
    
    This test verifies that when a claim is marked as SUPPORTED, it has
    evidence from steering file content.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create steering directory
        steering_dir = workspace_root / ".kiro" / "steering" / "household"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Create steering file with or without claim content
        steering_file = steering_dir / "context.md"
        if include_in_steering:
            # Include the claim text in steering file
            with open(steering_file, 'w', encoding='utf-8') as f:
                f.write(f"# Household Context\n\n{claim_text}\n\nAdditional context here.")
        else:
            # Create steering file without claim content
            with open(steering_file, 'w', encoding='utf-8') as f:
                f.write("# Household Context\n\nUnrelated content that doesn't match the claim.")
        
        # Detect hallucinations
        all_claims, flagged_claims = detect_hallucinations(claim_text, workspace_root)
        
        # Property: If claim is SUPPORTED, it must have supporting evidence
        for claim in all_claims:
            if claim.validation_status == ClaimValidation.SUPPORTED:
                assert len(claim.supporting_evidence) > 0, \
                    f"Claim marked as SUPPORTED but has no supporting evidence: {claim.claim_text}"
                assert claim.confidence_score > 0.0, \
                    f"Claim marked as SUPPORTED but has zero confidence score: {claim.claim_text}"


@settings(max_examples=100, deadline=None)
@given(claim_type=st.sampled_from(['factual', 'numerical', 'procedural', 'reference', 'inference']))
def test_property_10_inference_claims_not_flagged(claim_type: str):
    """
    Property 10: Claims explicitly marked as inference/assumption should not
    be flagged as unsupported.
    
    This test verifies that claims with inference markers are correctly
    identified and not treated as hallucinations.
    """
    # Generate claim with inference marker if claim_type is 'inference'
    if claim_type == 'inference':
        claim_text = "I assume that the component is functioning correctly based on the symptoms."
    else:
        claim_text = "The component is functioning correctly."
    
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create minimal steering structure (empty)
        steering_dir = workspace_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect hallucinations
        all_claims, flagged_claims = detect_hallucinations(claim_text, workspace_root)
        
        # Property: Inference claims should not be in flagged_claims
        if claim_type == 'inference':
            inference_claims = [c for c in all_claims if c.validation_status == ClaimValidation.INFERENCE]
            assert len(inference_claims) > 0, "Inference marker not detected"
            
            for claim in inference_claims:
                assert claim not in flagged_claims, \
                    f"Inference claim incorrectly flagged: {claim.claim_text}"


# ============================================================================
# Property 12: Validation Failure Blocking
# Feature: reasoning-context-framework, Property 12: Validation Failure Blocking
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    output=ai_output_with_claims(),
    is_critical_context=st.booleans()
)
def test_property_12_unsupported_claims_block_execution(output: str, is_critical_context: bool):
    """
    Property 12: For any verification hook that fails validation (unsupported
    factual claims), the hook should block the operation and require user
    confirmation before proceeding.
    
    This test verifies that when unsupported claims are detected, the hook
    returns should_proceed=False and provides a message to the user.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create minimal steering structure (empty, so claims will be unsupported)
        steering_dir = workspace_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Run hallucination detection hook
        should_proceed, message, flagged_claims = hallucination_detection_hook(
            output,
            workspace_root,
            is_critical_context=is_critical_context,
            require_user_confirmation=True
        )
        
        # Property: If there are flagged claims, execution should be blocked
        if len(flagged_claims) > 0:
            assert should_proceed is False, \
                "Hook should block execution when unsupported claims are detected"
            assert message is not None, \
                "Hook should provide message when blocking execution"
            assert len(message) > 0, \
                "Message should not be empty when blocking execution"
        else:
            # No flagged claims, should proceed
            assert should_proceed is True, \
                "Hook should allow execution when no unsupported claims detected"


@settings(max_examples=100, deadline=None)
@given(
    user_action=st.sampled_from(['Confirmed', 'Rejected', 'Updated Steering', 'confirmed', 'rejected', 'updated'])
)
def test_property_12_user_rejection_blocks_execution(user_action: str):
    """
    Property 12: When user rejects flagged output, execution must be blocked.
    
    This test verifies that handle_user_response correctly blocks execution
    when the user rejects the flagged claims.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create logs directory
        logs_dir = workspace_root / ".kiro" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a flagged claim
        flagged_claim = FactualClaim("The system requires immediate replacement.", "factual")
        flagged_claim.validation_status = ClaimValidation.UNSUPPORTED
        
        # Handle user response
        should_proceed = handle_user_response(user_action, [flagged_claim], workspace_root)
        
        # Property: Rejected actions must block execution
        if user_action.lower() == 'rejected':
            assert should_proceed is False, \
                f"User action '{user_action}' should block execution"
        elif user_action.lower() in ['confirmed', 'updated', 'updated steering']:
            assert should_proceed is True, \
                f"User action '{user_action}' should allow execution"


@settings(max_examples=100, deadline=None)
@given(
    num_unsupported=st.integers(min_value=0, max_value=10),
    require_confirmation=st.booleans()
)
def test_property_12_blocking_behavior_consistency(num_unsupported: int, require_confirmation: bool):
    """
    Property 12: Blocking behavior must be consistent - if require_user_confirmation
    is True and there are unsupported claims, execution must be blocked.
    
    This test verifies the consistency of blocking behavior across different
    configurations.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create minimal steering structure
        steering_dir = workspace_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output with specific number of unsupported claims
        claims = []
        for i in range(num_unsupported):
            claims.append(f"The component {i} requires replacement immediately.")
        
        output = " ".join(claims) if claims else "No factual claims here."
        
        # Run hook
        should_proceed, message, flagged_claims = hallucination_detection_hook(
            output,
            workspace_root,
            is_critical_context=False,
            require_user_confirmation=require_confirmation
        )
        
        # Property: Blocking behavior must be consistent
        if require_confirmation and len(flagged_claims) > 0:
            assert should_proceed is False, \
                "Must block when require_confirmation=True and flagged claims exist"
        
        if not require_confirmation:
            assert should_proceed is True, \
                "Must not block when require_confirmation=False"
        
        if len(flagged_claims) == 0:
            assert should_proceed is True, \
                "Must not block when no flagged claims exist"


@settings(max_examples=100, deadline=None)
@given(
    output=ai_output_with_claims(claim_types=['numerical', 'procedural', 'reference']),
    is_critical_context=st.booleans()
)
def test_property_12_critical_context_citation_requirements(output: str, is_critical_context: bool):
    """
    Property 12: In critical contexts (data/financial decisions), claims
    without citations should be flagged and block execution.
    
    This test verifies that citation requirements are enforced in critical
    contexts.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create steering with matching content
        steering_dir = workspace_root / ".kiro" / "steering" / "household"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        steering_file = steering_dir / "context.md"
        with open(steering_file, 'w', encoding='utf-8') as f:
            # Include output content so claims are "supported"
            f.write(f"# Context\n\n{output}\n")
        
        # Run hook
        should_proceed, message, flagged_claims = hallucination_detection_hook(
            output,
            workspace_root,
            is_critical_context=is_critical_context,
            require_user_confirmation=True
        )
        
        # Property: In critical context, claims needing citations should be flagged
        if is_critical_context:
            citation_required_claims = [
                c for c in flagged_claims
                if c.validation_status == ClaimValidation.CITATION_REQUIRED
            ]
            
            # If there are claims that need citations, execution should be blocked
            if len(citation_required_claims) > 0:
                assert should_proceed is False, \
                    "Must block in critical context when citations are required"


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
            all_claims, flagged_claims = detect_hallucinations(output, workspace_root)
            should_proceed, message, flagged = hallucination_detection_hook(
                output, workspace_root, require_user_confirmation=False
            )
            
            # Should always return valid types
            assert isinstance(all_claims, list)
            assert isinstance(flagged_claims, list)
            assert isinstance(should_proceed, bool)
            assert message is None or isinstance(message, str)
            
        except Exception as e:
            pytest.fail(f"Hook crashed on input: {e}")


def test_example_automotive_scenario():
    """
    Example-based test for automotive repair scenario from design document.
    """
    output = """
    The catalytic converter efficiency is below 95% threshold according to OBD-II standards.
    This requires immediate replacement which will cost approximately $1,200.
    
    The repair procedure is documented in section 7.3 of the service manual.
    You should schedule the repair within the next week to avoid further damage.
    
    Based on the symptoms, I assume the oxygen sensors are functioning correctly.
    """
    
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        
        # Create steering structure
        steering_dir = workspace_root / ".kiro" / "steering" / "framework" / "automotive"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Create service manual with section 7.3
        manual = steering_dir / "service-manual.md"
        with open(manual, 'w', encoding='utf-8') as f:
            f.write("""
            # Service Manual
            
            ## Section 7.3: Catalytic Converter Replacement
            
            The catalytic converter efficiency threshold is 95% according to OBD-II standards.
            Replacement cost is approximately $1,200 for parts and labor.
            """)
        
        # Run detection
        all_claims, flagged_claims = detect_hallucinations(output, workspace_root, is_critical_context=True)
        
        # Verify inference claim is not flagged
        inference_claims = [c for c in all_claims if 'assume' in c.claim_text.lower()]
        assert len(inference_claims) > 0, "Should detect inference claim"
        assert all(c.validation_status == ClaimValidation.INFERENCE for c in inference_claims)
        
        # Verify supported claims
        supported_claims = [c for c in all_claims if c.validation_status == ClaimValidation.SUPPORTED]
        assert len(supported_claims) > 0, "Should have supported claims from steering file"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
