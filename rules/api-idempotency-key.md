# api-idempotency-key

> Scope idempotency keys to the caller, serialize concurrent duplicates, and replay the original outcome

## Why It Matters

Clients retry after timeouts without knowing whether the server committed the
operation. Processing the same state-changing request twice can double-charge,
double-send, or create duplicate records. A caller-generated idempotency key
states intent: the same caller and key identify one logical operation.

## Contract

- Require a non-empty, bounded, header-safe key for operations that need
  retry-safety.
- Scope uniqueness to the authenticated principal and operation, not globally.
- Store a canonical request fingerprint with the key. Reusing the key for a
  different request is a conflict, not a replay.
- Persist the operation state and response in the same transaction as the
  local business state whenever possible.
- The first request claims the key. Concurrent duplicates either wait within a
  bounded budget and replay, or receive a documented in-progress response.
- Completed duplicates return the semantically same status, headers, and body
  without executing side effects again.
- Persist only an allowlisted, size-bounded response representation. Do not
  replay hop-by-hop headers, `Date`, authentication challenges, or
  `Set-Cookie`; reconstruct dynamic transport headers at the current edge.
- Set an explicit retention period and cleanup mechanism. Expiry defines when
  retry guarantees end.
- Do not claim exactly-once delivery to an external system that does not share
  the transaction or its own idempotency contract.

## Bad

```rust
pub async fn charge(request: Charge) -> Result<Response, Error> {
    gateway.charge(request).await
}
```

## Good

```rust
pub enum Claim {
    New,
    InProgress,
    Completed(SavedResponse),
    Conflict,
}

pub struct SavedResponse {
    pub status: u16,
    pub body: Vec<u8>,
}

fn main() {
    let response = SavedResponse {
        status: 202,
        body: b"accepted".to_vec(),
    };
    assert_eq!(response.status, 202);
}
```

The persistence adapter atomically chooses the claim from
`(principal, operation, key, request_fingerprint)`.

## Failure Tests

- a sequential duplicate causes one side effect and replays the response;
- two simultaneous duplicates cause one side effect;
- the same key with a different fingerprint is rejected;
- different principals may use the same key without seeing each other's data;
- a crash after local commit but before response still allows replay;
- oversized response bodies and unsafe response headers are not persisted;
- cleanup removes only entries beyond the documented retention window.

## See Also

- [conc-db-transaction-boundary](conc-db-transaction-boundary.md) - claim and local state must commit atomically
- [api-extract-or-reject](api-extract-or-reject.md) - validate the key before effects
- [test-http-blackbox](test-http-blackbox.md) - prove response replay at the boundary
- [async-http-client-reuse](async-http-client-reuse.md) - retry only operations with a safety contract
- [err-edge-mapping](err-edge-mapping.md) - map in-progress and conflict outcomes explicitly
