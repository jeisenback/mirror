def run(task, model_provider, belief_store, repo):
    feature = task.get('input', {})
    step = {
        'step_id': task.get('id') + ':story',
        'task_id': task.get('id'),
        'action': 'generate_story'
    }
    title = feature.get('title') or (feature.get('summary') or 'Untitled feature')
    # simple deterministic estimation rule
    complexity = feature.get('complexity')
    if complexity is None:
        # fallback to model provider mock: use hash-based estimate
        est = model_provider.estimate_work(feature)
    else:
        est = {'estimate': complexity, 'confidence': 0.9}
    # build a simple user story and acceptance criteria
    story = {
        'title': f"As a user, {title}",
        'acceptance_criteria': feature.get('acceptance_criteria') or ["Given..., When..., Then..."],
        'estimate': est.get('estimate'),
        'confidence': est.get('confidence')
    }
    belief_store.record_step({
        'step_id': step['step_id'],
        'task_id': step['task_id'],
        'story': story
    })
    # append to repo (mock issue tracker)
    repo.append({'feature': feature, 'story': story})
    return {'status': 'ok', 'story': story}
