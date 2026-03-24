# Worker AI

Worker-plane entrypoint for bounded research orchestration tasks.

Phase 1 intentionally avoids vendor-coupled model execution. The worker currently handles queue-style memo export and quote-lock validation tasks so the task boundary exists before later AI orchestration is added behind adapters.
