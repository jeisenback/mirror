import json
import sys

# simple emitter that outputs a sample node for docs pipeline
node = {
    'id': 'function::examples/prototype/skills/lead_qualification.py::run',
    'type': 'function',
    'display_name': 'lead_qualification.run',
    'path': 'examples/prototype/skills/lead_qualification.py',
}
print(json.dumps(node))
