# async-http-client-reuse

> Reuse one configured HTTP client per service and require deadlines on every outbound call

## Why It Matters

Constructing an HTTP client per request discards connection pools, DNS state,
TLS sessions, and policy. Calls without deadlines can occupy every worker or
connection forever when a dependency stalls. Build one client during service
initialization, hide it inside a cheap cloneable adapter, and set explicit
connect and request deadlines.

## Bad

```text
for each incoming request:
  construct a new HTTP client
  send without a deadline
```

The example creates a pool for one call and has no bounded completion time.

## Good

```rust
use std::sync::Arc;
use std::time::Duration;

#[derive(Clone)]
pub struct DeliveryClient {
    inner: Arc<Inner>,
}

struct Inner {
    endpoint: String,
    timeout: Duration,
}

impl DeliveryClient {
    pub fn new(endpoint: String, timeout: Duration) -> Result<Self, &'static str> {
        if timeout.is_zero() {
            return Err("timeout must be non-zero");
        }
        Ok(Self {
            inner: Arc::new(Inner { endpoint, timeout }),
        })
    }
}

fn main() {
    assert!(DeliveryClient::new(
        "https://example.com".to_owned(),
        Duration::from_secs(5),
    )
    .is_ok());
}
```

The concrete HTTP library belongs inside the adapter. Configure TLS, proxy,
redirect, connection, and total-request policy once; clone the service handle
into handlers.

## Failure Contract

- Connect, first-byte, and total operation time are bounded according to the
  product SLO.
- Non-success HTTP status is an error even when the transport completed.
- Response bodies have a size limit.
- Cancellation releases the response/connection cleanly.
- Retry only failures known to be transient and safe for the operation; apply
  an attempt budget, exponential backoff, jitter, `Retry-After` where trusted,
  and the caller's total deadline. A state-changing call needs its own
  idempotency contract before automatic retry.
- Tests use a local mock server to assert method, path, headers, body,
  non-success status, timeout, malformed response, and retry count.

## See Also

- [api-service-clone](api-service-clone.md) - expose the client as a cheap handle
- [async-cancel-safety](async-cancel-safety.md) - cancellation must not corrupt client state
- [async-spawn-blocking](async-spawn-blocking.md) - do not run blocking clients on the executor
- [err-context-chain](err-context-chain.md) - identify the dependency and operation that failed
- [obs-instrument-spans](obs-instrument-spans.md) - instrument each dependency boundary
