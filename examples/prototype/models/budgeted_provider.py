import hashlib
import time
import json

# optional precise tokenizer for accurate token accounting
try:
    import tiktoken
    _HAS_TIKTOKEN = True
    _ENC = tiktoken.get_encoding('cl100k_base')
except Exception:
    _HAS_TIKTOKEN = False
    _ENC = None

class BudgetedProvider:
    """Wraps an underlying model provider and enforces a simple token budget.

    This prototype implementation uses a naive token counter (whitespace split)
    so it has no external deps. In production replace the counter with
    `tiktoken` or another tokenizer for accurate counts.
    """

    def __init__(self, provider, per_call_budget=500, cache_path=None):
        self.provider = provider
        self.per_call_budget = per_call_budget
        self.cache = {}
        self.cache_path = cache_path
        if cache_path:
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except Exception:
                self.cache = {}

    def _prompt_hash(self, prompt):
        return hashlib.sha256(prompt.encode('utf-8')).hexdigest()

    def _count_tokens(self, prompt: str) -> int:
        # prefer precise token counting when available
        if _HAS_TIKTOKEN and _ENC is not None:
            try:
                return len(_ENC.encode(prompt))
            except Exception:
                pass
        # naive proxy: whitespace tokens
        return len(prompt.split())

    def _summarize(self, prompt: str, max_tokens: int) -> str:
        # naive summarizer: take the first N whitespace tokens; if tokenizer
        # is available, attempt to slice encoded tokens and decode back roughly
        toks = prompt.split()
        if _HAS_TIKTOKEN and _ENC is not None:
            try:
                enc = _ENC.encode(prompt)
                sliced = enc[:max_tokens]
                return _ENC.decode(sliced)
            except Exception:
                pass
        return ' '.join(toks[:max_tokens])

    def generate(self, prompt: str, max_tokens: int = None, metadata: dict = None):
        start = time.time()
        h = self._prompt_hash(prompt)
        if h in self.cache:
            cached = self.cache[h]
            cached['cached'] = True
            return cached

        tokens = self._count_tokens(prompt)
        budget = self.per_call_budget if max_tokens is None else min(self.per_call_budget, max_tokens)

        if tokens > budget:
            # over budget: create a truncated prompt and mark fallback
            truncated = self._summarize(prompt, budget//2)
            out = {
                'text': f"[TRUNCATED] {truncated}",
                'tokens_used': budget//2,
                'latency': 0.0,
                'fallback': True,
            }
        else:
            # delegate to underlying provider; support providers that return simple dicts
            if hasattr(self.provider, 'generate'):
                res = self.provider.generate(prompt, max_tokens=max_tokens or self.per_call_budget, metadata=metadata)
                out = {
                    'text': res.get('text') if isinstance(res, dict) else str(res),
                    'tokens_used': tokens,
                    'latency': time.time() - start,
                    'fallback': False,
                }
            else:
                # fallback for providers with custom methods
                out = {
                    'text': str(self.provider),
                    'tokens_used': tokens,
                    'latency': time.time() - start,
                    'fallback': False,
                }

        # cache result
        self.cache[h] = out
        if self.cache_path:
            try:
                with open(self.cache_path, 'w', encoding='utf-8') as f:
                    json.dump(self.cache, f)
            except Exception:
                pass

        return out

    def estimate_work(self, feature):
        # delegate to underlying provider if available
        if hasattr(self.provider, 'estimate_work'):
            return self.provider.estimate_work(feature)
        # naive default
        title = feature.get('title', '')
        return {'estimate': max(1, len(title.split()) // 10), 'confidence': 0.5}
