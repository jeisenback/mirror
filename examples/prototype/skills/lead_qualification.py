def run(task, model_provider, belief_store, crm):
    lead = task.get('input', {})
    step = {
        'step_id': task.get('id') + ':skill',
        'task_id': task.get('id'),
        'action': 'classify'
    }
    # simple deterministic rule first
    revenue = None
    try:
        revenue = float(lead.get('revenue', 0))
    except Exception:
        revenue = 0
    if revenue >= 100000:
        label = 'qualified'
        confidence = 0.95
    else:
        res = model_provider.classify_lead(lead)
        label = res['label']
        confidence = res['confidence']
    # record belief
    belief_store.record_step({
        'step_id': step['step_id'],
        'task_id': step['task_id'],
        'label': label,
        'confidence': confidence
    })
    # perform mock CRM action: append to crm list
    crm.append({'lead': lead, 'status': label, 'confidence': confidence})
    return {'status': 'ok', 'label': label}
