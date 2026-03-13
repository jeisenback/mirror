import os
import sys

# ensure package imports resolve when running from repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from runtime import get_bus
from executor.worker import TaskExecutor
from models.mock_provider import MockModelProvider
from adapters.product.adapter import receive_feature
from belief_store.store import BeliefStore
import skills.story_generation as story_skill


def run_scenario():
    bus = get_bus()
    belief_store = BeliefStore()
    repo = []
    model = MockModelProvider()
    skills_registry = {
        'story_generation': story_skill.run
    }
    executor = TaskExecutor(bus, skills_registry, model, belief_store, repo)

    # send two feature payloads
    receive_feature({'title': 'Improve search', 'summary': 'Better relevancy', 'complexity': 3}, bus)
    receive_feature({'title': 'Add onboarding flow', 'summary': 'New user flow'}, bus)

    executor.process_all()

    # assertions
    assert len(repo) == 2, f"Expected 2 repo entries, got {len(repo)}"
    stories = [r['story'] for r in repo]
    assert all('title' in s for s in stories), f"Expected title in all stories, got {stories}"

    # print summary
    print('Repo entries:')
    for e in repo:
        print('-', e['feature'].get('title'), '=>', e['story']['title'], f"(est={e['story']['estimate']}, conf={e['story']['confidence']})")
    print('\nBelief store:')
    for b in belief_store.all():
        print('-', b)
    # persist trace for docs/meta analysis
    try:
        import time, json, os
        out_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'traces')
        os.makedirs(out_dir, exist_ok=True)
        fname = os.path.join(out_dir, f"run_product_trace_{int(time.time())}.json")
        with open(fname, 'w', encoding='utf-8') as f:
            json.dump(belief_store.all(), f, indent=2)
        print('\nWrote trace to', fname)
    except Exception:
        pass


if __name__ == '__main__':
    try:
        run_scenario()
        print('\nPRODUCT TESTS PASSED')
    except AssertionError as e:
        print('\nPRODUCT TESTS FAILED:', e)
        raise
