# obs-request-correlation

> Open one request span at the HTTP edge and propagate a non-sensitive correlation ID through all downstream work

## Why It Matters

Concurrent requests interleave events from handlers, database calls, and
outbound clients. An operator needs one breadcrumb from a user report to find
the complete operation without searching on email addresses, tokens, or other
personal data. Create or accept a validated correlation ID at the ingress,
record it on the root request span, and propagate that context.

## Bad

```rust
#[tracing::instrument]
async fn subscribe(email: &str) {
    tracing::info!("starting request for {email}");
}
```

This logs personal data, and a handler that opens its own request span may
invent a second ID underneath the ingress span.

## Good

```text
HTTP ingress middleware:
  validated = accept incoming ID only when length and charset policy pass
  effective = validated or high_entropy_id_generator.mint()
  open the one root `http.request` span with effective ID
  run the production router inside that span
  return the effective ID in the response

handler and dependency adapters:
  open child spans only; inherit request ID from the root context
  forward standard trace context or the validated effective ID
```

A pure validation helper and adversarial cases live in
`checks/tests/source_guidance.rs`. ID generation uses a maintained random/UUID
implementation, not a timestamp or counter.

## Contract

- Ingress middleware creates exactly one root request span before routing.
- Accept a caller-provided ID only after length and character validation;
  otherwise replace it before recording, returning, or forwarding anything.
- Mint replacements with a high-entropy generator.
- Return the effective ID in the response and forward it to trusted downstream
  services using the platform's trace context or correlation header.
- Child spans inherit the field; handlers neither open another root request
  span nor overwrite its ID.
- Record route templates, not raw paths containing identifiers.
- Emit outcome and latency at the request edge.
- Log an error once at the handling boundary with its source chain; inner
  layers add context and return it.

## See Also

- [obs-instrument-spans](obs-instrument-spans.md) - attach async work to spans safely
- [obs-structured-fields](obs-structured-fields.md) - keep stable fields out of message strings
- [obs-no-sensitive-data](obs-no-sensitive-data.md) - never use secrets or unrestricted PII as correlation keys
- [obs-error-chain](obs-error-chain.md) - preserve causes for the handling edge
- [test-http-blackbox](test-http-blackbox.md) - verify ID propagation at the HTTP boundary
