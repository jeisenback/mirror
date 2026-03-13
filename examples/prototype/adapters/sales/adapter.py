import uuid

def receive_webhook(payload, bus):
    envelope = {
        'id': str(uuid.uuid4()),
        'type': 'lead_qualification',
        'input': payload,
    }
    bus.publish(envelope)
    return envelope['id']
