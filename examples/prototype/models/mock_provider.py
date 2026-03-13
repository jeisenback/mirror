import hashlib

class MockModelProvider:
    def classify_lead(self, lead):
        # deterministic classification: simple rule + hash fallback
        revenue = None
        try:
            revenue = float(lead.get('revenue', 0))
        except Exception:
            revenue = 0
        if revenue >= 100000:
            return {'label': 'qualified', 'confidence': 0.95}
        # fallback: hash-based pseudo-random but deterministic
        s = (lead.get('name', '') + str(lead.get('email', ''))).encode('utf-8')
        h = int(hashlib.sha256(s).hexdigest(), 16)
        if h % 10 > 6:
            return {'label': 'qualified', 'confidence': 0.7}
        return {'label': 'not_qualified', 'confidence': 0.6}

    def estimate_work(self, feature):
        # deterministic estimate based on title hash
        s = (feature.get('title', '') + feature.get('summary', '')).encode('utf-8')
        h = int(hashlib.sha256(s).hexdigest(), 16)
        estimate = (h % 8) + 1  # story points 1-8
        confidence = 0.6 + (estimate / 16.0)
        return {'estimate': estimate, 'confidence': confidence}
