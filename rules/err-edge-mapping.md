# err-edge-mapping

> Keep domain and infrastructure errors protocol-neutral; map them to safe, actionable responses at the entrypoint

## Why It Matters

One failure serves different audiences. Application code may need a typed
distinction to decide control flow; operators need the full situation and
source chain; an HTTP or CLI caller needs only a stable machine signal and
information they can act on. Implementing a framework response trait on a
database or domain error couples inner layers to one entrypoint and risks
leaking internals.

## Bad

```rust
pub enum StoreError {
    Sql(String),
}

impl IntoHttpResponse for StoreError {
    fn into_response(self) -> HttpResponse {
        HttpResponse::internal_error(format!("database failed: {self:?}"))
    }
}
```

The storage type now knows HTTP and exposes diagnostics to an untrusted caller.

## Good

```rust
#[derive(Debug)]
pub enum SubscribeError {
    InvalidEmail,
    Unexpected(anyhow::Error),
}

pub struct EdgeResponse {
    pub status: u16,
    pub public_message: &'static str,
}

pub fn map_subscribe_error(error: &SubscribeError) -> EdgeResponse {
    match error {
        SubscribeError::InvalidEmail => EdgeResponse {
            status: 400,
            public_message: "email address is invalid",
        },
        SubscribeError::Unexpected(_) => EdgeResponse {
            status: 500,
            public_message: "request could not be completed",
        },
    }
}

fn main() {
    let response = map_subscribe_error(&SubscribeError::InvalidEmail);
    assert_eq!(response.status, 400);
}
```

The request edge records the unexpected error once with a short `Display`
field and a source-complete diagnostic field, then returns the generic response.

## Decision Matrix

| Purpose and location | Representation |
| --- | --- |
| Internal control flow | typed error with only distinctions the caller handles |
| Internal human diagnosis | contextual source chain in logs/traces |
| External machine control | status code, exit code, or protocol error code |
| External human correction | safe message naming the field and constraint |

Choose matchable versus opaque errors from caller intent, not merely whether
the crate is called a library or application.

## Contract

- Inner domain and infrastructure errors do not implement HTTP, CLI, or gRPC
  response traits.
- Caller-fixable failures preserve an actionable explanation at the edge.
- Unexpected responses omit SQL, paths, stack traces, dependency bodies, and
  secrets.
- Intermediate layers return errors with context; they do not manufacture a
  success-typed failure response and discard the cause.
- The handling edge logs once. Inner layers add context without duplicate
  error events.

## See Also

- [err-context-chain](err-context-chain.md) - add situation context while propagating
- [err-source-chain](err-source-chain.md) - retain the causal chain
- [obs-error-chain](obs-error-chain.md) - record operator diagnostics at the handling edge
- [obs-no-sensitive-data](obs-no-sensitive-data.md) - redact both response and telemetry
- [api-extract-or-reject](api-extract-or-reject.md) - make fixable input failures explicit
