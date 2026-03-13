import uuid

def receive_feature(payload, bus):
    envelope = {
        'id': str(uuid.uuid4()),
        'type': 'story_generation',
        'input': payload,
    }
    bus.publish(envelope)
    return envelope['id']
