"""Run the prototype meta-reasoner service (uvicorn).

Usage:
    python examples/prototype/meta/run_service.py
"""
import uvicorn

if __name__ == '__main__':
    uvicorn.run('examples.prototype.meta.service:app', host='127.0.0.1', port=8001, log_level='info')
