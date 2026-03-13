import os
import sys

# ensure package imports resolve when running from repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from runtime import get_bus
from executor.worker import TaskExecutor
from models.mock_provider import MockModelProvider
from adapters.sales.adapter import receive_webhook
from belief_store.store import BeliefStore
import skills.lead_qualification as lead_skill


def run_scenario():
    bus = get_bus()
    belief_store = BeliefStore()
    crm = []
    model = MockModelProvider()
    skills_registry = {
        'lead_qualification': lead_skill.run
    }
    executor = TaskExecutor(bus, skills_registry, model, belief_store, crm)

    # send two webhooks
    receive_webhook({'name': 'Small Co', 'email': 'a@small.co', 'revenue': 50000}, bus)
    receive_webhook({'name': 'Big Co', 'email': 'b@big.co', 'revenue': 200000}, bus)

    executor.process_all()

    # assertions
    assert len(crm) == 2, f"Expected 2 CRM entries, got {len(crm)}"
    statuses = [c['status'] for c in crm]
    assert 'qualified' in statuses, f"Expected a qualified lead, got {statuses}"

    # print summary
    print('CRM entries:')
    for e in crm:
        print('-', e['lead']['name'], '=>', e['status'], f"(conf={e['confidence']})")
    print('\nBelief store:')
    for b in belief_store.all():
        print('-', b)
    # persist trace for docs/meta analysis
    try:
        import time, json, os
        out_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'traces')
        os.makedirs(out_dir, exist_ok=True)
        fname = os.path.join(out_dir, f"run_tests_trace_{int(time.time())}.json")
        with open(fname, 'w', encoding='utf-8') as f:
            json.dump(belief_store.all(), f, indent=2)
        print('\nWrote trace to', fname)
    except Exception:
        pass


if __name__ == '__main__':
    try:
        run_scenario()
        print('\nTESTS PASSED')
    except AssertionError as e:
        print('\nTESTS FAILED:', e)
        raise
