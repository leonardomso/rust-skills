# proj-stateless-process

> Keep durable application state outside individual service processes

## Why It Matters

Replicas are disposable: they restart, move hosts, and scale independently.
State written only to a local filesystem or in-memory registry disappears with
one instance and is invisible to the others. Persist durable domain state in a
shared service with an explicit consistency contract; keep process-local state
limited to caches and bounded work that can be reconstructed.

## Contract

- Do not use the local filesystem as the source of truth for replicated
  application data.
- Externalize durable state to a database, object store, or log appropriate to
  its access and consistency needs.
- Treat local caches as disposable: bound them, invalidate or version them, and
  recover from a cold start.
- Store uploads and generated artifacts durably before returning a success
  that promises persistence.
- Sessions, idempotency records, queue tasks, and leader state require shared
  storage or a platform primitive.
- Startup does not depend on a previous process's local files.
- Tests run multiple replicas or restart the process to prove state survives
  and remains coherent.

## See Also

- [proj-schema-migrations](proj-schema-migrations.md) - evolve shared database state
- [api-session-security](api-session-security.md) - keep authoritative sessions server-side and shared
- [api-idempotency-key](api-idempotency-key.md) - retry records survive process loss
- [async-durable-worker](async-durable-worker.md) - in-memory spawned work is not durable
- [proj-continuous-delivery](proj-continuous-delivery.md) - replace replicas without state loss
