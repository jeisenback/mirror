from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import time

app = FastAPI(title="Prototype Meta-Reasoner")


class TraceStep(BaseModel):
    step_id: str
    task_id: str
    label: str = None
    confidence: float = None
    data: Dict[str, Any] = {}


class Trace(BaseModel):
    run_id: str
    steps: List[TraceStep]


class AnalyzeResult(BaseModel):
    suggestions: List[Dict[str, Any]]
    summary: str


class SimulationRequest(BaseModel):
    run_id: str
    proposed_change: Dict[str, Any]


class SimulationResult(BaseModel):
    run_id: str
    delta_metrics: Dict[str, Any]
    simulated: bool


@app.post('/meta/analyze', response_model=AnalyzeResult)
def analyze(trace: Trace):
    """Analyze a trace and return ranked suggestions.

    Heuristic prototype: find steps with confidence < 0.7 and suggest retry, fallback, or spec update.
    """
    suggestions = []
    low_conf_steps = [s for s in trace.steps if (s.confidence is not None and s.confidence < 0.7)]
    for s in low_conf_steps:
        suggestions.append({
            'step_id': s.step_id,
            'task_id': s.task_id,
            'issue': 'low_confidence',
            'suggested_action': 'retry_with_more_context',
            'expected_benefit': 0.2,
        })

    summary = f"Analyzed run {trace.run_id}: {len(low_conf_steps)} low-confidence steps found."
    return {'suggestions': suggestions, 'summary': summary}


@app.post('/meta/simulate', response_model=SimulationResult)
def simulate(req: SimulationRequest):
    """Run a sandboxed counterfactual simulation.

    Prototype: returns estimated delta metrics based on rule-of-thumb heuristics.
    """
    # simple deterministic simulated delta
    delta = {'error_rate_delta': -0.1, 'latency_delta': 0.0}
    if req.proposed_change.get('action') == 'simplify_prompt':
        delta['error_rate_delta'] = -0.05
    if req.proposed_change.get('action') == 'add_retrieval':
        delta['error_rate_delta'] = -0.15
        delta['latency_delta'] = 0.05

    return {'run_id': req.run_id, 'delta_metrics': delta, 'simulated': True}


@app.post('/meta/propose-change')
def propose_change(payload: Dict[str, Any]):
    """Produce a draft spec/skill change artifact for review.

    Returns a packageable artifact reference (stub) that can be pushed to the Spec Registry.
    """
    artifact = {
        'artifact_id': str(uuid.uuid4()),
        'created_at': time.time(),
        'payload': payload,
        'status': 'draft',
    }
    return artifact
